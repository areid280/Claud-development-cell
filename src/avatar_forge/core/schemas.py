"""JSON-schema validators that resolve $refs between files in schemas/ (e.g. body_params)."""

from __future__ import annotations

import json
from functools import cache
from typing import Any

import jsonschema
from referencing import Registry, Resource

from avatar_forge.core.paths import SCHEMA_DIR


def load_schema(name: str) -> dict[str, Any]:
    with (SCHEMA_DIR / name).open("r", encoding="utf-8") as fh:
        return json.load(fh)


@cache
def _registry() -> Registry:
    registry: Registry = Registry()
    for path in SCHEMA_DIR.glob("*.schema.json"):
        registry = registry.with_resource(path.name, Resource.from_contents(load_schema(path.name)))
    return registry


def validator(name: str) -> jsonschema.Draft202012Validator:
    """Validator for schemas/<name>; `$ref: "body_params.schema.json"` etc. resolve."""
    return jsonschema.Draft202012Validator(load_schema(name), registry=_registry())


def validate(data: Any, name: str) -> None:
    """Raise jsonschema.ValidationError if data does not match schemas/<name>."""
    validator(name).validate(data)
