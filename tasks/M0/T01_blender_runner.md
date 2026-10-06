# T01 — Blender runner and smoke test
milestone: M0 · effort: low · depends: T00
owner input: none

## Goal
A single, tested way for pipeline code to run Blender headless scripts.

## Read first
- src/avatar_forge/blender/__init__.py
- src/avatar_forge/core/config.py (for `load_pipeline_config`)
- config/pipeline.yaml (`tools` section)

## Do
1. Create `src/avatar_forge/blender_runner.py` with:
   ```python
   class BlenderError(RuntimeError): ...

   def run_blender(script: Path, script_args: list[str], config: dict, *,
                   timeout_s: int | None = None, log_path: Path | None = None
                   ) -> subprocess.CompletedProcess[str]:
   ```
   - Binary = `config["tools"]["blender"]`; if that file does not exist,
     fall back to `shutil.which("blender")`; if neither, raise `BlenderError`
     with message "Blender not found; run scripts/install_blender.sh".
   - Command: `[blender, "--background", "--factory-startup", "--python",
     str(script), "--", *script_args]`.
   - Timeout default: `config["tools"]["blender_timeout_s"]`.
   - Capture stdout+stderr (text). If `log_path` given, write both to it.
   - Non-zero exit or the string `"Traceback (most recent call last)"` in
     output → raise `BlenderError` containing the last 30 lines.
2. Create `src/avatar_forge/blender/hello_cube.py` (runs inside Blender; must
   NOT import avatar_forge). It parses args after `--`: `--out <path.fbx>`,
   deletes the default scene objects, adds a 1 m cube, exports FBX to `--out`.
   Use `argparse` on `sys.argv[sys.argv.index("--") + 1:]`.
3. Create `tests/test_blender_runner.py`:
   - `test_missing_blender_raises` (no marker): config with a fake path and
     `monkeypatch.setattr(shutil, "which", lambda _: None)` → `BlenderError`.
   - `test_hello_cube` with `@pytest.mark.blender`: runs hello_cube into
     `tmp_path / "cube.fbx"`; asserts the file exists and is > 1 KB.

## Must not
- Add Blender's Python packages (`bpy`) to pyproject.
- Call Blender any other way anywhere in the codebase.

## Verify
- `ruff check src tests`
- `pytest -q tests/test_blender_runner.py` → 2 passed (on the pod, Blender test runs, not skipped).

## Done when
- [x] Both tests pass on the pod
- [x] Log contains the pytest output

## Escalate if
- Blender crashes on start-up with missing system libraries not listed in setup_pod.sh.

## Log
```text
$ ruff check src tests
All checks passed!

$ pytest -q tests/test_blender_runner.py
..                                                                       [100%]
2 passed in 2.12s
```
