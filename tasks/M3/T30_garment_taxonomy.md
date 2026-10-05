# T30 — Garment taxonomy and classification
milestone: M3 · effort: medium · depends: G2

> Planning-time draft. **Opus rewrites this card at G2** with exact details.

## Goal
Turn `s03_parse/parts.json` into a list of garments, each with category,
strategy, layer and material guess — the "review what was found" list.

## Read first
- schemas/garment.schema.json · config/pipeline.yaml → `stages.s06_garments`
- src/avatar_forge/stages/s06_garments.py

## Do (outline)
1. `src/avatar_forge/garments/taxonomy.py`: map canonical parse labels → garment
   categories (e.g. `boots` → boots, `upper_clothes` → top unless the parse also
   finds `bodysuit`), split left/right instances into one garment.
2. Tightness test for tops/bottoms: ratio of garment-mask width to body
   silhouette width at the same rows; ≤ `tight_ratio` (new config, 1.04) → `skin_layer`.
3. Material guess from the masked pixels: specular highlight ratio, saturation,
   texture variance → `fabric|leather|latex|knit|metal|other` with simple
   thresholds in config. Colour = median.
4. Layer order defaults per category (skin_layer 0–1, jackets 3, belts 4).
5. `mode: separate` in s06 writes `s06_garments/<id>/garment.json` for every item
   (mesh `null` for now). Respect `overrides.disabled_garments`.
6. Unit tests with synthetic masks.

## Verify
- garment.json files validate; manifest `garments` populated (runner sync); list them in Log for each sample.

## Log
