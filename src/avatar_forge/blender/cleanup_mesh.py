"""Clean, scale and place an image-to-3D GLB as one game-ready mesh (runs inside Blender).

Usage (via avatar_forge.blender_runner.run_blender):
    blender --background --factory-startup --python cleanup_mesh.py -- \
        --in raw.glb --out character_fused.glb --height-m 1.68 --max-tris 150000 \
        --merge-dist 0.0005 --min-part-frac 0.01

Steps: join all meshes, merge by distance, drop loose parts smaller than --min-part-frac of all
vertices, recalculate normals outside, decimate (collapse) above --max-tris, scale uniformly to
--height-m, put the lowest point on z = 0 and centre x/y on 0, export GLB with vertex colours.
The input is trusted to be glTF Y-up facing +Z (E-018), i.e. Blender Z-up facing -Y: never rotate.
Must not import avatar_forge. Prints one "CLEANUP_STATS {json}" line for the caller's log.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy  # isort: split

import bmesh  # after bpy: the standalone bpy module only provides bmesh once bpy is loaded
from mathutils import Matrix, Vector

DECIMATE_HEADROOM = 0.99  # collapse can overshoot the requested ratio slightly


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--height-m", type=float, required=True)
    parser.add_argument("--max-tris", type=int, required=True)
    parser.add_argument("--merge-dist", type=float, required=True)
    parser.add_argument("--min-part-frac", type=float, required=True)
    parser.add_argument(
        "--color-space",
        choices=("srgb", "linear"),
        default="srgb",
        help="what the input COLOR_0 values really are (see _fix_color_space)",
    )
    options = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    if options.height_m <= 0 or options.max_tris <= 0:
        parser.error("--height-m and --max-tris must be positive")
    return options


def _joined_mesh_object() -> bpy.types.Object:
    """Bake every mesh's world transform into its data, unparent, and join them into one object."""
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("GLB contains no mesh objects")
    for obj in meshes:
        obj.data.transform(obj.matrix_world)
        obj.parent = None
        obj.matrix_world = Matrix.Identity(4)
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


def _remove_small_parts(bm: bmesh.types.BMesh, min_fraction: float) -> int:
    """Delete connected parts with < min_fraction of all vertices; return how many were removed."""
    total = len(bm.verts)
    seen: set[int] = set()
    doomed: list[bmesh.types.BMVert] = []
    removed = 0
    bm.verts.ensure_lookup_table()
    for start in bm.verts:
        if start.index in seen:
            continue
        island = [start]
        seen.add(start.index)
        stack = [start]
        while stack:
            vert = stack.pop()
            for edge in vert.link_edges:
                other = edge.other_vert(vert)
                if other.index not in seen:
                    seen.add(other.index)
                    island.append(other)
                    stack.append(other)
        if len(island) < min_fraction * total:
            doomed.extend(island)
            removed += 1
    if doomed:
        bmesh.ops.delete(bm, geom=doomed, context="VERTS")
    return removed


def _fix_color_space(mesh: bpy.types.Mesh, color_space: str) -> None:
    """Reinterpret colours written as display (sRGB) values into glTF's linear COLOR_0.

    Image-to-3D models output sRGB vertex colours and trimesh stores them unchanged, but glTF
    defines COLOR_0 as linear, so Blender (and UE) would show them washed out. Re-storing the
    imported numbers as sRGB fixes the meaning; the exporter then writes correct linear values.
    """
    if color_space != "srgb":
        return
    for attribute in mesh.color_attributes:
        values = [0.0] * (len(attribute.data) * 4)
        attribute.data.foreach_get("color", values)
        attribute.data.foreach_set("color_srgb", values)


def _triangle_count(mesh: bpy.types.Mesh) -> int:
    return sum(len(poly.vertices) - 2 for poly in mesh.polygons)


def main() -> None:
    options = _parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(options.input))
    obj = _joined_mesh_object()
    mesh = obj.data
    _fix_color_space(mesh, options.color_space)
    triangles_in = _triangle_count(mesh)

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=options.merge_dist)
    parts_removed = _remove_small_parts(bm, options.min_part_frac)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    triangles = _triangle_count(mesh)
    if triangles > options.max_tris:
        modifier = obj.modifiers.new("decimate", "DECIMATE")
        modifier.decimate_type = "COLLAPSE"
        modifier.ratio = options.max_tris / triangles * DECIMATE_HEADROOM
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        triangles = _triangle_count(mesh)

    corners = [vert.co for vert in mesh.vertices]
    low = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    high = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    height = high.z - low.z
    if height <= 0:
        raise RuntimeError("mesh has zero height")
    scale = options.height_m / height
    anchor = Vector(((low.x + high.x) / 2.0, (low.y + high.y) / 2.0, low.z))
    mesh.transform(Matrix.Scale(scale, 4) @ Matrix.Translation(-anchor))
    mesh.update()

    options.out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(options.out),
        export_format="GLB",
        export_yup=True,
        export_vertex_color="ACTIVE",  # D-015: vertex colours are the MVP's only colour source
        export_all_vertex_colors=True,
        export_texcoords=False,  # no UVs in M2 (D-015)
    )
    stats = {
        "triangles_in": triangles_in,
        "triangles": triangles,
        "parts_removed": parts_removed,
        "scale": scale,
        "color_attributes": [attr.name for attr in mesh.color_attributes],
    }
    print("CLEANUP_STATS " + json.dumps(stats))


if __name__ == "__main__":
    main()
