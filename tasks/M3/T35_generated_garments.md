# T35 — Strategy: generated garments
milestone: M3 · effort: medium · depends: T30

> Planning-time draft. **Opus rewrites this card at G2.**

## Goal
Unusual items (collars, harnesses, jewellery) from the image-to-3D model.

## Do (outline)
1. Masked crop (as in T15) → selected image_to_3d model → raw GLB.
2. Cleanup (reuse cleanup_mesh.py) with `generated_max_triangles`.
3. Place on the body: scale from the mask's size in cm (cm_per_px from s04),
   position from the mask centroid projected onto the body surface; snap to
   the nearest body region (neck, waist, wrist).
4. Save `raw.glb`, update garment.json.

## Log
