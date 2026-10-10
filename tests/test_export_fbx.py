from __future__ import annotations

import json
from pathlib import Path

import pytest

from avatar_forge.blender_runner import run_blender
from avatar_forge.core.config import load_pipeline_config
from test_cleanup_mesh import RED_SRGB, SCRIPTS, _two_colour_figure_with_speck

# Re-imports an FBX and prints its height and distinct sRGB vertex colours (runs inside Blender).
CHECK_SCRIPT = '''
import json, sys
import bpy
path = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=path)
obj = next(o for o in bpy.context.scene.objects if o.type == "MESH")
zs = [(obj.matrix_world @ v.co).z for v in obj.data.vertices]
attr = obj.data.color_attributes[0]
colors = sorted({tuple(round(c * 255) for c in d.color_srgb[:3]) for d in attr.data})
print("CHECK " + json.dumps({"height": max(zs) - min(zs), "colors": colors}))
'''


def _stats(stdout: str, prefix: str) -> dict:
    line = next(line for line in stdout.splitlines() if line.startswith(prefix + " "))
    return json.loads(line.split(" ", 1)[1])


@pytest.mark.blender
def test_fused_vertex_colour_mesh_exports_to_fbx(tmp_path: Path) -> None:
    pytest.importorskip("trimesh")
    config = load_pipeline_config()
    raw = tmp_path / "raw.glb"
    _two_colour_figure_with_speck(raw)
    glb = tmp_path / "character_fused.glb"
    run_blender(SCRIPTS / "cleanup_mesh.py",
                ["--in", str(raw), "--out", str(glb), "--height-m", "1.68", "--max-tris", "100000",
                 "--merge-dist", "0.0005", "--min-part-frac", "0.01"], config)
    fbx = tmp_path / "fused" / "character_fused.fbx"

    tex_dir = tmp_path / "tex"
    result = run_blender(
        SCRIPTS / "export_fbx.py",
        ["--in", str(glb), "--out-fbx", str(fbx), "--tex-dir", str(tex_dir)],
        config,
    )

    stats = _stats(result.stdout, "EXPORT_STATS")
    assert stats["textures"] == [] and stats["color_attributes"]
    check_script = tmp_path / "check.py"
    check_script.write_text(CHECK_SCRIPT, encoding="utf-8")
    check = _stats(run_blender(check_script, [str(fbx)], config).stdout, "CHECK")
    assert check["height"] == pytest.approx(1.68, abs=1e-3)
    assert list(RED_SRGB) in check["colors"]  # display colours survive GLB -> FBX


@pytest.mark.blender
def test_textures_are_written_by_socket(tmp_path: Path) -> None:
    trimesh = pytest.importorskip("trimesh")
    import numpy as np
    from PIL import Image

    box = trimesh.creation.box()
    uv = np.random.default_rng(0).random((len(box.vertices), 2))
    image = Image.new("RGB", (64, 32), (10, 120, 200))
    box.visual = trimesh.visual.TextureVisuals(uv=uv, image=image)
    glb = tmp_path / "jacket.glb"
    box.export(glb)

    result = run_blender(SCRIPTS / "export_fbx.py",
                         ["--in", str(glb), "--out-fbx", str(tmp_path / "jacket.fbx"),
                          "--tex-dir", str(tmp_path / "tex")], load_pipeline_config())

    assert _stats(result.stdout, "EXPORT_STATS")["textures"] == ["jacket_basecolor.png"]
    saved = Image.open(tmp_path / "tex" / "jacket_basecolor.png").convert("RGB")
    assert saved.size == (64, 32)
    assert saved.getpixel((5, 5)) == (10, 120, 200)  # the real texture, not a re-render
