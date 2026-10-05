"""The stage contract. Do not change without a gate decision (docs/01_ARCHITECTURE.md §6)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Status = Literal["ok", "warn", "fail", "skipped"]


@dataclass(frozen=True)
class StageContext:
    """Everything a stage is allowed to see."""

    name: str
    job_dir: Path
    stage_dir: Path
    config: dict[str, Any]
    manifest: dict[str, Any]  # read-only snapshot; stages must not mutate it
    overrides: dict[str, Any]
    logger: logging.Logger

    def stage_config(self) -> dict[str, Any]:
        """Config block for this stage, e.g. config['stages']['s01_validate']."""
        return self.config.get("stages", {}).get(self.name, {})

    def previous_output(self, stage_name: str, relative: str) -> Path:
        """Path to a file another stage produced. Raises if it does not exist."""
        path = self.job_dir / stage_name / relative
        if not path.exists():
            raise FileNotFoundError(f"{self.name} needs {path}, which {stage_name} did not produce")
        return path


@dataclass
class StageResult:
    status: Status
    outputs: list[str] = field(default_factory=list)  # paths relative to job_dir
    messages: list[str] = field(default_factory=list)  # human-readable, shown in CLI/UI
    data: dict[str, Any] = field(default_factory=dict)  # small summary stored in manifest

    @classmethod
    def not_implemented(cls, task_id: str) -> StageResult:
        return cls(status="skipped", messages=[f"not implemented yet ({task_id})"])
