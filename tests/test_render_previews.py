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


@pytest.mark.blender
@pytest.mark.parametrize("up_axis", ["z", "y"])
def test_render_previews_stands_figure_upright(tmp_path: Path, up_axis: str) -> None:
    trimesh = pytest.importorskip("trimesh")
    import numpy as np
    from PIL import Image

    # Tall, wide, shallow "figure" (0.45 wide, 0.22 deep, 1.7 tall), authored Z-up or Y-up.
    figure = trimesh.creation.box(extents=(0.45, 0.22, 1.7))
    if up_axis == "y":
        figure.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, (1, 0, 0)))
    glb = tmp_path / "figure.glb"
    figure.export(glb)
    out_dir = tmp_path / "previews"

    run_blender(SCRIPT, ["--in", str(glb), "--out-dir", str(out_dir), "--size", "128"],
                load_pipeline_config())

    pixels = np.asarray(Image.open(out_dir / "front.png").convert("L")).astype(int)
    background = pixels[0, 0]
    rows, cols = np.nonzero(abs(pixels - background) > 8)
    assert rows.ptp() > 2 * cols.ptp()  # standing: much taller than wide in the front view
