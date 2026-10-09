# T23 — Stage s04_body_fit
milestone: M2 · effort: medium · depends: T22

> **G1 (Opus, 2026-10-09, D-013):** body_measure = **keypoint-ratio** (in-house), `src/avatar_forge/body/keypoint_ratio.py`
> `measure(keypoints, alpha, height_cm, cfg)`. Keypoints from `s01_validate/<view>_keypoints.json`, alpha from
> `s02_prepare/<view>_rgba.png`. Ignore `mesh_measure.py` in M2. `confidence` = 0.5 for every value.

## Goal
`body_fit.json` with measurements (cm) and colours that validates against the schema.

## Read first
- src/avatar_forge/stages/s04_body_fit.py (contract)
- schemas/body_params.schema.json
- config/pipeline.yaml → `stages.s04_body_fit`
- src/avatar_forge/body/keypoint_ratio.py and/or mesh_measure.py (whichever G1 selected)

## Contracts (Opus, 2026-10-09 — follow `s02_prepare.py` / `s03_parse.py` as the pattern)
- **Front view only:** inputs `s02_prepare/front_rgba.png`, `s02_prepare/front_keypoints.json`,
  `s03_parse/parts.json` and the `front` masks it lists. If there is no `front` input → `status="fail"`.
- **Keypoints:** `front_keypoints.json` is a list of persons in **s02 image coordinates**; use the highest-`score`
  person and pass its `keypoints` dict (`{name: [x, y, score]}`) to
  `keypoint_ratio.measure(keypoints, alpha, height_cm, cfg)`; `alpha = np.asarray(rgba.getchannel("A")) > 0`;
  `cfg = ctx.stage_config()`. It returns cm values for the schema's measurement keys.
- **Masks:** `Image.open(job_dir / part["mask"])` → `np.asarray(...) > 127`. Union of `skin` and `face` for skin colour.
- **Output** `s04_body_fit/body_fit.json`: `{"units": "cm", "source": "s04_body_fit", "measurements": {...},
  "confidence": {key: 0.5}, "colors": {"skin": "#rrggbb", "hair": "#rrggbb", "eyes": "#rrggbb"},
  "body_type_hint": ...}` (only keys the schema allows). Validate with
  `jsonschema.validate(data, json.load(open("schemas/body_params.schema.json")))` — resolve the schema path from
  `avatar_forge.core.paths` / repo root, not the working directory.
- **No model is loaded in this stage.**

## Do
1. Height reference: if `ctx.overrides.get("set", {}).get("height")` is a plain
   number use it; else `default_height_cm`. Record which in `data["height_source"]`.
2. Measurements via the selected method on the **front** view. Fill every
   required key; optional keys only if the method provides them.
   `confidence`: 0.5 for keypoint-ratio values, model-provided otherwise.
3. Colours (`src/avatar_forge/body/colours.py`, pure functions + tests):
   - skin: median RGB of pixels in `skin` ∪ `face` masks, excluding the darkest
     and brightest 10% (shadows/highlights). Hex.
   - hair: same on `hair` mask. If no hair mask → `#2b2420`.
   - eyes: `stages.s04_body_fit.default_eye_color` (new key, `#5a7a8c`) for now.
4. `body_type_hint` from config.
5. Write `body_fit.json`; validate it with `jsonschema` against
   `body_params.schema.json` inside the stage (fail with the validation message if invalid).

## Verify
- `pytest -q` (colours tests) · run `--to s04_body_fit` on all samples; put a
  table of measured vs `samples/reference.yaml` in Log.

## Escalate if
- Any measurement is off by > 20% on more than one sample.

## Log
