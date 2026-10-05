from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = REPO_ROOT / "config"
SCHEMA_DIR = REPO_ROOT / "schemas"


def jobs_root() -> Path:
    """Where job folders live. Override with AF_JOBS_DIR."""
    return Path(os.environ.get("AF_JOBS_DIR", REPO_ROOT / "jobs"))


def weights_dir() -> Path:
    """Where model weights live (never in git). Override with AF_WEIGHTS_DIR."""
    return Path(os.environ.get("AF_WEIGHTS_DIR", "/workspace/weights"))


def stage_dir(job_dir: Path, stage_name: str) -> Path:
    return job_dir / stage_name


def manifest_path(job_dir: Path) -> Path:
    return job_dir / "manifest.json"
