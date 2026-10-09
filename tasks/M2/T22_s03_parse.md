# T22 — Stage s03_parse
milestone: M2 · effort: low · depends: T21

> **G1 (Opus, 2026-10-09, D-012):** parsing = **segformer-clothes** (single model, no combining in M2), wrapper
> `src/avatar_forge/models/parsing_segformer_clothes.py`, class `SegformerClothes`,
> `predict(image: PIL.Image) -> dict[str, np.ndarray]` (canonical label -> bool mask). Fallback: sapiens-seg.
> Licence approved by Opus 2026-10-09 (personal use / non-profit, D-008); `selected_model("parsing")` returns it.

## Goal
Canonical part masks per view, ready for body fitting and (later) garment separation.

## Read first
- src/avatar_forge/stages/s03_parse.py (contract)
- config/pipeline.yaml → `stages.s03_parse`
- the selected parsing wrapper

## Contracts (Opus, E-021 — follow `s02_prepare.py` as the pattern)
- **StageContext / views / result:** exactly as in the T21 card's Contracts (`ctx.job_dir`, `ctx.stage_dir`,
  `ctx.stage_config()` = `stages.s03_parse`, views from `ctx.manifest["inputs"]`).
- **Model:** `from avatar_forge.models.registry import load_selected`;
  `with load_selected("parsing") as model:` (load once), then per view
  `image = Image.open(job_dir/"s02_prepare"/f"{view}_rgba.png")`; `masks = model.predict(image)` →
  `dict[str, np.ndarray]`, canonical label → bool array of shape `(H, W)` = the s02 image size.
- **Alpha:** `alpha = np.asarray(image.getchannel("A")) > 0`.
- **Labels:** only labels in `cfg["labels"]`; anything else → `"accessory"`. Never write a `"background"` part.
- **Helper** `postprocess_masks(masks, alpha, min_area) -> dict[str, tuple[np.ndarray, int]]` in
  `src/avatar_forge/stages/parse_post.py`: `mask & alpha`; drop masks with fewer than `min_area` pixels;
  instances = number of connected components (`scipy.ndimage.label`, 8-connectivity) whose area is
  ≥ 25 % of the largest component of that label (so specks do not count). Returns `(mask, instances)`.
- **Outputs:** `s03_parse/<view>/<label>_mask.png` (mode "L", 0/255) and `s03_parse/<view>/labels_preview.png`
  (RGB, black background, colours from `avatar_forge.parts.LABEL_COLORS`, painted in `cfg["labels"]` order).
  `s03_parse/parts.json` = list of `{"label", "view", "mask": <path relative to job_dir>, "area_px": int,
  "bbox": [x0, y0, x1, y1] (s02 image pixels, from the mask), "instances": int}`.
- **Result:** `StageResult(status="ok", outputs=[...], data={"views": {view: [labels...]}})`; if a view has no
  parts at all, return `status="fail"` with `f"{view}: no body parts found"`.

## Do
1. `run(ctx)`: per view: run the selected parsing model on `s02_prepare/<view>_rgba.png`.
   Zero every mask outside the alpha channel. Drop masks smaller than
   `min_part_area_px`. Save `s03_parse/<view>/<label>_mask.png` (8-bit, 0/255).
2. Connected components: if one label has several separate blobs of similar
   size (e.g. two boots, two gloves) keep them in one mask but record
   `"instances": n` in parts.json.
3. `parts.json`: list of `{label, view, mask, area_px, bbox, instances}`.
   Also write `labels_preview.png` (see Contracts for colours).
4. Tests: a pure helper `postprocess_masks(masks, alpha, min_area)` tested
   with synthetic arrays (outside-alpha removal, small-mask removal, instance count).

## Verify
- `pytest -q` · run `--to s03_parse` on two samples, list parts.json labels in Log.

## Log

- `source ~/.avatar_forge_env && ruff check src tests` → `All checks passed!`
- `source ~/.avatar_forge_env && pytest -q` → `80 passed, 3 warnings in 44.96s`.
- `pytest -q tests/test_s03_parse.py` → `1 passed in 2.09s`.
- `avatar-forge run samples/a_front.png --confirm-adult-consent --to s03_parse` → `s00_ingest ok`, `s01_validate ok`, `s02_prepare ok`, `s03_parse ok`; job `/workspace/jobs/20261009-212621-2658e9`. `parts.json` labels: `hair, face, skin, upper_clothes, lower_clothes, shoes`.
- `avatar-forge run samples/b_front.png --confirm-adult-consent --to s03_parse` → `s00_ingest ok`, `s01_validate ok`, `s02_prepare ok`, `s03_parse ok`; job `/workspace/jobs/20261009-212657-7bf227`. `parts.json` labels: `hair, face, skin, dress, belt, shoes`.
- Initial sample attempt found zero-byte cached SegFormer config, processor config, and weights. Removed those exact corrupt cache entries; subsequent sample runs downloaded/loaded the model and passed. No model assets were added to the repository.
