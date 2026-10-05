# 00 — Project brief

## 1. Goal

Turn 1–4 full-body images of an attractive **adult** character into a
beautiful, rigged, game-ready UE5 character that can be used as a main
character or NPC, with:

1. Body, face, skin and hair matching the image as closely as practical.
2. Every clothing item as its own mesh with its own textures, so items can be
   swapped, recoloured, hidden or replaced in UE5.
3. Editable body features (height, bust, waist, hips, shoulders, leg length,
   hair colour, skin tone) and a **normalise** step that pulls unusual
   proportions back into a configurable plausible range.
4. Clothing that refits automatically after body edits.
5. Clean FBX + PBR texture export that imports into UE5 with one script.

## 2. Quality bar

"Beautiful and detailed" means, at minimum:

- No holes, spikes, inverted normals or floating fragments on any mesh.
- Body uses a professional base (MetaHuman-compatible), not a raw scan blob.
- Garments sit on the body without visible clipping in the A-pose and in a
  basic walk animation.
- Textures 2K minimum (4K for body and main garment), with base colour,
  normal, roughness and (where relevant) metallic maps.
- The front view in UE5 is recognisably the same outfit and colouring as the input.

Gates G2–G4 test this bar. The gatekeeper judges it from screenshots.

## 3. Scope decisions (already made)

- **MetaHuman-first.** The body is a MetaHuman-compatible body driven by
  measured parameters, not a mesh generated from scratch. This gives rigging,
  skin shading and body sliders for free.
- **Garment strategy per item:**
  - `skin_layer` — tight items (bodysuits, leggings, stockings, tight tops):
    the body surface itself, offset slightly, with its own texture.
  - `template` — common items (jackets, boots, gloves, belts, skirts, hats):
    nearest match from `assets/garment_library/`, fitted to the body,
    re-textured from the image.
  - `generated` — unusual items: image-to-3D on the masked crop, then cleaned up.
- **Development hardware:** rented NVIDIA GPU (RunPod RTX 4090). The owner's
  AMD 7900 XT is used later only if the chosen models have working AMD ports.
- **UE5 runs on the owner's Windows PC.** The pipeline produces files; UE5 imports them.
- **Style:** the pipeline targets realistic and semi-realistic characters.
  Painted artwork is accepted as input but treated mainly as a colour and
  design reference.

## 4. Input rules (enforced by stage s01_validate)

- Full body, head to toe, feet visible.
- One person per image.
- Long side at least 1024 px.
- Recommended: A-pose (arms slightly away from body), plain background, even lighting.
- Multi-view (M5): front required; back, left, right optional.
- Crossed arms, cropped feet or heavy occlusion → warning or rejection with a
  clear reason (thresholds in `config/pipeline.yaml`).

## 5. Content and consent rules

- Subjects must be adults. Inputs must be original characters, or real people
  who have consented to being turned into a 3D character.
- The CLI and UI require the user to confirm both points before a job runs
  (`--confirm-adult-consent` flag / checkbox). Jobs record this in the manifest.
- No feature may be designed to strip clothing from a real person's likeness.
  Body edits and clothing swaps operate on the 3D character.
- Characters from existing franchises are fine for private testing but must
  not ship in a released game without rights.

## 6. Non-goals (for now)

- Training new neural networks.
- Hair strand simulation beyond MetaHuman/groom presets.
- Facial animation capture.
- Real-time in-game generation.

## 7. Milestones

| Milestone | Result | Gate |
|-----------|--------|------|
| M0 | Rented GPU working, repo set up, CI green | G0 |
| M1 | Candidate models run in isolation; licences approved | G1 |
| M2 | End-to-end MVP: image → measurements + fused mesh → FBX → UE5 | G2 |
| M3 | Separate garments with textures, assembled on body | G3 |
| M4 | Body editing, normalise, garment refit, MetaHuman mapping, LODs | G4 |
| M5 | Multi-image input, simple UI, packaged release | G5 |

Each gate can stop the project. That is deliberate: it protects the budget.
