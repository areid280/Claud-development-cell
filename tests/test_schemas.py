from __future__ import annotations

import jsonschema
import pytest

from avatar_forge.core import schemas

BODY = {
    "units": "cm",
    "source": "s05_body_params",
    "measurements": {"height": 168, "bust": 90, "underbust": 75, "waist": 70, "hips": 96,
                     "shoulder_width": 40, "inseam": 78},
    "colors": {"skin": "#e0b8a0", "hair": "#2b2420", "eyes": "#5a7a8c"},
}


def _import_manifest(body: dict) -> dict:
    return {
        "schema_version": 1,
        "job_id": "20261010-104423-71096a",
        "body": body,
        "meshes": [{"id": "character_fused", "kind": "fused", "path": "fused/character_fused.fbx"}],
    }


def test_import_manifest_resolves_body_params_ref() -> None:
    schemas.validate(_import_manifest(BODY), "import_manifest.schema.json")


def test_import_manifest_rejects_bad_body_through_ref() -> None:
    bad = {**BODY, "colors": {**BODY["colors"], "hair": "brown"}}
    with pytest.raises(jsonschema.ValidationError):
        schemas.validate(_import_manifest(bad), "import_manifest.schema.json")
