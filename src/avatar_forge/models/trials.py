from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

TrialFn = Callable[[dict[str, Any], Path, Path], dict[str, Any]]
REGISTRY: dict[tuple[str, str], TrialFn] = {}


class TrialSkippedError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)


def register(role: str, name: str) -> Callable[[TrialFn], TrialFn]:
    def decorator(trial_fn: TrialFn) -> TrialFn:
        key = (role, name)
        if key in REGISTRY:
            raise ValueError(f"A trial is already registered for {role!r}/{name!r}")
        REGISTRY[key] = trial_fn
        return trial_fn

    return decorator
