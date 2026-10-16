from __future__ import annotations

import json
from pathlib import Path

import pytest

from avatar_forge.blender_runner import run_blender
from avatar_forge.core.config import load_pipeline_config

SCRIPTS = Path(__file__).resolve().parents[1] / "src/avatar_forge/blender"
BODY_SRGB = (200, 40, 40)
CHECK_A, CHECK_B = (255, 255, 255), (20, 160, 20)
PX_PER_M = 1000


def _figure(path: Path, blocker: bool) -> None:
    """A 0.45 x 0.22 x 1.7 m red 'body', optionally with a box in front of the chest (glTF Y-up)."""
    import numpy as np
    import trimesh

    from avatar_forge.models.mesh_axes import Z_UP_TO_Y_UP

    body = trimesh.creation.box(extents=(0.45, 0.22, 1.7))
    for _ in range(4):
        body = body.subdivide()
    parts = [body]
    if blocker:
        block = trimesh.creation.box(extents=(0.15, 0.1, 0.2))
        block.apply_translation((0.0, -0.25, 0.4))  # -Y is the front (camera side)
        parts.append(block)
    mesh = trimesh.util.concatenate(parts)
    mesh.apply_transform(Z_UP_TO_Y_UP)
    colors = np.tile(np.array([*BODY_SRGB, 255], dtype=np.uint8), (len(mesh.vertices), 1))
    mesh.visual = trimesh.visual.ColorVisuals(vertex_colors=colors)
    mesh.export(path)


def _checker_photo(path: Path) -> None:
    """Front photo of the figure's silhouette (1.7 x 0.45 m at PX_PER_M) filled with a checker."""
    import numpy as np
    from PIL import Image

    height_px, width_px = int(1.7 * PX_PER_M), int(0.45 * PX_PER_M)
    rows, cols = height_px + 200, width_px + 200
    yy, xx = np.mgrid[0:rows, 0:cols]
    inside = (yy >= 100) & (yy < 100 + height_px) & (xx >= 100) & (xx < 100 + width_px)
    checker = ((yy // 32 + xx // 32) % 2).astype(bool)
    image = np.zeros((rows, cols, 4), dtype=np.uint8)
    image[inside & checker] = (*CHECK_A, 255)
    image[inside & ~checker] = (*CHECK_B, 255)
    Image.fromarray(image, "RGBA").save(path)


def _project(tmp_path: Path, blocker: bool) -> tuple[dict, set[tuple[int, int, int]]]:
    from PIL import Image

    config = load_pipeline_config()
    _figure(tmp_path / "raw.glb", blocker)
    # as in s06: cleanup first (it fixes the colour space); keep the blocker (no part removal)
    run_blender(SCRIPTS / "cleanup_mesh.py",
                ["--in", str(tmp_path / "raw.glb"), "--out", str(tmp_path / "fused.glb"),
                 "--height-m", "1.7", "--max-tris", "100000", "--merge-dist", "0.0005",
                 "--min-part-frac", "0"], config)
    _checker_photo(tmp_path / "front_rgba.png")
    out = tmp_path / "textured.glb"
    result = run_blender(
        SCRIPTS / "project_texture.py",
        ["--in", str(tmp_path / "fused.glb"), "--image", str(tmp_path / "front_rgba.png"),
         "--out", str(out), "--tex-px", "512", "--facing-min", "0.2", "--facing-full", "0.6",
         "--erode-px", "3", "--margin-px", "4"],
        config,
    )
    line = next(row for row in result.stdout.splitlines() if row.startswith("PROJECT_STATS "))
    run_blender(SCRIPTS / "export_fbx.py",
                ["--in", str(out), "--out-fbx", str(tmp_path / "c.fbx"),
                 "--tex-dir", str(tmp_path / "tex")], config)
    texture = Image.open(tmp_path / "tex" / "c_basecolor.png").convert("RGB")
    return json.loads(line.split(" ", 1)[1]), set(texture.getdata())


@pytest.mark.blender
def test_front_takes_the_photo_and_back_keeps_mesh_colour(tmp_path: Path) -> None:
    pytest.importorskip("trimesh")
    stats, colours = _project(tmp_path, blocker=False)
    assert stats["coverage"] > 0.8
    assert stats["hidden_vertices"] == 0
    assert {CHECK_A, CHECK_B, BODY_SRGB} <= colours  # exact colours: no colour-space drift


@pytest.mark.blender
def test_hidden_surface_does_not_take_the_photo(tmp_path: Path) -> None:
    pytest.importorskip("trimesh")
    stats, _ = _project(tmp_path, blocker=True)
    assert stats["hidden_vertices"] > 0
