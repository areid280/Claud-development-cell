"""Project the front photo onto the fused mesh and bake one colour texture (runs inside Blender).

Usage (via avatar_forge.blender_runner.run_blender):
    blender --background --factory-startup --python project_texture.py -- \
        --in character_fused.glb --image front_rgba.png --out character_textured.glb \
        --tex-px 2048 --facing-min 0.2 --facing-full 0.6 --erode-px 3 --margin-px 8

The input is cleanup_mesh.py's output: metres, Blender Z-up, facing -Y, feet on z = 0, centred.
The photo is s02_prepare's cut-out (alpha = person). Alignment is orthographic: the photo's alpha
bounding box is matched to the mesh's front bounding box (height sets the scale, centres line up).
Each surface point takes the photo colour where it faces the camera and is not hidden (weight from
the normal and a ray cast), the mesh's own vertex colour elsewhere, blended smoothly; the photo's
alpha (eroded) stops background pixels bleeding in at the silhouette. The blend is baked with
Cycles into a new UV atlas (Smart UV Project) and exported as a GLB with a base-colour texture and
no vertex colours (glTF would multiply them in). Must not import avatar_forge.
Prints one "PROJECT_STATS {json}" line; "coverage" is the share of camera-facing visible vertices
that land inside the photo's silhouette (low = misaligned).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import bpy  # isort: split

import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ALPHA_SOLID = 0.5  # photo pixels above this alpha belong to the person
# Occlusion rays start this far toward the camera, so surface bumps and cloth folds closer than this
# never count as occluders (TRELLIS surfaces are bumpy at mm scale, E-026); arms, hands and cloaks
# that really hide the body are further away. A start point inside an occluder still hits it.
MIN_OCCLUDER_M = 0.02
WELD_DIST_M = 1e-5  # merge only coincident vertices (a soup's duplicated corners)
UV_ANGLE_LIMIT_RAD = 1.15  # Smart UV Project angle limit (about 66 degrees)
UV_ISLAND_MARGIN = 0.002
BAKE_SAMPLES = 4
ROUGHNESS = 0.6


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--tex-px", type=int, required=True)
    parser.add_argument("--facing-min", type=float, required=True)
    parser.add_argument("--facing-full", type=float, required=True)
    parser.add_argument("--erode-px", type=int, required=True)
    parser.add_argument("--margin-px", type=int, required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def _single_mesh() -> bpy.types.Object:
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if len(meshes) != 1:
        raise RuntimeError(f"expected the one fused mesh from cleanup_mesh.py, found {len(meshes)}")
    obj = meshes[0]
    obj.data.transform(obj.matrix_world)
    obj.parent = None
    obj.matrix_world.identity()
    # Weld and smooth: a triangle soup (flat-shaded GLB, E-026) gives one UV island per triangle and
    # breaks the visibility rays, so never rely on the input being welded.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=WELD_DIST_M)
    for face in bm.faces:
        face.smooth = True
    bm.normal_update()
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def _load_photo(path: Path, erode_px: int) -> tuple[bpy.types.Image, np.ndarray]:
    """Load the photo, erode its alpha in place, return (image, alpha[rows top->bottom, cols])."""
    image = bpy.data.images.load(str(path))
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    rgba = pixels.reshape(height, width, 4)  # Blender rows run bottom -> top
    alpha = rgba[:, :, 3] > ALPHA_SOLID
    for _ in range(erode_px):  # 4-neighbour erosion, one pixel per pass
        shrunk = alpha.copy()
        shrunk[1:, :] &= alpha[:-1, :]
        shrunk[:-1, :] &= alpha[1:, :]
        shrunk[:, 1:] &= alpha[:, :-1]
        shrunk[:, :-1] &= alpha[:, 1:]
        alpha = shrunk
    rgba[:, :, 3] = alpha.astype(np.float32)
    image.pixels.foreach_set(rgba.ravel())
    image.pack()
    return image, alpha[::-1]


def _fit(mesh: bpy.types.Mesh, alpha_top_down: np.ndarray) -> tuple[float, float, float, float]:
    """Orthographic map: pixel_x = cx_px + (x - cx_m) * s, pixel_y = bottom_px - z * s."""
    rows = np.flatnonzero(alpha_top_down.any(axis=1))
    cols = np.flatnonzero(alpha_top_down.any(axis=0))
    if rows.size == 0:
        raise RuntimeError("photo has no opaque pixels")
    xs = np.array([v.co.x for v in mesh.vertices])
    zs = np.array([v.co.z for v in mesh.vertices])
    scale = (rows[-1] + 1 - rows[0]) / (zs.max() - zs.min())
    cx_px = (cols[0] + cols[-1] + 1) / 2.0
    cx_m = (xs.min() + xs.max()) / 2.0
    bottom_px = rows[-1] + 1 + zs.min() * scale
    return scale, cx_px, cx_m, bottom_px


def _smoothstep(edge0: float, edge1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _photo_weights(
    obj: bpy.types.Object, options: argparse.Namespace
) -> tuple[np.ndarray, int, int]:
    """Per-vertex weight: faces the camera (at -Y, looking +Y) and nothing in front of it.
    Also returns how many camera-facing vertices were hidden, and how many face the camera."""
    mesh = obj.data
    normals = np.array([v.normal.y for v in mesh.vertices])
    facing = _smoothstep(options.facing_min, options.facing_full, -normals)
    polygons = [p.vertices[:] for p in mesh.polygons]
    tree = BVHTree.FromPolygons([v.co for v in mesh.vertices], polygons)
    toward_camera = Vector((0.0, -1.0, 0.0))
    visible = np.ones(len(mesh.vertices))
    for index, vert in enumerate(mesh.vertices):
        if facing[index] <= 0.0:
            continue
        hit, *_ = tree.ray_cast(vert.co + toward_camera * MIN_OCCLUDER_M, toward_camera)
        if hit is not None:
            visible[index] = 0.0
    facing_mask = facing > 0.0
    hidden = int((facing_mask & (visible == 0.0)).sum())
    return facing * visible, hidden, int(facing_mask.sum())


def _add_point_attribute(mesh: bpy.types.Mesh, name: str, values: np.ndarray) -> None:
    attribute = mesh.attributes.new(name, "FLOAT", "POINT")
    attribute.data.foreach_set("value", values.astype(np.float32))


def _projection_uvs(mesh: bpy.types.Mesh, fit: tuple[float, float, float, float], size) -> None:
    scale, cx_px, cx_m, bottom_px = fit
    width, height = size
    layer = mesh.uv_layers.new(name="proj")
    coords = np.array([mesh.vertices[loop.vertex_index].co[:] for loop in mesh.loops])
    u = (cx_px + (coords[:, 0] - cx_m) * scale) / width
    v = 1.0 - (bottom_px - coords[:, 2] * scale) / height
    layer.data.foreach_set("uv", np.column_stack([u, v]).astype(np.float32).ravel())


def _coverage(mesh, fit, alpha_top_down: np.ndarray, weights: np.ndarray) -> float:
    scale, cx_px, cx_m, bottom_px = fit
    seen = weights > ALPHA_SOLID
    if not seen.any():
        return 0.0
    co = np.array([v.co[:] for v in mesh.vertices])[seen]
    px = np.clip((cx_px + (co[:, 0] - cx_m) * scale).astype(int), 0, alpha_top_down.shape[1] - 1)
    py = np.clip((bottom_px - co[:, 2] * scale).astype(int), 0, alpha_top_down.shape[0] - 1)
    return float(alpha_top_down[py, px].mean())


def _atlas_uvs(obj: bpy.types.Object) -> None:
    layer = obj.data.uv_layers.new(name="atlas")
    obj.data.uv_layers.active = layer
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=UV_ANGLE_LIMIT_RAD, island_margin=UV_ISLAND_MARGIN)
    bpy.ops.object.mode_set(mode="OBJECT")


def _bake(obj: bpy.types.Object, photo: bpy.types.Image, options: argparse.Namespace):
    """Emission bake of mix(vertex colour, photo, weight * photo alpha) into the atlas."""
    vertex_color = obj.data.color_attributes[0].name if obj.data.color_attributes else None
    material = bpy.data.materials.new("af_project")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    base = nodes.new("ShaderNodeAttribute")
    base.attribute_name = vertex_color or ""
    proj_uv = nodes.new("ShaderNodeUVMap")
    proj_uv.uv_map = "proj"
    photo_node = nodes.new("ShaderNodeTexImage")
    photo_node.image = photo
    photo_node.extension = "CLIP"
    links.new(proj_uv.outputs["UV"], photo_node.inputs["Vector"])
    weight = nodes.new("ShaderNodeAttribute")
    weight.attribute_name = "af_photo_weight"
    mask = nodes.new("ShaderNodeMath")
    mask.operation = "MULTIPLY"
    links.new(weight.outputs["Fac"], mask.inputs[0])
    links.new(photo_node.outputs["Alpha"], mask.inputs[1])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    links.new(mask.outputs["Value"], mix.inputs["Factor"])
    links.new(base.outputs["Color"], mix.inputs["A"])
    links.new(photo_node.outputs["Color"], mix.inputs["B"])
    emission = nodes.new("ShaderNodeEmission")
    links.new(mix.outputs["Result"], emission.inputs["Color"])
    output = nodes.new("ShaderNodeOutputMaterial")
    links.new(emission.outputs["Emission"], output.inputs["Surface"])

    baked = bpy.data.images.new("basecolor", options.tex_px, options.tex_px, alpha=False)
    target = nodes.new("ShaderNodeTexImage")
    target.image = baked
    nodes.active = target  # Cycles bakes into the active image node, using the active UV map
    obj.data.materials.clear()
    obj.data.materials.append(material)

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = BAKE_SAMPLES
    bpy.ops.object.bake(type="EMIT", margin=options.margin_px, use_clear=True)
    baked.pack()
    return baked


def _final_material(obj: bpy.types.Object, baked: bpy.types.Image) -> None:
    material = bpy.data.materials.new("af_character")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes["Principled BSDF"]
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = baked
    links.new(texture.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = ROUGHNESS
    obj.data.materials.clear()
    obj.data.materials.append(material)
    mesh = obj.data
    mesh.uv_layers.remove(mesh.uv_layers["proj"])
    mesh.attributes.remove(mesh.attributes["af_photo_weight"])
    while mesh.color_attributes:
        mesh.color_attributes.remove(mesh.color_attributes[0])


def main() -> None:
    options = _parse_args()
    started = time.monotonic()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(options.input))
    obj = _single_mesh()
    mesh = obj.data
    photo, alpha = _load_photo(options.image, options.erode_px)
    fit = _fit(mesh, alpha)
    weights, hidden, facing_count = _photo_weights(obj, options)
    _add_point_attribute(mesh, "af_photo_weight", weights)
    _projection_uvs(mesh, fit, photo.size)
    coverage = _coverage(mesh, fit, alpha, weights)
    _atlas_uvs(obj)
    baked = _bake(obj, photo, options)
    _final_material(obj, baked)

    options.out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(options.out),
        export_format="GLB",
        export_yup=True,
        export_vertex_color="NONE",
        export_texcoords=True,
        export_image_format="AUTO",
    )
    stats = {
        "scale_px_per_m": round(float(fit[0]), 2),
        "photo_vertex_share": round(float((weights > ALPHA_SOLID).mean()), 3),
        "coverage": round(coverage, 3),
        "hidden_vertices": hidden,
        "facing_vertices": facing_count,
        "tex_px": options.tex_px,
        "seconds": round(time.monotonic() - started, 1),
    }
    print("PROJECT_STATS " + json.dumps(stats))


if __name__ == "__main__":
    main()
