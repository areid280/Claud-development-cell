# T02 — Stage s00_ingest
milestone: M0 · effort: low · depends: T00
owner input: none

## Goal
Normalise input images (orientation, colour mode, size) and record metadata.

## Read first
- src/avatar_forge/stages/s00_ingest.py (docstring = contract)
- src/avatar_forge/core/stage.py
- config/pipeline.yaml → `stages.s00_ingest`
- tests/test_core.py lines 1-13 and 75-81 (how existing tests import and call `create_job` / `run_job`)

## Do
1. Implement `run(ctx)` in `s00_ingest.py`:
   - For each entry in `ctx.manifest["inputs"]`: open `ctx.job_dir / entry["path"]` with Pillow.
   - Apply `ImageOps.exif_transpose`.
   - Convert to `RGBA` if the image has an alpha channel, else `RGB`.
   - If the long side > `ctx.stage_config()["max_long_side_px"]`, downscale
     (keep aspect, `Image.LANCZOS`).
   - Save as `ctx.stage_dir / f"{view}.png"`.
   - SHA-256 of the **original input file bytes**.
   - Return `StageResult(status="ok", outputs=[<relative paths>],
     data={"views": {view: {"width": w, "height": h, "sha256": sha, "downscaled": bool}}})`
     where width/height are of the saved PNG.
   - A file Pillow can't open → `status="fail"`, message "Cannot read <view> image: <reason>".
2. Create `tests/test_s00_ingest.py` (use the `front_image` and `jobs_dir` fixtures
   from conftest and `create_job` + `run_job(..., to_stage="s00_ingest")`).
   Use exactly these imports (added by Opus, E-002):
   ```python
   from avatar_forge.core.config import load_pipeline_config
   from avatar_forge.core.job import create_job
   from avatar_forge.core.runner import StageFailedError, run_job
   ```
   Call pattern (same as tests/test_core.py):
   ```python
   job = create_job({"front": path}, adult_confirmed=True, consent_confirmed=True, root=jobs_dir)
   results = run_job(job, load_pipeline_config(), to_stage="s00_ingest")
   data = results["s00_ingest"].data["views"]["front"]
   out = Image.open(job / "s00_ingest" / "front.png")
   ```
   For the downscale test compare against
   `load_pipeline_config()["stages"]["s00_ingest"]["max_long_side_px"]` (no hard-coded 4096).
   Tests:
   - JPEG with EXIF orientation 6 (rotate 90°) of size 1000×600 → output is 600×1000.
     Make it with: `img = Image.new("RGB", (1000, 600)); exif = img.getexif();
     exif[0x0112] = 6; img.save(path, exif=exif)`.
   - 5000×3000 image → long side equals `max_long_side_px`, `downscaled: True`.
   - PNG with alpha → output mode `RGBA`.
   - Corrupt file (write b"not an image" to `x.jpg`) → `StageFailedError` raised by run_job.

3. Add `"downscaled": bool` to the `Data:` line of the module docstring in
   `s00_ingest.py` so the docstring matches step 1.

## Must not
- Change the stage signature or edit the manifest from the stage.
- Change anything under `src/avatar_forge/core/` (the imports above already exist).

## Verify
- `ruff check src tests`
- `pytest -q` → all pass

## Done when
- [x] Four new tests pass
- [x] `test_real_run_with_stubs_does_not_fail` still passes

## Escalate if
- Pillow can't write EXIF orientation in the test (ask Opus for a fixture approach rather than skipping the test).

## Log

### Attempt 1 (Sonnet worker on pod) - blocked, E-002
```text
$ ruff check src tests
All checks passed!

$ pytest -q
ERROR collecting tests/test_s00_ingest.py
ImportError: cannot import name 'run_job' from 'avatar_forge.core.job'
(/workspace/avatar-forge/src/avatar_forge/core/job.py)
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 1.70s
```
Opus (E-002): card now gives exact imports. Keep the existing s00_ingest.py work;
fix only the imports in tests/test_s00_ingest.py, then run Verify.
```

### Final verification
```text
$ ruff check src tests
All checks passed!

$ pytest -q
....................                                                     [100%]
20 passed in 3.70s
