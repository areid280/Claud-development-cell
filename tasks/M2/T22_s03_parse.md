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

## Do
1. `run(ctx)`: per view: run the selected parsing model on `s02_prepare/<view>_rgba.png`.
   Zero every mask outside the alpha channel. Drop masks smaller than
   `min_part_area_px`. Save `s03_parse/<view>/<label>_mask.png` (8-bit, 0/255).
2. Connected components: if one label has several separate blobs of similar
   size (e.g. two boots, two gloves) keep them in one mask but record
   `"instances": n` in parts.json.
3. `parts.json`: list of `{label, view, mask, area_px, bbox, instances}`.
   Also write `labels_preview.png` (colour-coded, same colours as the T13 trial).
4. Tests: a pure helper `postprocess_masks(masks, alpha, min_area)` tested
   with synthetic arrays (outside-alpha removal, small-mask removal, instance count).

## Verify
- `pytest -q` · run `--to s03_parse` on two samples, list parts.json labels in Log.

## Log
