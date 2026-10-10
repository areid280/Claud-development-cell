"""Convert a GLB to a UE5-ready FBX plus PNG textures (runs inside Blender).

Usage (via avatar_forge.blender_runner.run_blender):
    blender --background --factory-startup --python export_fbx.py -- \
        --in character_fused.glb --out-fbx fused/character_fused.fbx --tex-dir textures/ \
        [--id character_fused]

Textures feeding the Principled BSDF are written as <id>_basecolor.png, <id>_normal.png,
<id>_roughness.png, <id>_metallic.png (only those that exist; the MVP fused mesh has none, D-015).
A glTF ORM image feeding roughness and metallic via Separate Color is written once per socket.
Vertex colours are exported as sRGB (D-015 addendum). Must not import avatar_forge.
Prints one "EXPORT_STATS {json}" line for the caller.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy

SOCKETS = {
    "Base Color": "basecolor",
    "Normal": "normal",
    "Roughness": "roughness",
    "Metallic": "metallic",
}
MAX_NODE_DEPTH = 4  # BSDF <- Mix/Normal Map/Separate Color <- image is at most a few hops


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument("--out-fbx", type=Path, required=True)
    parser.add_argument("--tex-dir", type=Path, required=True)
    parser.add_argument("--id", dest="mesh_id", help="texture name prefix (default: FBX stem)")
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def _source_image(socket: bpy.types.NodeSocket, depth: int = 0) -> bpy.types.Image | None:
    """Search back from a BSDF input to the first image, through the helper nodes the glTF
    importer inserts (Mix for colour factors, Normal Map, Separate Color for ORM)."""
    if depth > MAX_NODE_DEPTH or not socket.is_linked:
        return None
    node = socket.links[0].from_node
    if node.type == "TEX_IMAGE":
        return node.image
    for upstream in node.inputs:
        image = _source_image(upstream, depth + 1)
        if image is not None:
            return image
    return None


def _save_textures(tex_dir: Path, mesh_id: str) -> list[str]:
    written: list[str] = []
    for material in bpy.data.materials:
        if material.node_tree is None:
            continue
        for node in material.node_tree.nodes:
            if node.type != "BSDF_PRINCIPLED":
                continue
            for socket_name, suffix in SOCKETS.items():
                image = _source_image(node.inputs[socket_name])
                if image is None:
                    continue
                tex_dir.mkdir(parents=True, exist_ok=True)
                path = tex_dir / f"{mesh_id}_{suffix}.png"
                image.file_format = "PNG"
                image.save(filepath=str(path))
                written.append(path.name)
    return sorted(set(written))


def main() -> None:
    options = _parse_args()
    mesh_id = options.mesh_id or options.out_fbx.stem
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(options.input))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("GLB contains no mesh objects")

    textures = _save_textures(options.tex_dir, mesh_id)
    options.out_fbx.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=str(options.out_fbx),
        object_types={"MESH", "ARMATURE"},
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Y",
        axis_up="Z",
        path_mode="STRIP",
        embed_textures=False,
        colors_type="SRGB",
        mesh_smooth_type="FACE",  # UE warns "No smoothing group information" without it
        add_leaf_bones=False,
        bake_anim=False,
    )
    stats = {
        "meshes": len(meshes),
        "textures": textures,
        "color_attributes": sorted({a.name for obj in meshes for a in obj.data.color_attributes}),
    }
    print("EXPORT_STATS " + json.dumps(stats))


if __name__ == "__main__":
    main()
