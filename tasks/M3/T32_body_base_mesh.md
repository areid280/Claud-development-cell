# T32 — Body base mesh shaped to measurements
milestone: M3 · effort: medium · depends: G2
owner input: likely — export MetaHuman body/bodies from UE5 as FBX (Opus will say exactly which at G2)

> **Opus decides the method at G2 and rewrites this card.** Options considered:
> (a) owner exports several MetaHuman bodies spanning the shape range; the
> pipeline blends them (shape keys) to hit the measurements;
> (b) a licence-clean parametric body in Blender, matched to MetaHuman proportions;
> (c) measurements only, garments fitted in UE5 (weakest).

## Goal
A rigged body mesh on the pod whose shape matches `body_params.json` and the
MetaHuman body in UE5, so garments fitted here also fit there.

## Do (outline, pending G2)
1. `src/avatar_forge/blender/shape_body.py`: load base(s), solve blend weights
   to minimise measurement error (measure with the same slicing as `mesh_measure.py`),
   keep the skeleton, export `s08_assemble/body.glb`.
2. Tests: measured error ≤ 2 cm per key on three synthetic targets.

## Log
