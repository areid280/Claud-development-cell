# Task board

Single source of truth. Workers take the **first** `todo` whose dependencies are `done`.

| id | title | milestone | depends | status |
|----|-------|-----------|---------|--------|
| T00 | Install and verify on the pod | M0 | — | done |
| T01 | Blender runner and smoke test | M0 | T00 | done |
| T02 | Stage s00_ingest | M0 | T00 | done |
| T03 | CI and repo hygiene | M0 | T01, T02 | done |
| **G0** | **Gate: environment (Opus)** | M0 | T00–T03 | done (PASS WITH FIXES) |
| T04 | Network volume persistence check | M0 | G0 | done |
| T10 | Model wrapper base and weights fetcher | M1 | G0, T04 | done |
| T11 | Model trial harness | M1 | T10 | done |
| T12 | Trials: pose and background removal | M1 | T11 | done |
| T16 | Re-run ViTPose and BiRefNet (transformers<5) | M1 | T12 | done |
| T13 | Trials: human/garment parsing | M1 | T12, T16 | done |
| T17 | Re-run Florence-2 + SAM after box fix | M1 | T13 | done |
| T14 | Trials: body measurements | M1 | T12 | done |
| T15 | Trials: image-to-3D | M1 | T14 | todo |
| T18 | Trials: mesh-based body measurement | M1 | T14 | todo |
| **G1** | **Gate: model choice and licences (Opus)** | M1 | T10–T18 | todo |
| T20 | Stage s01_validate | M2 | G1 | todo |
| T21 | Stage s02_prepare | M2 | T20 | todo |
| T22 | Stage s03_parse | M2 | T21 | todo |
| T23 | Stage s04_body_fit | M2 | T22 | todo |
| T24 | Stage s05_body_params (overrides) | M2 | T23 | todo |
| T25 | Stage s06_garments (MVP fused mesh) | M2 | T24 | todo |
| T26 | Stage s09_export + UE5 import script | M2 | T25 | todo |
| T27 | End-to-end MVP run and evidence pack | M2 | T26 | todo |
| **G2** | **Gate: MVP go / no-go (Opus)** | M2 | T20–T27 | todo |
| T30 | Garment taxonomy and classification | M3 | G2 | todo |
| T31 | Garment library loader and matcher | M3 | T30 | todo |
| T32 | Body base mesh shaped to measurements | M3 | G2 | todo |
| T33 | Strategy: skin_layer | M3 | T32 | todo |
| T34 | Strategy: template fitting | M3 | T31, T32 | todo |
| T35 | Strategy: generated garments | M3 | T30 | todo |
| T36 | Texture projection and PBR maps | M3 | T33, T34, T35 | todo |
| T37 | Assemble: skinning, anti-clipping, walk test | M3 | T36 | todo |
| T38 | Per-garment export + UE5 import update | M3 | T37 | todo |
| **G3** | **Gate: garment separation (Opus)** | M3 | T30–T38 | todo |
| T40 | Normalise proportions | M4 | G3 | todo |
| T41 | Re-run with overrides (integration) | M4 | T40 | todo |
| T42 | Garment refit after body edits | M4 | T41 | todo |
| T43 | Colour overrides (hair, skin, eyes, garments) | M4 | T41 | todo |
| T44 | MetaHuman parameter mapping | M4 | T41 | todo |
| T45 | LODs | M4 | T42 | todo |
| **G4** | **Gate: body editing and refit (Opus)** | M4 | T40–T45 | todo |
| T50 | Multi-view input | M5 | G4 | todo |
| T51 | Multi-view texture fusion | M5 | T50 | todo |
| T52 | Simple UI (four screens) | M5 | T50 | todo |
| T53 | Third-party notices and docs | M5 | T52 | todo |
| T54 | Fresh-install test | M5 | T53 | todo |
| **G5** | **Gate: release (Opus)** | M5 | T50–T54 | todo |
