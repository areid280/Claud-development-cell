from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from avatar_forge.blender_runner import BlenderError, run_blender
from avatar_forge.core.config import load_pipeline_config


def test_missing_blender_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(shutil, "which", lambda _: None)
    config = {"tools": {"blender": str(tmp_path / "missing-blender")}}

    with pytest.raises(
        BlenderError,
        match="Blender not found; run scripts/install_blender.sh",
    ):
        run_blender(tmp_path / "script.py", [], config)


@pytest.mark.blender
def test_hello_cube(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    script = project_root / "src" / "avatar_forge" / "blender" / "hello_cube.py"
    output = tmp_path / "cube.fbx"

    run_blender(script, ["--out", str(output)], load_pipeline_config())

    assert output.is_file()
    assert output.stat().st_size > 1024
