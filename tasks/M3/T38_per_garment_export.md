# T38 — Per-garment export + UE5 import update
milestone: M3 · effort: medium · depends: T37
owner input: run the updated UE script and send screenshots with garments toggled on/off

> Planning-time draft. **Opus rewrites this card at G2.**

## Goal
One skeletal-mesh FBX per garment (and the body) that UE5 imports and attaches.

## Do (outline)
1. Export body + each garment as separate skeletal FBX sharing the skeleton.
2. import_manifest.json with `kind: body|garment`, `skeletal: true`, layer, category.
3. UE script: import skeletal meshes against one skeleton; create material
   instances; build a simple Blueprint actor with one SkeletalMeshComponent per
   garment following the body (leader pose) so items can be toggled.
4. End-to-end run on all samples → `gates/reports/G3_evidence.md`. Tell the human G3 is due.

GATE: G3

## Log
