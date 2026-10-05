# T52 — Simple UI (four screens)
milestone: M5 · effort: medium · depends: T50

> Planning-time draft. **Opus rewrites this card at G4.**

## Goal
A browser UI on the pod (opened through VS Code port forwarding) matching the planned flow:
drop images → review what was found → tweak body → export.

## Do (outline)
1. Gradio app `src/avatar_forge/ui/app.py`, launched with `avatar-forge ui`.
2. Screen 1: front (+ optional back/left/right) upload, **required** checkbox
   "The subject is an adult, and this is an original character or I have their consent".
3. Screen 2: garment list from manifest with tick boxes (→ `disabled_garments`),
   strategy and colour shown; validation warnings shown.
4. Screen 3: sliders for each measurement (ranges from config), colour pickers,
   normalise toggle → calls `rerun --from s05_body_params`; shows previews.
5. Screen 4: export summary + "download zip".
6. Runs locally only (no public share links).

## Log
