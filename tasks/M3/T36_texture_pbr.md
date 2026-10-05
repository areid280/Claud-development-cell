# T36 — Texture projection and PBR maps
milestone: M3 · effort: medium · depends: T33, T34, T35

> Planning-time draft. **Opus rewrites this card at G2.**

## Goal
Each garment gets base colour, normal, roughness and metallic maps that match the image.

## Do (outline)
1. Blender bake: project `s02_prepare/front_rgba.png` from the matched camera onto
   each garment's UVs (only where the garment mask is visible and the surface faces the camera).
2. Fill unseen texels per `unseen_fill`: mirror front→back for symmetric items,
   then inpaint remaining holes (OpenCV Telea) and, for patterned fabric,
   tile a sample patch.
3. Normal map from a high-pass of luminance (strength by material type);
   roughness/metallic from the material guess in garment.json.
4. Resolutions from config. Write into `s07_texture/<id>/`.

## Log
