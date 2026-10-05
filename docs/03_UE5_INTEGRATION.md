# 03 — UE5 integration

Target: Unreal Engine 5.6 or newer (MetaHuman Creator is built into the
engine from 5.6). Record the exact version you use in `docs/05_DECISIONS.md`.

## 1. What the pipeline hands to UE5

`jobs/<job_id>/s09_export/<job_id>/`:

```
import_manifest.json     what to import, materials, body parameters
body/body_params.json    measurements (cm) + skin, hair, eye colours
garments/<id>.fbx        one skeletal mesh per garment
garments/textures/<id>_basecolor.png  _normal.png  _roughness.png  _metallic.png
previews/front.png back.png
```

M2 (MVP) also includes `fused/character_fused.fbx`, a single combined mesh
used to prove the pipeline works.

## 2. Import steps (owner, on Windows)

1. Enable plugins: **MetaHuman**, **Python Editor Script Plugin**.
2. Copy `unreal/` from this repo into your UE project as `Content/Python/avatar_forge/`.
3. In the UE editor: **Tools → Execute Python Script** →
   `Content/Python/avatar_forge/import_character.py`, and choose the job's
   `import_manifest.json` when prompted.
4. The script imports garments into `/Game/AvatarForge/<job_id>/`, creates
   material instances from `M_AF_Garment` and prints the body parameters.
5. In MetaHuman Creator, create a MetaHuman and set body parameters to the
   printed values. (M4 aims to automate as much of this as the UE version allows.)
6. Attach garments to the MetaHuman body skeleton.

## 3. Open questions for G1/G4 (Opus to resolve and record)

- Which MetaHuman body parameters can be set from Python in the installed UE
  version, and which must be set by hand.
- Whether garments should be skinned to the MetaHuman body skeleton in
  Blender (preferred) or retargeted in UE.
- How MetaHuman's own outfit/clothing fitting can be used so garments refit
  when body sliders change in UE.
- MetaHuman licence terms for the intended use (check Epic's current EULA).
