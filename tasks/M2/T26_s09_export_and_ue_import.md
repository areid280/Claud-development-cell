# T26 — Stage s09_export + UE5 import script
milestone: M2 · effort: medium · depends: T25
owner input: run the UE5 script on your PC and paste the Output Log (card stays `waiting-owner` until then)

## Goal
An export folder UE5 can import with one script.

## Read first
- src/avatar_forge/stages/s09_export.py (contract)
- schemas/import_manifest.schema.json
- docs/03_UE5_INTEGRATION.md
- unreal/import_character.py

## Contracts (Opus, 2026-10-09, D-015)
- **Fused MVP mesh has vertex colours and no textures.** `export_fbx.py` exports vertex colours
  (`colors_type="SRGB"` in Blender 4.2's FBX exporter); `--tex-dir` stays empty for it.
- **import_manifest.json:** one mesh `{"id": "character_fused", "kind": "fused", "path": "fused/character_fused.fbx"}`
  with **no `material` object** (the schema allows that). Validate against `schemas/import_manifest.schema.json`.
- **UE script:** besides `M_AF_Garment`, create `/Game/AvatarForge/M_AF_VertexColor` if missing
  (a `VertexColor` node → Base Color; Roughness constant 0.6). Use it for any mesh whose manifest entry has
  no `material.basecolor`. Import the FBX with vertex colours set to **Replace** (`FbxStaticMeshImportData.vertex_color_import_option`).

## Do
1. Blender script `src/avatar_forge/blender/export_fbx.py` (args `--in --out-fbx --tex-dir`):
   import GLB, unpack/save its images as PNG into `--tex-dir`
   (`<id>_basecolor.png` etc. — name by which socket of the Principled BSDF
   they feed), export FBX: `apply_scale_options='FBX_SCALE_ALL'`,
   `axis_forward='-Y'`, `axis_up='Z'`, `path_mode='STRIP'`, no embedded textures.
2. `run(ctx)` (MVP): export `s06_garments/fused/character_fused.glb` →
   `s09_export/<job_id>/fused/character_fused.fbx` + textures; copy
   `body_params.json` to `body/`; copy previews to `previews/`; write
   `import_manifest.json` (validate against the schema; one mesh, `kind: fused`).
3. Implement `unreal/import_character.py` (UE Python API only):
   - Get the manifest path from env `AF_IMPORT_MANIFEST` or an
     `unreal.EditorDialog`/file prompt fallback.
   - Ensure parent material `/Game/AvatarForge/M_AF_Garment` exists; if not, create
     it with `MaterialEditingLibrary`: TextureSampleParameter2D nodes
     `BaseColor`, `Normal` (sampler type normal), `Roughness`, `Metallic`
     connected to the matching material properties.
   - Import textures and FBX with `AssetImportTask` into `/Game/AvatarForge/<job_id>/`
     (static mesh for `fused`, skeletal later). Create one
     `MaterialInstanceConstant` per mesh, set texture parameters, assign it.
   - `unreal.log` the body measurements.
4. Ask the owner to run it (docs/03_UE5_INTEGRATION.md §2) and paste the Output
   Log and a screenshot path. Fix only errors visible in that log.

## Verify
- Export folder validates · owner's UE log shows the import without errors.

## Log
