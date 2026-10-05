# T51 — Multi-view texture fusion
milestone: M5 · effort: medium · depends: T50

> Planning-time draft. **Opus rewrites this card at G4.**

## Goal
Real back textures from the back view; seamless blending between views.

## Do (outline)
1. Project every view; per texel weight by view-angle cosine and mask confidence.
2. Blend with feathered seams (multi-band blending if seams are visible).
3. Fallback to T36 fill only where no view saw the surface.
4. Before/after previews for single vs multi-view in stage data.

## Log
