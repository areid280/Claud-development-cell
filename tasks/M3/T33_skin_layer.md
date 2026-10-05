# T33 — Strategy: skin_layer
milestone: M3 · effort: medium · depends: T32

> Planning-time draft. **Opus rewrites this card at G2.**

## Goal
Tight garments (bodysuit, leggings, stockings, tight tops) as body-surface layers.

## Do (outline)
1. Project each skin_layer garment's front mask onto the shaped body (camera
   matched to the s02 crop and keypoints) → set of body faces covered.
2. Grow/smooth the selection (no jagged edges), use neckline/cuff edges from the mask outline.
3. Duplicate those faces, offset outward by `skin_layer_offset_mm`, keep body UVs
   and skin weights. Save `s06_garments/<id>/raw.glb`, set `mesh` in garment.json.
4. Back side: same region mirrored front→back unless a back view exists (M5).

## Verify
- Render previews; seam gaps visible? Paste paths in Log.

## Log
