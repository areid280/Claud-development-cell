from __future__ import annotations

import copy
import json
import logging
import subprocess
from pathlib import Path
from typing import Any

import pytest
import trimesh

from avatar_forge.core.config import load_pipeline_config
from avatar_forge.core.schemas import validate
from avatar_forge.core.stage import StageContext
from avatar_forge.stages import s09_export

JOB_ID = "20261010-000000-abcdef"
BODY_PARAMS = {
    "units": "cm",
    "source": "test",
    "measurements": {
        "height": 168,
        "bust": 90,
        "underbust": 75,
        "waist": 70,
        "hips": 95,
        "shoulder_width": 40,
        "inseam": 80,
    },
    "colors": {"skin": "#d0a080", "hair": "#302820", "eyes": "#507090"},
}


def _context(tmp_path: Path, mode: str = "mvp_fused") -> StageContext:
    config = copy.deepcopy(load_pipeline_config())
    config["stages"]["s06_garments"]["mode"] = mode

    body_dir = tmp_path / "s05_body_params"
    body_dir.mkdir()
    (body_dir / "body_params.json").write_text(
        json.dumps(BODY_PARAMS), encoding="utf-8"
    )
    fused_dir = tmp_path / "s06_garments" / "fused"
    fused_dir.mkdir(parents=True)
    (fused_dir / "character_fused.glb").write_bytes(b"glb")
    (fused_dir / "front.png").write_bytes(b"front")
    (fused_dir / "back.png").write_bytes(b"back")

    return StageContext(
        name="s09_export",
        job_dir=tmp_path,
        stage_dir=tmp_path / "s09_export",
        config=config,
        manifest={"job_id": JOB_ID},
        overrides={},
        logger=logging.getLogger(__name__),
    )


def _fake_export(args: list[str]) -> subprocess.CompletedProcess[str]:
    fbx = Path(args[args.index("--out-fbx") + 1])
    fbx.parent.mkdir(parents=True, exist_ok=True)
    fbx.write_bytes(b"fake-fbx")
    return subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='EXPORT_STATS {"meshes": 1, "textures": [], "color_attributes": ["Color"]}\n',
        stderr="",
    )


def test_s09_export_writes_valid_export_layout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run_blender(
        script: Path,
        args: list[str],
        config: dict[str, Any],
        *,
        log_path: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return _fake_export(args)

    monkeypatch.setattr(s09_export, "run_blender", fake_run_blender)
    result = s09_export.run(_context(tmp_path))

    export_dir = tmp_path / "s09_export" / JOB_ID
    manifest_path = export_dir / "import_manifest.json"
    import_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate(import_manifest, "import_manifest.schema.json")
    assert result.status == "ok"
    assert (export_dir / "fused/character_fused.fbx").is_file()
    assert (export_dir / "body/body_params.json").is_file()
    assert (export_dir / "previews/front.png").is_file()
    assert (export_dir / "previews/back.png").is_file()
    assert "material" not in import_manifest["meshes"][0]
    assert result.outputs == sorted(result.outputs)
    assert all(not Path(output).is_absolute() for output in result.outputs)
    assert set(result.outputs) == {
        "s09_export/20261010-000000-abcdef/fused/character_fused.fbx",
        "s09_export/20261010-000000-abcdef/body/body_params.json",
        "s09_export/20261010-000000-abcdef/previews/front.png",
        "s09_export/20261010-000000-abcdef/previews/back.png",
        "s09_export/20261010-000000-abcdef/import_manifest.json",
    }


def test_s09_export_removes_stale_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stale_dir = tmp_path / "s09_export" / JOB_ID
    stale_dir.mkdir(parents=True)
    (stale_dir / "stale.txt").write_text("stale", encoding="utf-8")
    monkeypatch.setattr(
        s09_export,
        "run_blender",
        lambda script, args, config, *, log_path=None: _fake_export(args),
    )

    s09_export.run(_context(tmp_path))

    assert not (stale_dir / "stale.txt").exists()


def test_s09_export_without_stats_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        s09_export,
        "run_blender",
        lambda script, args, config, *, log_path=None: subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        ),
    )

    result = s09_export.run(_context(tmp_path))

    assert result.status == "fail"
    assert result.messages == ["export_fbx.py printed no EXPORT_STATS line"]


def test_separate_mode_is_skipped(tmp_path: Path) -> None:
    result = s09_export.run(_context(tmp_path, mode="separate"))

    assert result.status == "skipped"


@pytest.mark.blender
def test_s09_export_runs_real_blender(
    tmp_path: Path,
) -> None:
    ctx = _context(tmp_path)
    mesh = trimesh.creation.box()
    mesh.visual = trimesh.visual.ColorVisuals(
        vertex_colors=[[200, 40, 40, 255]] * len(mesh.vertices)
    )
    glb = tmp_path / "s06_garments/fused/character_fused.glb"
    mesh.export(glb)
    result = s09_export.run(ctx)

    fbx = tmp_path / "s09_export" / JOB_ID / "fused/character_fused.fbx"
    assert result.status == "ok"
    assert fbx.is_file()
    assert fbx.stat().st_size > 1000
