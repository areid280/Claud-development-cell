from __future__ import annotations

from pathlib import Path

import pytest

from avatar_forge.blender_runner import run_blender
from avatar_forge.core.config import load_pipeline_config

SCRIPT = Path(__file__).resolve().parents[1] / "src/avatar_forge/blender/render_previews.py"


@pytest.mark.blender
def test_render_previews_writes_front_and_back(tmp_path: Path) -> None:
    trimesh = pytest.importorskip("trimesh")
    from PIL import Image

    glb = tmp_path / "box.glb"
    trimesh.creation.box(extents=(0.4, 0.2, 1.7)).export(glb)
    out_dir = tmp_path / "previews"

    run_blender(SCRIPT, ["--in", str(glb), "--out-dir", str(out_dir), "--size", "128"],
                load_pipeline_config())

    for view in ("front", "back"):
        image = Image.open(out_dir / f"{view}.png")
        assert image.size == (128, 128)
        assert len(set(image.convert("L").getdata())) > 1  # not a blank frame
