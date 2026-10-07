# T13 — Trials: human/garment parsing
milestone: M1 · effort: medium · depends: T12
owner input: none

## Goal
Working wrappers + trial outputs for every `parsing` candidate.

## Read first
- config/models.yaml → role `parsing`
- config/pipeline.yaml → `stages.s03_parse.labels`
- src/avatar_forge/models/trials.py, one wrapper from T12 as a pattern
- docs/INSTALL_LOG.md

## Do
1. Wrapper per candidate: `src/avatar_forge/models/parsing_<shortname>.py`,
   `predict(image_rgba: PIL.Image) -> dict[str, np.ndarray]` mapping **canonical**
   label → boolean mask (H×W). Put the model-label → canonical-label table at
   the top of each wrapper as a dict constant. Unmappable labels go to `accessory`.
2. For the open-vocabulary candidate (`florence2-plus-sam2`): text prompts come
   from a new config key `stages.s03_parse.open_vocab_prompts`. Add it to
   `config/pipeline.yaml` with: `["hair", "face", "jacket", "bodysuit", "gloves",
   "belt", "collar", "boots", "shoes", "skirt", "dress", "hat", "stockings", "harness", "bra", "top"]`.
   Each prompt → boxes → SAM 2 masks → canonical label (same name, or `upper_clothes`
   for `top`, `socks_stockings` for `stockings`).
3. Trial adapter module `trial_adapters_parsing.py`: per image write
   `masks/<label>.png`, `labels.png` (colour-coded, fixed colour per label),
   `parts.json` ({label: area_px}). Input (Opus, E-006): use the **BiRefNet** cut-outs for every
   candidate, `jobs/_model_trials/bg_remove/birefnet/<stem>/cutout.png`. Do not judge or switch
   inputs; if a BiRefNet cut-out is missing for an image, fall back to the `rembg` one and note it
   in the Log. Background-removal quality is judged at G1, not here.
4. Run trials for every candidate; append installs to `docs/INSTALL_LOG.md`;
   rerun `scripts/trials_report.py`.

## Must not
- Same as T12. If `sapiens-seg` setup takes > 30 minutes, record it as failed and move on.

## Verify
- `pytest -q` green · REPORT.md includes parsing.

## Done when
- [ ] Each candidate has summary.json; label images exist for successful ones

## Log
