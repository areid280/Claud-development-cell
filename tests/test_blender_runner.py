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


def _fake_blender(tmp_path: Path, body: str) -> dict:
    """A stand-in 'blender' executable so runner error handling is tested without Blender."""
    exe = tmp_path / "fake-blender"
    exe.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    exe.chmod(0o755)
    return {"tools": {"blender": str(exe), "blender_timeout_s": 30}}


def test_success_writes_log(tmp_path: Path) -> None:
    config = _fake_blender(tmp_path, 'echo "args: $*"')
    log = tmp_path / "logs" / "blender.log"

    result = run_blender(tmp_path / "script.py", ["--out", "x.fbx"], config, log_path=log)

    assert result.returncode == 0
    assert "--background --factory-startup --python" in log.read_text(encoding="utf-8")
    assert "-- --out x.fbx" in log.read_text(encoding="utf-8")


def test_traceback_in_output_raises(tmp_path: Path) -> None:
    config = _fake_blender(tmp_path, 'echo "Traceback (most recent call last):"; exit 0')

    with pytest.raises(BlenderError, match="Traceback"):
        run_blender(tmp_path / "script.py", [], config)


def test_timeout_raises_blender_error(tmp_path: Path) -> None:
    config = _fake_blender(tmp_path, "sleep 5")

    with pytest.raises(BlenderError, match="timed out"):
        run_blender(tmp_path / "script.py", [], config, timeout_s=1)
