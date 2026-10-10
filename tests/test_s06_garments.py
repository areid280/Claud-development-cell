from __future__ import annotations

import copy
import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import trimesh
from PIL import Image

from avatar_forge.core.config import load_pipeline_config
from avatar_forge.core.stage import StageContext
from avatar_forge.stages import s06_garments


def _context(tmp_path: Path, mode: str = "mvp_fused") -> StageContext:
    config = copy.deepcopy(load_pipeline_config())
    config["stages"]["s06_garments"]["mode"] = mode

    body_dir = tmp_path / "s05_body_params"
    body_dir.mkdir(parents=True)
    (body_dir / "body_params.json").write_text(
        json.dumps({"measurements": {"height": 168}}), encoding="utf-8"
    )
    prepare_dir = tmp_path / "s02_prepare"
    prepare_dir.mkdir()
    Image.new("RGBA", (2, 2), (120, 90, 80, 255)).save(
        prepare_dir / "front_rgba.png"
    )

    return StageContext(
        name="s06_garments",
        job_dir=tmp_path,
        stage_dir=tmp_path / "s06_garments",
        config=config,
        manifest={},
        overrides={},
        logger=logging.getLogger(__name__),
    )


class _FakeModel:
    name = "fake"

    def __init__(self) -> None:
        self.seeds: list[int] = []

    def __enter__(self) -> _FakeModel:
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def predict(
        self,
        image: Image.Image,
        *,
        out_dir: Path,
        seed: int,
        output_name: str,
    ) -> Path:
        self.seeds.append(seed)
        path = out_dir / output_name
        trimesh.creation.box().export(path)
        return path


def _fake_blender(
    calls: list[list[str]], *, include_stats: bool = True
) -> Any:
    def run(
        script: Path,
        args: list[str],
        config: dict[str, Any],
        *,
        log_path: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        if script.name == "cleanup_mesh.py":
            shutil.copyfile(args[args.index("--in") + 1], args[args.index("--out") + 1])
            stdout = (
                'CLEANUP_STATS {"triangles_in": 12, "triangles": 12, '
                '"parts_removed": 0, "scale": 1.68, "color_attributes": []}\n'
                if include_stats
                else ""
            )
        else:
            out_dir = Path(args[args.index("--out-dir") + 1])
            (out_dir / "front.png").write_bytes(b"front")
            (out_dir / "back.png").write_bytes(b"back")
            stdout = ""
        return subprocess.CompletedProcess(
            args=[], returncode=0, stdout=stdout, stderr=""
        )

    return run


def test_separate_mode_is_skipped(tmp_path: Path) -> None:
    result = s06_garments.run(_context(tmp_path, mode="separate"))

    assert result.status == "skipped"


def test_unknown_mode_fails_with_exact_message(tmp_path: Path) -> None:
    result = s06_garments.run(_context(tmp_path, mode="banana"))

    assert result.status == "fail"
    assert result.messages == ["Unknown s06_garments mode 'banana'"]


def test_mvp_fused_runs_model_and_blender(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model = _FakeModel()
    calls: list[list[str]] = []
    monkeypatch.setattr(s06_garments, "load_selected", lambda _: model)
    monkeypatch.setattr(s06_garments, "run_blender", _fake_blender(calls))
    monkeypatch.setattr(s06_garments, "vram_peak_gb", lambda: 2.345)
    result = s06_garments.run(_context(tmp_path))

    assert result.status == "ok"
    assert result.outputs == [
        "s06_garments/fused/raw.glb",
        "s06_garments/fused/character_fused.glb",
        "s06_garments/fused/front.png",
        "s06_garments/fused/back.png",
    ]
    cleanup_args = calls[0]
    assert cleanup_args[cleanup_args.index("--height-m") + 1] == "1.6800"
    assert cleanup_args[cleanup_args.index("--max-tris") + 1] == "150000"
    assert model.seeds == [0]
    assert result.data["triangles"] == 12
    assert result.data["model"] == "fake"
    assert result.data["watertight"] is True


def test_cleanup_without_stats_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model = _FakeModel()
    calls: list[list[str]] = []
    monkeypatch.setattr(s06_garments, "load_selected", lambda _: model)
    monkeypatch.setattr(
        s06_garments, "run_blender", _fake_blender(calls, include_stats=False)
    )

    result = s06_garments.run(_context(tmp_path))

    assert result.status == "fail"
    assert result.messages == ["cleanup_mesh.py printed no CLEANUP_STATS line"]


@pytest.mark.blender
def test_mvp_fused_with_real_blender(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import numpy as np

    from avatar_forge.models.mesh_axes import Z_UP_TO_Y_UP

    class ColoredBoxModel(_FakeModel):
        def predict(
            self,
            image: Image.Image,
            *,
            out_dir: Path,
            seed: int,
            output_name: str,
        ) -> Path:
            self.seeds.append(seed)
            mesh = trimesh.creation.box(extents=(0.5, 0.25, 1.0))
            mesh.apply_transform(Z_UP_TO_Y_UP)
            colors = np.full((len(mesh.vertices), 4), 255, dtype=np.uint8)
            colors[mesh.vertices[:, 1] > 0, :3] = (200, 40, 40)
            colors[mesh.vertices[:, 1] <= 0, :3] = (40, 40, 200)
            mesh.visual = trimesh.visual.ColorVisuals(vertex_colors=colors)
            path = out_dir / output_name
            mesh.export(path)
            return path

    monkeypatch.setattr(s06_garments, "load_selected", lambda _: ColoredBoxModel())
    result = s06_garments.run(_context(tmp_path))

    assert result.status == "ok"
    output = tmp_path / "s06_garments/fused/character_fused.glb"
    mesh = trimesh.load(output, force="mesh")
    low, high = mesh.bounds
    assert high[1] - low[1] == pytest.approx(1.68, abs=1e-3)
    assert result.data["watertight"] is True
    assert (output.parent / "front.png").is_file()
    assert (output.parent / "back.png").is_file()
