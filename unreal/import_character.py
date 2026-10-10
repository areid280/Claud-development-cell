"""Import an AvatarForge export into Unreal Editor 5.6 or newer."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def load_import_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def plan_import(manifest: dict[str, Any], export_dir: Path) -> list[dict[str, Any]]:
    plans: list[dict[str, Any]] = []
    for mesh in manifest["meshes"]:
        material = mesh.get("material", {})
        plans.append(
            {
                "fbx": str((export_dir / mesh["path"]).resolve()),
                "destination": f"/Game/AvatarForge/{manifest['job_id']}",
                "asset_name": mesh["id"],
                "material": "garment" if material.get("basecolor") else "vertex_color",
                "textures": {
                    suffix: str((export_dir / path).resolve())
                    for suffix, path in material.items()
                },
            }
        )
    return plans


def _manifest_path() -> Path | None:
    configured = os.environ.get("AF_IMPORT_MANIFEST")
    if configured:
        return Path(configured)

    path_file = Path(__file__).with_name("import_manifest_path.txt")
    if path_file.is_file():
        first_line = path_file.read_text(encoding="utf-8").splitlines()
        if first_line and first_line[0].strip():
            return Path(first_line[0].strip())

    try:
        from tkinter import Tk, filedialog

        root = Tk()
        root.withdraw()
        selected = filedialog.askopenfilename(
            title="Select AvatarForge import_manifest.json",
            filetypes=[("AvatarForge manifest", "import_manifest.json"), ("JSON", "*.json")],
        )
        root.destroy()
        return Path(selected) if selected else None
    except Exception:
        return None


def ensure_vertex_color_material() -> str:
    import unreal

    asset_path = "/Game/AvatarForge/M_AF_VertexColor"
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return asset_path

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = asset_tools.create_asset(
        "M_AF_VertexColor",
        "/Game/AvatarForge",
        unreal.Material,
        unreal.MaterialFactoryNew(),
    )
    mel = unreal.MaterialEditingLibrary
    vertex_color = mel.create_material_expression(
        material, unreal.MaterialExpressionVertexColor, -400, 0
    )
    mel.connect_material_property(
        vertex_color, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    roughness = mel.create_material_expression(
        material, unreal.MaterialExpressionConstant, -400, 200
    )
    roughness.set_editor_property("r", 0.6)
    mel.connect_material_property(
        roughness, "", unreal.MaterialProperty.MP_ROUGHNESS
    )
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(material.get_path_name())
    return asset_path


def ensure_garment_material() -> str:
    import unreal

    asset_path = "/Game/AvatarForge/M_AF_Garment"
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return asset_path

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = asset_tools.create_asset(
        "M_AF_Garment",
        "/Game/AvatarForge",
        unreal.Material,
        unreal.MaterialFactoryNew(),
    )
    mel = unreal.MaterialEditingLibrary
    parameters = (
        ("BaseColor", unreal.TextureSamplerType.TSAMPLER_COLOR, -400, 0),
        ("Normal", unreal.TextureSamplerType.TSAMPLER_NORMAL, -400, 200),
        ("Roughness", unreal.TextureSamplerType.TSAMPLER_LINEAR_COLOR, -400, 400),
        ("Metallic", unreal.TextureSamplerType.TSAMPLER_LINEAR_COLOR, -400, 600),
    )
    for name, sampler, x, y in parameters:
        expression = mel.create_material_expression(
            material, unreal.MaterialExpressionTextureSampleParameter2D, x, y
        )
        expression.set_editor_property("parameter_name", name)
        expression.set_editor_property("sampler_type", sampler)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(material.get_path_name())
    return asset_path


def _import_fbx(entry: dict[str, Any]) -> None:
    import unreal

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", entry["fbx"])
    task.set_editor_property("destination_path", entry["destination"])
    task.set_editor_property("destination_name", entry["asset_name"])
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)

    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = False
    options.import_materials = False
    options.import_textures = False
    options.import_animations = False
    options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    options.static_mesh_import_data.set_editor_property(
        "vertex_color_import_option", unreal.VertexColorImportOption.REPLACE
    )
    options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    imported_paths = task.get_editor_property("imported_object_paths")
    for path in imported_paths:
        if entry["material"] == "vertex_color":
            mesh = unreal.EditorAssetLibrary.load_asset(path)
            material_path = ensure_vertex_color_material()
            mesh.set_material(0, unreal.EditorAssetLibrary.load_asset(material_path))
            unreal.EditorAssetLibrary.save_asset(path)
        unreal.log(f"AvatarForge: Imported {path}")


def main() -> None:
    import unreal

    manifest_path = _manifest_path()
    if manifest_path is None:
        unreal.log_error("Set AF_IMPORT_MANIFEST or import_manifest_path.txt")
        return

    manifest = load_import_manifest(manifest_path)
    export_dir = manifest_path.parent
    plans = plan_import(manifest, export_dir)
    if any(entry["material"] == "garment" for entry in plans):
        ensure_garment_material()
    for entry in plans:
        _import_fbx(entry)

    body = manifest["body"]
    measurements = body["measurements"]
    unreal.log(f"AvatarForge: Body height: {measurements['height']} cm")
    for name, value in measurements.items():
        unreal.log(f"AvatarForge: {name}: {value} cm")
    for name in ("skin", "hair", "eyes"):
        unreal.log(f"AvatarForge: {name}: {body['colors'][name]}")


if __name__ == "__main__":
    main()
