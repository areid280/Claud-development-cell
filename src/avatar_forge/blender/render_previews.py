"""Render front and back preview PNGs of a GLB with Workbench (runs inside Blender).

Usage (via avatar_forge.blender_runner.run_blender):
    blender --background --factory-startup --python render_previews.py -- \
        --in mesh.glb --out-dir previews/ [--size 768]

Writes <out-dir>/front.png and <out-dir>/back.png. Must not import avatar_forge.
Models do not agree on "up" (TripoSR writes Z-up meshes into a Y-up format), so the figure is
stood upright from the file convention and turned to face the camera axis (see _auto_orient).
Front and back may come out swapped for some models; both views are always rendered.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

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


def _auto_orient() -> None:
    """Stand the figure along +Z and turn it to face the Y axis.

    If the figure lies along Blender Y, the file was written Z-up (e.g. TripoSR); rotating -90°
    about X exactly undoes the importer's Y-up conversion. Shape alone cannot tell head from
    feet, so the sign comes from that file convention rather than a guess.
    """
    low, high = _mesh_bounds()
    extent = high - low
    height_axis = max(range(3), key=lambda axis: extent[axis])
    rotations = {
        0: Matrix.Rotation(math.radians(-90.0), 4, "Y"),  # X-up file: +X -> +Z
        1: Matrix.Rotation(math.radians(-90.0), 4, "X"),  # Z-up file: undo the glTF import turn
        2: Matrix.Identity(4),
    }
    _apply(rotations[height_axis])
    low, high = _mesh_bounds()
    extent = high - low
    if extent.x < extent.y:  # narrow along X: the figure faces sideways; turn it to face Y
        _apply(Matrix.Rotation(math.radians(90.0), 4, "Z"))


def _apply(transform: Matrix) -> None:
    for obj in bpy.context.scene.objects:
        if obj.parent is None:
            obj.matrix_world = transform @ obj.matrix_world
    bpy.context.view_layer.update()


def _setup_scene(size: int) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "TEXTURE"  # falls back to material colour when a mesh has no texture
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
    _auto_orient()
    _setup_scene(options.size)

    low, high = _mesh_bounds()
    centre = (low + high) / 2.0
    extent = high - low
    _render_view("front", centre, extent, -1.0, options.out_dir)
    _render_view("back", centre, extent, 1.0, options.out_dir)


if __name__ == "__main__":
    main()
