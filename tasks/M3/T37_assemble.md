# T37 — Assemble: skinning, anti-clipping, walk test
milestone: M3 · effort: medium · depends: T36

> Planning-time draft. **Opus rewrites this card at G2.**

## Goal
One Blender file with the body and every garment skinned to the body skeleton.

## Do (outline)
1. Blender `assemble.py`: import body + garments + textures; materials per garment.
2. Weight transfer body→garment (Data Transfer modifier, nearest face interpolated),
   then smooth weights; rigid items (buckles, jewellery) parented to one bone.
3. Layer order: inner layers pushed in slightly where outer layers overlap.
4. Walk test: apply a short bundled walk cycle (owner provides or a simple
   procedural one), render 4 frames; measure max penetration per garment.
5. Save `s08_assemble/character.blend` + previews.

## Log
