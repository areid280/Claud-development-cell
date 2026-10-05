# T45 — LODs
milestone: M4 · effort: low · depends: T42

> Planning-time draft. **Opus rewrites this card at G3.**

## Goal
LOD0–LOD3 per garment using `lod_triangle_ratios`, imported into UE as mesh LODs.

## Do (outline)
1. Blender: decimate copies per ratio (keep UV seams and silhouette; protect
   boundary edges), export as LOD groups in the FBX (`LOD0..LOD3` naming).
2. import_manifest `lods` list; UE script enables "Import Mesh LODs".
3. Evidence: triangle counts per LOD per garment → `gates/reports/G4_evidence.md`.
   Tell the human G4 is due.

GATE: G4

## Log
