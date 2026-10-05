# Garment library

Base meshes for the `template` garment strategy (docs/05_DECISIONS.md D-003).
**This library is the biggest single factor in how good the output looks.**

The files are not committed to git (licences vary). Each machine syncs them
from the owner's storage into `assets/garment_library/` (see T31).

## What the owner needs to provide (input to task T31)

Start with 10–15 items. Good starter set for the target characters:

| id | category | notes |
|----|----------|-------|
| jacket_cropped_01 | jacket | cropped/bolero, long sleeves |
| jacket_biker_01 | jacket | |
| boots_knee_01 | boots | knee-high, flat or low heel |
| boots_knee_heel_01 | boots | knee-high, heeled |
| boots_ankle_01 | boots | |
| shoes_heels_01 | shoes | |
| gloves_long_01 | gloves | over-elbow |
| gloves_short_01 | gloves | wrist |
| belt_01 | belt | |
| skirt_mini_01 | skirt | |
| skirt_pleated_01 | skirt | |
| dress_bodycon_01 | dress | |
| hat_beanie_01 | hat | |
| shorts_01 | shorts | |

Requirements for each item:

- FBX or GLB, **quad-dominant**, clean UVs, under ~30k triangles.
- Modelled for a **MetaHuman-proportioned body in A-pose** (ideally made for
  MetaHuman, or fitted to the body in `assets/body_base/`).
- Neutral grey or white base colour (the pipeline re-textures it).
- Licence that allows your intended use (personal or commercial). Keep the
  licence text next to the file.

Where to get them: buy on Fab (filter for MetaHuman-compatible clothing),
make them in Marvelous Designer / CLO, or model them in Blender.

## Layout

```
assets/garment_library/
  index.yaml          copy index.example.yaml and fill it in
  <id>/mesh.fbx
  <id>/LICENSE.txt
  <id>/preview.png    optional, used by the matcher and UI
```
