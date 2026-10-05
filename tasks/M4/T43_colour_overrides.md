# T43 — Colour overrides (hair, skin, eyes, garments)
milestone: M4 · effort: low · depends: T41

> Planning-time draft. **Opus rewrites this card at G3.**

## Goal
`--set hair_color=#a0522d`, `--set garment.jacket_01.color=#202020` change the exported look.

## Do (outline)
1. Extend `overrides.py` with `garment.<id>.color` and `garment.<id>.enabled`.
2. Garment recolour: hue/saturation shift of the base-colour texture toward the
   target, preserving luminance detail; also write `tint` into import_manifest.
3. Hair/skin/eye colours go into body_params → printed for MetaHuman (T44).
4. Tests for parsing and for the recolour function on a small synthetic texture.

## Log
