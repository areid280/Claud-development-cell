from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

SCRIPT = Path(__file__).resolve().parents[1] / "unreal" / "import_character.py"


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("avatar_forge_import_character", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_plan_import_for_fused_mesh(tmp_path: Path) -> None:
    module = _load_script()
    manifest = {
        "job_id": "job-123",
        "meshes": [
            {"id": "character_fused", "kind": "fused", "path": "fused/character_fused.fbx"}
        ],
    }

    plan = module.plan_import(manifest, tmp_path)

    assert len(plan) == 1
    assert plan[0]["material"] == "vertex_color"
    assert plan[0]["destination"] == "/Game/AvatarForge/job-123"
    assert plan[0]["fbx"] == str((tmp_path / "fused/character_fused.fbx").resolve())


def test_plan_import_for_garment_with_texture_paths(tmp_path: Path) -> None:
    module = _load_script()
    manifest = {
        "job_id": "job-456",
        "meshes": [
            {
                "id": "shirt",
                "kind": "garment",
                "path": "garments/shirt.fbx",
                "material": {"basecolor": "garments/textures/shirt_basecolor.png"},
            }
        ],
    }

    plan = module.plan_import(manifest, tmp_path)

    assert plan[0]["material"] == "garment"
    assert plan[0]["textures"]["basecolor"] == str(
        (tmp_path / "garments/textures/shirt_basecolor.png").resolve()
    )
