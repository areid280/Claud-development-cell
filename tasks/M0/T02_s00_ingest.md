# T02 — Stage s00_ingest
milestone: M0 · effort: low · depends: T00
owner input: none

## Goal
Normalise input images (orientation, colour mode, size) and record metadata.

## Read first
- src/avatar_forge/stages/s00_ingest.py (docstring = contract)
- src/avatar_forge/core/stage.py
- config/pipeline.yaml → `stages.s00_ingest`

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
   from conftest and `create_job` + `run_job(..., to_stage="s00_ingest")`):
   - JPEG with EXIF orientation 6 (rotate 90°) of size 1000×600 → output is 600×1000.
     Make it with: `img = Image.new("RGB", (1000, 600)); exif = img.getexif();
     exif[0x0112] = 6; img.save(path, exif=exif)`.
   - 5000×3000 image → long side equals `max_long_side_px`, `downscaled: True`.
   - PNG with alpha → output mode `RGBA`.
   - Corrupt file (write b"not an image" to `x.jpg`) → `StageFailedError` raised by run_job.

## Must not
- Change the stage signature or edit the manifest from the stage.

## Verify
- `ruff check src tests`
- `pytest -q` → all pass

## Done when
- [ ] Four new tests pass
- [ ] `test_real_run_with_stubs_does_not_fail` still passes

## Escalate if
- Pillow can't write EXIF orientation in the test (ask Opus for a fixture approach rather than skipping the test).

## Log
