"""Render front and back preview PNGs of a GLB with Workbench (runs inside Blender).

Usage (via avatar_forge.blender_runner.run_blender):
    blender --background --factory-startup --python render_previews.py -- \
        --in mesh.glb --out-dir previews/ [--size 768]

Writes <out-dir>/front.png and <out-dir>/back.png. Must not import avatar_forge.
The GLB is trusted to be glTF Y-up (+Z forward); Blender's importer turns that into +Z up with the
model facing -Y, so the "front" camera sits on -Y. Wrappers convert their meshes to Y-up before
export (avatar_forge.models.mesh_axes, E-018); this script never guesses orientation.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

MARGIN = 1.1  # frame the mesh with 10% padding


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--size", type=int, default=768)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def _mesh_bounds() -> tuple[Vector, Vector]:
    corners = [
        obj.matrix_world @ Vector(corner)
        for obj in bpy.context.scene.objects
        if obj.type == "MESH"
        for corner in obj.bound_box
    ]
    if not corners:
        raise RuntimeError("GLB contains no mesh objects")
    low = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    high = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return low, high


def _uses_vertex_colors() -> bool:
    """True when every mesh has a colour attribute and none has an image texture."""
    meshes = [obj.data for obj in bpy.context.scene.objects if obj.type == "MESH"]
    has_texture = any(
        node.type == "TEX_IMAGE"
        for mesh in meshes
        for material in mesh.materials
        if material is not None and material.node_tree is not None
        for node in material.node_tree.nodes
    )
    return bool(meshes) and all(mesh.color_attributes for mesh in meshes) and not has_texture


def _setup_scene(size: int) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"  # show colours as stored (AgX shifts them)
    shading = scene.display.shading
    shading.light = "STUDIO"
    # Vertex-coloured meshes (image-to-3D output, D-015) need VERTEX; TEXTURE ignores them.
    shading.color_type = "VERTEX" if _uses_vertex_colors() else "TEXTURE"
    shading.show_cavity = True


def _render_view(name: str, centre: Vector, extent: Vector, side: float, out_dir: Path) -> None:
    distance = max(extent) * 3.0 + 1.0
    camera_data = bpy.data.cameras.new(f"cam_{name}")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = max(extent.x, extent.z) * MARGIN
    camera_data.clip_end = distance * 4.0
    camera = bpy.data.objects.new(f"cam_{name}", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = centre + Vector((0.0, side * distance, 0.0))
    # Cameras look down their local -Z; rotate so it points along -side*Y at the mesh centre.
    camera.rotation_euler = (math.radians(90.0), 0.0, 0.0 if side < 0 else math.radians(180.0))
    bpy.context.scene.camera = camera
    bpy.context.scene.render.filepath = str(out_dir / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    options = _parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(options.input))
    options.out_dir.mkdir(parents=True, exist_ok=True)
    _setup_scene(options.size)

    low, high = _mesh_bounds()
    centre = (low + high) / 2.0
    extent = high - low
    _render_view("front", centre, extent, -1.0, options.out_dir)
    _render_view("back", centre, extent, 1.0, options.out_dir)


if __name__ == "__main__":
    main()
