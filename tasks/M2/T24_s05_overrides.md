# T24 — Stage s05_body_params (overrides)
milestone: M2 · effort: low · depends: T23

## Goal
Apply `--set` overrides to the measured body and write the final `body_params.json`.
(Normalise is added later in T40.)

## Read first
- src/avatar_forge/stages/s05_body_params.py (contract)
- schemas/body_params.schema.json
- src/avatar_forge/cli.py (`_parse_sets`) — values arrive as strings

## Do
1. `src/avatar_forge/body/overrides.py` (pure, tested):
   ```python
   def apply_overrides(body: dict, sets: dict[str, str]) -> tuple[dict, list[str]]
   ```
   - Measurement keys (`height`, `bust`, `underbust`, `waist`, `hips`,
     `shoulder_width`, `inseam`, `arm_length`, `thigh`, `neck`):
     `"175"` → absolute cm; `"+5"`/`"-3"` → add cm; `"+10%"`/`"-5%"` → relative.
   - Colour keys: `hair_color`, `skin_color`, `eye_color` → `colors.hair/skin/eyes`;
     must match `#rrggbb` (case-insensitive) else a warning message.
   - Unknown key → warning "Unknown setting '<key>' ignored."
   - Height changes scale **no other** measurement (that's normalise's job later).
   - Returns the new body (deep copy) and messages.
2. `run(ctx)`: load `s04_body_fit/body_fit.json`, apply `ctx.overrides["set"]`,
   set `source` to `"s05_body_params"`, write `body_params.json`
   (the runner copies it into manifest `body`). Status `warn` if any warnings.
3. Tests for every value form, colour validation and unknown keys.

## Verify
- `pytest -q` · `avatar-forge rerun <job> --from s05_body_params --to s05_body_params --set bust=+10%`
  then show the before/after bust value in Log.

## Log
