from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from avatar_forge.core.paths import CONFIG_DIR


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping at the top level")
    return data


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Return a new dict: values in `override` win; nested dicts are merged."""
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def load_pipeline_config(extra: Path | None = None) -> dict[str, Any]:
    """Load config/pipeline.yaml, optionally merged with an extra YAML file."""
    cfg = load_yaml(CONFIG_DIR / "pipeline.yaml")
    if extra is not None:
        cfg = deep_merge(cfg, load_yaml(extra))
    return cfg


def load_models_config() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "models.yaml")


def selected_model(role: str) -> dict[str, Any]:
    """Return the selected, licence-approved model entry for a role.

    Raises if none is selected or its licence has not been approved at gate G1.
    """
    models = load_models_config().get("roles", {}).get(role, {}).get("candidates", [])
    chosen = [m for m in models if m.get("selected")]
    if not chosen:
        raise LookupError(f"No model selected for role '{role}' (decided at gate G1)")
    model = chosen[0]
    if not model.get("licence_ok"):
        raise PermissionError(
            f"Model '{model.get('name')}' for role '{role}' has licence_ok: false. "
            "Only the gatekeeper may approve it."
        )
    return model
