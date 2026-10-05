from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from PIL import Image


def _has_gpu() -> bool:
    try:
        import torch
    except ImportError:
        return False
    return bool(torch.cuda.is_available())


def _has_blender() -> bool:
    from avatar_forge.core.config import load_pipeline_config

    configured = load_pipeline_config()["tools"]["blender"]
    return Path(configured).is_file() or shutil.which("blender") is not None


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    checks = {
        "gpu": (_has_gpu(), "no NVIDIA GPU available"),
        "blender": (_has_blender(), "Blender not installed (scripts/install_blender.sh)"),
    }
    for marker, (available, reason) in checks.items():
        if available:
            continue
        skip = pytest.mark.skip(reason=reason)
        for item in items:
            if marker in item.keywords:
                item.add_marker(skip)


@pytest.fixture
def front_image(tmp_path: Path) -> Path:
    """A synthetic 1024x1536 RGB image (not a person; for plumbing tests only)."""
    path = tmp_path / "front.jpg"
    Image.new("RGB", (1024, 1536), (180, 160, 150)).save(path)
    return path


@pytest.fixture
def jobs_dir(tmp_path: Path) -> Path:
    d = tmp_path / "jobs"
    d.mkdir()
    return d
