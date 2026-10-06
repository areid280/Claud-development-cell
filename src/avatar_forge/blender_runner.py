from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class BlenderError(RuntimeError):
    """Raised when Blender cannot be found or a Blender script fails."""


def run_blender(
    script: Path,
    script_args: list[str],
    config: dict,
    *,
    timeout_s: int | None = None,
    log_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    configured_blender = Path(config["tools"]["blender"])
    if configured_blender.is_file():
        blender = str(configured_blender)
    else:
        blender = shutil.which("blender")
        if blender is None:
            raise BlenderError(
                "Blender not found; run scripts/install_blender.sh"
            )

    timeout = timeout_s
    if timeout is None:
        timeout = config["tools"]["blender_timeout_s"]

    result = subprocess.run(
        [
            blender,
            "--background",
            "--factory-startup",
            "--python",
            str(script),
            "--",
            *script_args,
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(output, encoding="utf-8")

    if result.returncode != 0 or "Traceback (most recent call last)" in output:
        last_lines = "\n".join(output.splitlines()[-30:])
        raise BlenderError(f"Blender script failed:\n{last_lines}")

    return result
