# T31 — Garment library loader and matcher
milestone: M3 · effort: low · depends: T30
owner input: the starter garment library (assets/garment_library/README.md) uploaded to the pod, with index.yaml

> Planning-time draft. **Opus rewrites this card at G2.**

## Goal
For each `template` garment, choose the best library item.

## Do (outline)
1. `src/avatar_forge/garments/library.py`: load and validate `index.yaml`
   (ids unique, files exist, licence file present); `items_for(category)`.
2. Matcher: filter by category, then rank by tag overlap with features from the
   image (length: knee/ankle/thigh via mask extent relative to keypoints;
   sleeve length; heel present via foot keypoints), tie-break by preview
   similarity if a preview exists (simple colour-agnostic edge histogram).
3. Write `template_id` into each garment.json; no match → strategy `generated`
   with a warning.
4. A `scripts/sync_garment_library.sh` the owner fills in (rclone/scp from their storage).

## Verify
- Unit tests with a tiny fake library (2 boots, 1 jacket).

## Log
