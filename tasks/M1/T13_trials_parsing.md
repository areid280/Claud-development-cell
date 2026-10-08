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

## Sapiens notes (Opus, 2026-10-08)
- Weights: `huggingface_hub.list_repo_files("facebook/sapiens-seg-1b-torchscript")`, download the one
  `*.pt2` file with `hf_hub_download` (lands in `HF_HOME` on the volume), load with
  `torch.jit.load(path).eval().cuda()`. Do not use `transformers` / `AutoModel` for Sapiens.
- Pre/post-processing: follow `lite/demo/vis_seg.py` in github.com/facebookresearch/sapiens
  (input resized to 1024×768 H×W, ImageNet mean/std in 0–255 scale, output logits upsampled to the
  image size, argmax over the 28 Goliath classes). Map Goliath classes to canonical labels in the
  wrapper's table (e.g. Upper_Clothing→upper_clothes, Lower_Clothing→lower_clothes, Hair→hair,
  Face_Neck→face, *_Shoe→shoes, *_Sock→socks_stockings, Apparel→accessory, limbs/hands/feet→skin).
- Licence is CC BY-NC 4.0, acceptable under D-008. The 30-minute rule still applies.

## Must not
- Same as T12. If `sapiens-seg` setup takes > 30 minutes, record it as failed and move on.

## Verify
- `pytest -q` green · REPORT.md includes parsing.

## Done when
- [ ] Each candidate has summary.json; label images exist for successful ones

## Log
