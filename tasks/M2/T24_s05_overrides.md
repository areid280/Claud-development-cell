# T24 — Stage s05_body_params (overrides)
milestone: M2 · effort: low · depends: T23

## Goal
Apply `--set` overrides to the measured body and write the final `body_params.json`.
(Normalise is added later in T40.)

## Read first
- docs/06_STAGE_CONTRACTS.md (StageContext, StageResult, overrides, schema validation)
- src/avatar_forge/stages/s05_body_params.py (contract)
- src/avatar_forge/stages/s04_body_fit.py (the pattern to copy: load, validate, write, return)
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

## Contracts (Opus, 2026-10-10, E-023)
Everything not listed here is in `docs/06_STAGE_CONTRACTS.md`.

**`src/avatar_forge/body/overrides.py`** (pure; no file I/O, no logging)
- Module constants:
  `MEASUREMENT_KEYS = ("height", "bust", "underbust", "waist", "hips", "shoulder_width", "inseam", "arm_length", "thigh", "neck")`,
  `COLOR_KEYS = {"hair_color": "hair", "skin_color": "skin", "eye_color": "eyes"}`,
  `RESERVED_KEYS = frozenset({"normalise"})` (handled by s05 itself in T40: skip silently, no message),
  `MAX_CM = 300.0  # schemas/body_params.schema.json $defs.cm`.
- Value grammar, after `value.strip()`: `^([+-])?(\d+(?:\.\d+)?)(%)?$`
  | form | example | result |
  |------|---------|--------|
  | no sign, no `%` | `175` | absolute cm |
  | sign, no `%` | `+5`, `-3` | old + N cm |
  | sign and `%` | `+10%`, `-5%` | old × (1 + N/100) |
  | `%` without a sign, or anything else | `10%`, `tall`, `` | invalid |
- Round every new measurement with `round(x, 1)`.
- Process keys in `sorted(sets)` order so messages are deterministic.
- Never mutate the input: `body = copy.deepcopy(body)` first.
- On a successful measurement change, also set `body.setdefault("confidence", {})[key] = 1.0`
  (the user chose it).
- Exact messages (each makes the key a no-op, so the old value is kept):
  - unknown key: `Unknown setting '<key>' ignored.`
  - bad measurement value: `Invalid value '<value>' for '<key>' (use 175, +5, -3, +10% or -5%); ignored.`
  - relative form on a key that `body["measurements"]` lacks (`arm_length`, `thigh`, `neck` are
    optional): `Cannot apply '<value>' to '<key>': no measured value; ignored.`
    An absolute value on a missing optional key **sets** it (no message).
  - result `<= 0` or `> MAX_CM`: `'<key>' would become <new> cm (allowed: above 0, up to 300); ignored.`
  - bad colour (`^#[0-9a-fA-F]{6}$` fails): `Invalid colour '<value>' for '<key>' (use #rrggbb); ignored.`
    Valid colours are stored **lower-case**.

**`run(ctx)` in `s05_body_params.py`**
1. `body = json.loads(ctx.previous_output("s04_body_fit", "body_fit.json").read_text(encoding="utf-8"))`.
   A missing file raises; do not catch it (the runner records the failure).
2. `new_body, messages = apply_overrides(body, ctx.overrides.get("set", {}))`.
3. `new_body["source"] = "s05_body_params"`. Leave `body_type_hint` as it is and do **not** add a
   `normalise` key (T40 does). Do not read `ctx.stage_config()` yet (T40).
4. Validate against `SCHEMA_DIR / "body_params.schema.json"` exactly as s04 does; on error return
   `StageResult(status="fail", messages=[f"body_params.json failed schema validation: {exc.message}"])`.
5. `ctx.stage_dir.mkdir(parents=True, exist_ok=True)`; write `ctx.stage_dir / "body_params.json"`
   (`indent=2`, trailing newline). Do not touch `manifest.json`: the runner copies the file into
   `manifest["body"]`.
6. Return
   ```python
   StageResult(
       status="warn" if messages else "ok",
       outputs=["s05_body_params/body_params.json"],   # via relative_to(ctx.job_dir).as_posix()
       messages=messages,
       data={"normalised": False, "changes": {}, "overrides": applied},
   )
   ```
   where `applied` maps each measurement or colour key whose value changed to
   `{"from": old, "to": new}` (e.g. `{"bust": {"from": 90.0, "to": 99.0}}`), found by comparing
   `body` and `new_body`. Measurement keys use the measurement name; colour keys use the
   `colors` name (`hair`, `skin`, `eyes`).

**Height (by design, not a bug):** s04 already uses an absolute `--set height=175` as its scale
reference, so a full run gives consistent measurements. A later `rerun --from s05_body_params
--set height=...` changes only `height` (normalise and T41 handle the rest). To rescale every
measurement to a new height, rerun `--from s04_body_fit`.

**Tests** (`tests/test_overrides.py`, `tests/test_s05_body_params.py`). At minimum:
absolute, `+N`, `-N`, `+N%`, `-N%`, decimals (`+2.5`), whitespace, each invalid form,
`10%` (no sign) invalid, `<= 0` and `> 300` rejected, relative on a missing optional key,
absolute on a missing optional key, confidence set to 1.0, each colour key (valid upper-case
stored lower-case, invalid), unknown key message text, `normalise` skipped silently, height
changes nothing else, input not mutated. For `run`: `tmp_path` job with a hand-written
`s04_body_fit/body_fit.json`; check status `ok` without sets, `warn` with an unknown key,
`source`, `data["overrides"]`, and that the written file validates against the schema.

## Verify
- `pytest -q`
- On the pod, with the T23 job (`ls $AF_JOBS_DIR` to find it):
  `avatar-forge rerun $AF_JOBS_DIR/<job> --from s05_body_params --to s05_body_params --set bust=+10% --set hair_color=#2B1D14`
  then
  `python -c "import json,sys; j=sys.argv[1]; a=json.load(open(j+'/s04_body_fit/body_fit.json')); b=json.load(open(j+'/manifest.json')); print('bust', a['measurements']['bust'], '->', b['body']['measurements']['bust']); print('hair', b['body']['colors']['hair']); print(b['stages']['s05_body_params'])" $AF_JOBS_DIR/<job>`
  Expect: bust about +10%, hair `#2b1d14`, status `ok`. (Unknown keys are covered by unit tests;
  do not add one here, because `--set` values stay in the job's manifest.) Paste both outputs in Log.

## Log
