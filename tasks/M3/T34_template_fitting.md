# T34 — Strategy: template fitting
milestone: M3 · effort: medium · depends: T31, T32

> Planning-time draft. **Opus rewrites this card at G2.**

## Goal
Fit each chosen library garment onto the shaped body without clipping.

## Do (outline)
1. Blender script `fit_template.py`: import the template (fitted to the base body),
   transfer the base→shaped body deformation with a Surface Deform / Mesh Deform
   modifier bound on the base body, then apply.
2. Length/extent adjustments from the image (e.g. boot top height, skirt hem)
   via simple lattice scaling along the limb axis.
3. Anti-clip pass: shrinkwrap "outside" with `anti_clip_offset_mm` limited to
   vertices inside the body.
4. Save `raw.glb`; record fit stats (max penetration depth) in garment.json data.

## Log
