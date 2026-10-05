# T21 — Stage s02_prepare
milestone: M2 · effort: low · depends: T20

> Opus refines this card at G1 (selected bg_remove model).

## Goal
Person cut out on transparent background, cropped and resized consistently.

## Read first
- src/avatar_forge/stages/s02_prepare.py (contract)
- config/pipeline.yaml → `stages.s02_prepare`
- the selected bg_remove wrapper

## Do
1. `src/avatar_forge/stages/crop_math.py`:
   `crop_box(alpha_bbox, kp_bbox, image_size, margin_frac) -> (x0, y0, x1, y1)` —
   union of both boxes, expanded by `margin_frac × box height` on every side,
   clamped to the image. Unit tests for clamping and union.
2. `run(ctx)`: per view: load `s00_ingest/<view>.png` and
   `s01_validate/<view>_keypoints.json`; cut-out via selected bg_remove model;
   crop; resize so the long side = `output_long_side_px` (LANCZOS);
   write `<view>_rgba.png` and `<view>_crop.json`
   (`{"box": [...], "scale": float}` so later stages can map coordinates back).
   Also write `<view>_keypoints.json` transformed into the new image's coordinates.
3. Tests: crop_math unit tests; a GPU test on `samples/a_front.png` checks the
   output has alpha with > 10% opaque pixels and long side = 2048.

## Verify
- `pytest -q` · run to `--to s02_prepare` on a sample; open `<view>_rgba.png` and describe it in Log.

## Log
