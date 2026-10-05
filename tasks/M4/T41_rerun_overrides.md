# T41 — Re-run with overrides (integration)
milestone: M4 · effort: low · depends: T40

> Planning-time draft. **Opus rewrites this card at G3.**

## Goal
`avatar-forge rerun <job> --from s05_body_params --set ...` regenerates everything downstream correctly.

## Do (outline)
1. Make every stage from s05 onward clear its own `stage_dir` before writing
   (idempotence), but never touch other stages' folders.
2. `rerun` keeps a copy of the previous export as `s09_export/<job_id>_prev/`
   so before/after can be compared.
3. Integration test (GPU/Blender-marked) on one sample: height +5 cm → exported
   body height +5 cm ±0.5; bust +10% → measured bust within 2 cm of target.

## Log
