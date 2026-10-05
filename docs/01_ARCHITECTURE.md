# 01 — Architecture

Owned by the gatekeeper (Opus). Workers must not change this file; escalate instead.

## 1. Shape of the system

A linear pipeline of **stages**. Each stage reads files from a **job folder**,
writes new files into it, and records what it did in `manifest.json`.
Any stage can be re-run on its own, which is what makes body edits cheap:
change a parameter, re-run from s05 onward.

```
inputs (1–4 images)
   │
s00_ingest ─────── create job folder, copy inputs, start manifest
s01_validate ───── full-body / single-person / resolution / occlusion checks, consent flag
s02_prepare ────── background removal, crop, colour normalise, assign views
s03_parse ──────── per-part masks: hair, face, skin, and one mask per garment
s04_body_fit ───── pose + body shape → body measurements (cm) + skin/hair/eye colours
s05_body_params ── apply user overrides + normalise → final body parameters
s06_garments ───── classify each garment, pick strategy, produce raw garment meshes
s07_texture ────── project image colours to UVs, fill unseen areas, PBR maps
s08_assemble ───── Blender headless: body + garments, weight transfer, anti-clipping, LODs
s09_export ─────── FBX + textures + import_manifest.json for UE5
   │
UE5 (Windows PC): unreal/import_character.py
```

## 2. Job folder layout

```
jobs/<job_id>/
  manifest.json                 single source of truth (schema below)
  inputs/front.png  back.png ...
  s01_validate/report.json
  s02_prepare/<view>_rgba.png
  s03_parse/<view>/<part>_mask.png  parts.json
  s04_body_fit/body_fit.json        measurements, colours, pose keypoints
  s05_body_params/body_params.json  final measurements after overrides + normalise
  s06_garments/<garment_id>/raw.glb  garment.json
  s07_texture/<garment_id>/basecolor.png normal.png roughness.png metallic.png
  s08_assemble/character.blend  lod0..lod3 previews
  s09_export/<job_id>/*.fbx  textures/  import_manifest.json
  logs/<stage>.log
```

## 3. Data contracts

- `schemas/character_manifest.schema.json` — the manifest.
- `schemas/garment.schema.json` — one garment entry.
- `schemas/body_params.schema.json` — body measurements and colours.

Body shape is exchanged as **measurements in centimetres** plus colours, not as
the parameters of any one body model. This keeps the pipeline independent of
which body-fitting model we use, and of that model's licence.

## 4. Code layout

```
src/avatar_forge/
  cli.py                 `avatar-forge run|rerun|validate|doctor`
  core/
    config.py            loads config/pipeline.yaml (+ overrides)
    manifest.py          read/write/validate manifest.json
    stage.py             StageContext, StageResult, stage registry
    runner.py            runs stages in order, resumes, re-runs from a stage
    log.py               logging setup
    paths.py             job folder paths
  stages/s00_ingest.py … s09_export.py   one `run(ctx)` each
  models/                lazy wrappers around third-party models
  blender/               scripts executed inside `blender --background --python`
  body/                  measurements, normalise rules, MetaHuman mapping
  garments/              taxonomy, strategy choice, library matching
unreal/import_character.py   runs inside UE5's Python
```

## 5. External tools

| Purpose | Tool | Where it runs |
|---------|------|---------------|
| Mesh ops, weight transfer, FBX export | Blender 4.x headless | pod |
| Pose keypoints | chosen at G1 (see config/models.yaml) | pod GPU |
| Human/garment parsing | chosen at G1 | pod GPU |
| Body measurements | chosen at G1 | pod GPU |
| Image-to-3D for `generated` garments and MVP fused mesh | chosen at G1 | pod GPU |
| Background removal | chosen at G1 | pod GPU |
| Character body, skin, groom, rig | MetaHuman in UE5 | Windows PC |

## 6. Stage contract (do not change)

```python
def run(ctx: StageContext) -> StageResult: ...
```

- Reads only from `ctx.job_dir` and `ctx.config`.
- Writes only under `ctx.stage_dir`.
- Returns `StageResult(status="ok"|"warn"|"fail", outputs=[...], messages=[...])`.
- The runner writes the result into the manifest. Stages never edit the manifest directly.
- A stage must be idempotent: running it twice gives the same outputs.
