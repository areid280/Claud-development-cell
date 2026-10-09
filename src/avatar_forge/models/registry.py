"""Load the gate-approved model for a pipeline role (E-019).

    from avatar_forge.models.registry import load_selected
    with load_selected("bg_remove") as model:
        rgba = model.predict(image)

The entry comes from `selected_model(role)` (selected + licence_ok, decided at gate G1). The wrapper
class is found in `avatar_forge.models.<role>_<name>` (dashes/dots -> underscores), e.g.
pose + rtmlib-rtmw -> `pose_rtmlib_rtmw.RTMLibRTMW`; image_to_3d uses the `i23d_` prefix.
"""

from __future__ import annotations

import importlib

from avatar_forge.core.config import selected_model
from avatar_forge.models.base import ModelWrapper

MODULE_PREFIX = {"image_to_3d": "i23d"}  # wrapper files use a shorter prefix for this role


def wrapper_class(role: str, name: str) -> type[ModelWrapper]:
    prefix = MODULE_PREFIX.get(role, role)
    module_name = f"avatar_forge.models.{prefix}_{name.replace('-', '_').replace('.', '_')}"
    module = importlib.import_module(module_name)
    for attr in vars(module).values():
        if (
            isinstance(attr, type)
            and issubclass(attr, ModelWrapper)
            and attr is not ModelWrapper
            and getattr(attr, "role", None) == role
            and getattr(attr, "name", None) == name
        ):
            return attr
    raise LookupError(f"No {role} wrapper named {name!r} in {module_name}")


def load_selected(role: str, device: str = "cuda") -> ModelWrapper:
    """Return an (unloaded) wrapper for the approved model; use it as a context manager."""
    entry = selected_model(role)
    return wrapper_class(role, str(entry["name"]))(entry, device=device)
