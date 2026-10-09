# T21 — Stage s02_prepare
milestone: M2 · effort: low · depends: T20

> **G1 (Opus, 2026-10-09, D-011):** bg_remove = **birefnet**, wrapper `src/avatar_forge/models/bg_remove_birefnet.py`,
> class `BiRefNet`, `predict(image: PIL.Image) -> PIL.Image` (RGBA). Entry via `selected_model("bg_remove")`.
> Needs `timm einops kornia` (in the `trials` extra) and `HF_MODULES_CACHE` on local disk (setup does this).

## Goal
Person cut out on transparent background, cropped and resized consistently.

## Read first
- src/avatar_forge/stages/s02_prepare.py (contract)
- config/pipeline.yaml → `stages.s02_prepare`
- the selected bg_remove wrapper

## Contracts (Opus, E-019 — everything you need; follow `s01_validate.py` as the pattern)
- **StageContext** (`core/stage.py`): `ctx.job_dir`, `ctx.stage_dir` (= `job_dir/"s02_prepare"`, create it),
  `ctx.stage_config()` (= `stages.s02_prepare`), `ctx.config` (full pipeline config), `ctx.manifest`, `ctx.logger`.
- **Views:** `for item in ctx.manifest["inputs"]: view = str(item["view"])` — same as s01.
- **Model:** `from avatar_forge.models.registry import load_selected`;
  `with load_selected("bg_remove") as model: rgba = model.predict(image)` — load once, loop views inside.
- **Input keypoints** `s01_validate/<view>_keypoints.json` = JSON list of persons (possibly empty):
  `[{"bbox": [x0, y0, x1, y1], "score": float, "keypoints": {"nose": [x, y, score], ...}}]`, original pixels.
- **kp_bbox:** `bbox` of the highest-`score` person with score ≥ `ctx.config["stages"]["s01_validate"]["keypoint_min_score"]`;
  if none, use the alpha bbox alone.
- **alpha_bbox:** `rgba.getchannel("A").getbbox()`; if `None` → return
  `StageResult(status="fail", messages=[f"{view}: nothing left after background removal"])`.
- **Coordinates:** crop box `(x0, y0, x1, y1)` in original pixels (ints); `scale = output_long_side_px / max(crop w, h)`.
  Point transform: `x' = (x - x0) * scale`, `y' = (y - y0) * scale` (keypoints and bbox; scores unchanged).
- **Outputs per view:** `<view>_rgba.png`, `<view>_crop.json` = `{"box": [x0, y0, x1, y1], "scale": s, "size": [w, h]}`,
  `<view>_keypoints.json` (same shape as input, transformed).
- **Result:** `StageResult(status="ok", outputs=[paths relative to job_dir], data={"views": {view: {"box": [...], "scale": s}}})`.

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
