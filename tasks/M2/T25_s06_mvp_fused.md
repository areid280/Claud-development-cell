# T25 — Stage s06_garments, MVP fused mesh
milestone: M2 · effort: medium · depends: T24

> **G1 (Opus, 2026-10-09, D-014):** image_to_3d = **trellis**, wrapper `src/avatar_forge/models/i23d_trellis.py`,
> class `Trellis`, `predict(image_rgba, out_dir, seed=0, output_name="full.glb") -> Path` (glTF Y-up GLB with
> vertex colours, E-018). Install per the T15 card "Opus notes" (/opt/src/TRELLIS, kaolin 0.17.0 wheel, xformers,
> spconv; nvdiffrast only if the import fails without it). Fallback: triposr (`i23d_triposr.py`).
> nvdiffrast (research/evaluation licence) may be loaded; the owner confirmed the project is in scope (D-014 addendum).
> Triangle budget for the MVP mesh: decimate to ≤ 150k triangles before export (Blender Decimate, ratio
> from the face count).

## Goal
A clean, correctly scaled single mesh of the whole character, as proof the 3D path works.

## Read first
- src/avatar_forge/stages/s06_garments.py (contract)
- src/avatar_forge/blender_runner.py
- src/avatar_forge/blender/render_previews.py
- the selected image_to_3d wrapper

## Do
1. Add config key `stages.s06_garments.mvp_max_triangles: 200000`.
2. When `mode == "mvp_fused"`: run the selected model on
   `s02_prepare/front_rgba.png` → `s06_garments/fused/raw.glb`.
3. Blender script `src/avatar_forge/blender/cleanup_mesh.py`
   (args: `--in --out --height-m --max-tris`):
   - import GLB; join all mesh objects; merge by distance (0.0005 m);
   - delete loose parts with fewer than 1% of total vertices;
   - recalculate normals outside;
   - decimate (collapse) if triangles > `--max-tris`;
   - scale uniformly so the bounding-box height = `--height-m`; move so the
     lowest point is at z = 0 and centred on x/y = 0; face −Y (Blender front);
   - keep the material and texture; export GLB with textures embedded to `--out`.
   Call it with `--in s06_garments/fused/raw.glb --out s06_garments/fused/character_fused.glb`.
4. Height comes from `s05_body_params/body_params.json` (`height` cm / 100).
5. Render previews (front/back) with render_previews.py into `s06_garments/fused/`.
6. Return outputs + data `{triangles, watertight}` (trimesh on the result).
7. When `mode == "separate"` return `StageResult.not_implemented("T30")`.

## Verify
- run full pipeline `--to s06_garments` on all samples; paste triangle counts;
  describe the previews honestly (holes? spikes? texture blur?).

## Escalate if
- The model output is consistently unusable (Opus decides whether to change model).

## Log
