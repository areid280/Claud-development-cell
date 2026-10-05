# T42 — Garment refit after body edits
milestone: M4 · effort: medium · depends: T41

> Planning-time draft. **Opus rewrites this card at G3.**

## Goal
After a body edit, every garment follows the new shape without clipping or stretching textures.

## Do (outline)
1. skin_layer garments: regenerate from the new body (same face selection, stored in garment data).
2. template/generated garments: deform with the same base→shaped body deformation as T34; re-run the anti-clip pass.
3. Texture stays on UVs (no re-projection unless the user asks).
4. Report max penetration before/after in stage data; warn above 3 mm.

## Log
