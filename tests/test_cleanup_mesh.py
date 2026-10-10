from __future__ import annotations

import json
import struct
from pathlib import Path

import pytest

from avatar_forge.blender_runner import run_blender
from avatar_forge.core.config import load_pipeline_config

SCRIPTS = Path(__file__).resolve().parents[1] / "src/avatar_forge/blender"
RED_SRGB = (200, 40, 40)
BLUE_SRGB = (40, 40, 200)


def _srgb_to_linear(value: int) -> float:
    c = value / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _color_0(glb: Path) -> list[tuple[float, float, float]]:
    """Read COLOR_0 as glTF floats (trimesh mis-reads Blender's normalised uint16 colours)."""
    import numpy as np

    data = glb.read_bytes()
    json_len = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20 : 20 + json_len])
    accessor = gltf["accessors"][gltf["meshes"][0]["primitives"][0]["attributes"]["COLOR_0"]]
    view = gltf["bufferViews"][accessor["bufferView"]]
    dtype, scale = {5121: (np.uint8, 255.0), 5123: (np.uint16, 65535.0), 5126: (np.float32, 1.0)}[
        accessor["componentType"]
    ]
    width = {"VEC3": 3, "VEC4": 4}[accessor["type"]]
    offset = 20 + json_len + 8 + view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    values = np.frombuffer(data, dtype=dtype, count=accessor["count"] * width, offset=offset)
    rgb = values.reshape(-1, width)[:, :3] / scale
    return [tuple(row) for row in np.unique(rgb.round(3), axis=0)]


def _two_colour_figure_with_speck(path: Path) -> int:
    """A 1 m tall Y-up figure (red top, blue bottom) plus a tiny loose cube. Returns triangles."""
    import numpy as np
    import trimesh

    from avatar_forge.models.mesh_axes import Z_UP_TO_Y_UP

    body = trimesh.creation.box(extents=(0.45, 0.22, 1.0))
    for _ in range(4):
        body = body.subdivide()
    speck = trimesh.creation.box(extents=(0.01, 0.01, 0.01))
    speck.apply_translation((0.6, 0.0, 0.3))
    mesh = trimesh.util.concatenate([body, speck])
    mesh.apply_transform(Z_UP_TO_Y_UP)
    colors = np.full((len(mesh.vertices), 4), 255, dtype=np.uint8)
    top = mesh.vertices[:, 1] > 0
    colors[top, :3] = RED_SRGB
    colors[~top, :3] = BLUE_SRGB
    mesh.visual = trimesh.visual.ColorVisuals(vertex_colors=colors)
    mesh.export(path)
    return len(mesh.faces)


@pytest.mark.blender
def test_cleanup_scales_places_decimates_and_keeps_linear_colours(tmp_path: Path) -> None:
    trimesh = pytest.importorskip("trimesh")
    raw = tmp_path / "raw.glb"
    triangles_in = _two_colour_figure_with_speck(raw)
    out = tmp_path / "fused" / "character_fused.glb"
    max_tris = 2000
    assert triangles_in > max_tris

    result = run_blender(
        SCRIPTS / "cleanup_mesh.py",
        ["--in", str(raw), "--out", str(out), "--height-m", "1.68", "--max-tris", str(max_tris),
         "--merge-dist", "0.0005", "--min-part-frac", "0.01"],
        load_pipeline_config(),
    )

    stats_line = next(line for line in result.stdout.splitlines() if line.startswith("CLEANUP_"))
    stats = json.loads(stats_line.split(" ", 1)[1])
    assert stats["parts_removed"] == 1
    mesh = trimesh.load(out, force="mesh")
    assert len(mesh.faces) == stats["triangles"] <= max_tris
    low, high = mesh.bounds  # glTF Y-up
    assert high[1] - low[1] == pytest.approx(1.68, abs=1e-3)
    assert low[1] == pytest.approx(0.0, abs=1e-4)
    assert (low[0] + high[0]) / 2 == pytest.approx(0.0, abs=1e-4)
    assert (low[2] + high[2]) / 2 == pytest.approx(0.0, abs=1e-4)
    assert high[0] - low[0] < 0.45 * 1.68 + 1e-3  # speck (0.6 m out) is gone
    expected = {tuple(round(_srgb_to_linear(c), 3) for c in rgb) for rgb in (RED_SRGB, BLUE_SRGB)}
    assert set(_color_0(out)) == expected


@pytest.mark.blender
def test_previews_show_vertex_colours(tmp_path: Path) -> None:
    pytest.importorskip("trimesh")
    import numpy as np
    from PIL import Image

    raw = tmp_path / "raw.glb"
    _two_colour_figure_with_speck(raw)
    out = tmp_path / "character_fused.glb"
    config = load_pipeline_config()
    run_blender(
        SCRIPTS / "cleanup_mesh.py",
        ["--in", str(raw), "--out", str(out), "--height-m", "1.68", "--max-tris", "100000",
         "--merge-dist", "0.0005", "--min-part-frac", "0.01"],
        config,
    )
    run_blender(SCRIPTS / "render_previews.py",
                ["--in", str(out), "--out-dir", str(tmp_path), "--size", "128"], config)

    pixels = np.asarray(Image.open(tmp_path / "front.png").convert("RGB")).astype(int)
    top, bottom = pixels[32, 64], pixels[100, 64]
    assert top[0] > top[2] + 40  # red half is red, not grey
    assert bottom[2] > bottom[0] + 40  # blue half is blue
