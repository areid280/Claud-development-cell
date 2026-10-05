# T11 — Model trial harness
milestone: M1 · effort: low · depends: T10
owner input: test images in `samples/` on the pod (see samples/README.md). Ask for them now if missing and set status `waiting-owner`.

## Goal
Run any candidate model on the sample images in a uniform way so Opus can compare them at G1.

## Read first
- src/avatar_forge/models/base.py
- samples/README.md

## Do
1. Create `src/avatar_forge/models/trials.py`:
   ```python
   TrialFn = Callable[[dict, Path, Path], dict]   # (entry, image_path, out_dir) -> extra info
   REGISTRY: dict[tuple[str, str], TrialFn] = {}
   def register(role: str, name: str) -> Callable[[TrialFn], TrialFn]: ...   # decorator
   ```
2. Create `scripts/trial_model.py`:
   `python scripts/trial_model.py --role pose --name vitpose-hf --images "samples/*_front.png"`
   - For each image: out dir `jobs/_model_trials/<role>/<name>/<image_stem>/`.
   - `reset_vram_peak()`, time the call to the registered TrialFn, catch exceptions.
   - Write `trial.json`: `{role, name, image, ok, seconds, vram_peak_gb, error, extra}`.
   - After all images write `jobs/_model_trials/<role>/<name>/summary.json`
     (count ok/failed, mean seconds, max VRAM).
   - `--all-registered` runs every registered (role, name).
   - Import the adapter modules `avatar_forge.models.trial_adapters_*` (created in T12–T15)
     with `importlib` so registering happens; skip missing modules with a warning.
3. Create `scripts/trials_report.py` that walks `jobs/_model_trials/` and writes
   `jobs/_model_trials/REPORT.md`: one table per role (name, ok/total, mean s, max VRAM GB)
   and, under it, a list of the output PNG paths per image so Opus can open them.
4. Tests `tests/test_trials.py`: register a fake trial in the test, run
   `scripts/trial_model.py` logic through an importable `main(argv)` function
   on a synthetic image in `tmp_path`, check `trial.json` and `summary.json`.
   (Make `trial_model.py` expose `main(argv: list[str] | None) -> int` and
   accept `--out-root` for tests.)

## Must not
- Put model-specific code in the harness.

## Verify
- `ruff check src tests scripts` · `pytest -q`

## Done when
- [ ] Fake-trial test passes
- [ ] samples present on the pod (or status `waiting-owner`)

## Log
