from __future__ import annotations

import gc
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Self

from avatar_forge.core.config import load_models_config


class ModelWrapper(ABC):
    role: ClassVar[str]
    name: ClassVar[str]

    def __init__(self, entry: dict[str, Any], device: str = "cuda") -> None:
        self.entry = entry
        self.device = device

    @abstractmethod
    def load(self) -> None:
        """Load model resources into this wrapper."""

    def unload(self) -> None:
        for attribute in tuple(vars(self)):
            if attribute not in {"entry", "device"}:
                delattr(self, attribute)

        gc.collect()
        try:
            import torch
        except ImportError:
            return

        torch.cuda.empty_cache()

    def __enter__(self) -> Self:
        self.load()
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.unload()


def vram_peak_gb() -> float:
    try:
        import torch
    except ImportError:
        return 0.0

    if not torch.cuda.is_available():
        return 0.0
    return float(torch.cuda.max_memory_allocated() / 1e9)


def reset_vram_peak() -> None:
    try:
        import torch
    except ImportError:
        return

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()


def model_entry(role: str, name: str) -> dict[str, Any]:
    config = load_models_config()
    roles = config.get("roles", config)
    role_config = roles.get(role, {})
    for candidate in role_config.get("candidates", []):
        if candidate.get("name") == name:
            return candidate

    raise KeyError(f"Unknown model {name!r} for role {role!r}")
