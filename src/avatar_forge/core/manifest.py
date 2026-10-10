from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import jsonschema

from avatar_forge.core import schemas
from avatar_forge.core.paths import manifest_path

SCHEMA_VERSION = 1


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _validator() -> jsonschema.Draft202012Validator:
    """Manifest validator that resolves $refs to sibling schema files."""
    return schemas.validator("character_manifest.schema.json")


def new_manifest(job_id: str, consent: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "job_id": job_id,
        "created_at": now_iso(),
        "consent": consent,
        "inputs": [],
        "overrides": {},
        "stages": {},
        "body": None,
        "garments": [],
    }


def validate(manifest: dict[str, Any]) -> None:
    """Raise jsonschema.ValidationError if the manifest is invalid."""
    _validator().validate(manifest)


def load(job_dir: Path) -> dict[str, Any]:
    with manifest_path(job_dir).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save(job_dir: Path, manifest: dict[str, Any]) -> None:
    """Validate, then write atomically."""
    validate(manifest)
    path = manifest_path(job_dir)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)
