# T15 — Trials: image-to-3D
milestone: M1 · effort: medium · depends: T14 (uses its render_previews.py)
owner input: none

## Goal
Textured 3D outputs from each `image_to_3d` candidate on (a) the whole figure and
(b) one masked garment crop, so Opus can judge quality at G1.

## Read first
- config/models.yaml → role `image_to_3d` (read every `licence_note`)
- src/avatar_forge/blender/render_previews.py (from T14)
- docs/INSTALL_LOG.md

## Do
1. **Before installing `hunyuan3d-2`**: its licence note mentions territory
   exclusions and the owner is in the UK. Do not install it. Write an
   escalation (E-entry) asking Opus to check the licence first, mark it
   "skipped pending licence" in Log, and continue with the others.
2. For each remaining candidate: install following its README (use its own
   setup script where provided; record commands in docs/INSTALL_LOG.md).
   Wrapper `src/avatar_forge/models/i23d_<shortname>.py`:
   `predict(image_rgba: PIL.Image, seed: int = 0) -> Path` writing a GLB into a given out dir.
3. Trial adapter `trial_adapters_i23d.py`: for each sample, run on
   - the full cut-out (`cutout.png` from the best T12 bg_remove trial), and
   - one garment crop: take the `boots` or `jacket` mask from the best T13 trial,
     crop the cut-out to the mask bbox +10%, set pixels outside the mask transparent.
   Write `full.glb`, `garment.glb`, render both with `render_previews.py`
   (front/back PNG), and record triangle count + whether the mesh is watertight (trimesh).
4. Re-run `scripts/trials_report.py`. Set T15 done and tell the human:
   "Gate G1 is due. Switch to Opus and run /gate G1."

## Must not
- Use a candidate whose licence note says "territory" before Opus clears it.

## Verify
- REPORT.md includes image_to_3d with preview PNG paths · `pytest -q` green.

GATE: G1

## Log
