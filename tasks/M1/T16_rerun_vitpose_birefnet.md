# T16 — Re-run ViTPose and BiRefNet with transformers 4.x
milestone: M1 · effort: low · depends: T12
owner input: none

## Goal
T12 recorded `vitpose-hf` and `birefnet` as 0/6 because transformers 5.x needs torch>=2.5 and
disables torch on our pinned 2.4.1. `config/pip-constraints.txt` now pins `transformers>=4.48,<5`.
Re-run only these two trials so G1 compares all four candidates.

## Read first
- tasks/M1/T12_trials_pose_bg.md (Log section only)
- config/pip-constraints.txt, docs/05_DECISIONS.md D-007

## Do
1. Use **only** the pod venv. In a new terminal:
   ```bash
   source ~/.avatar_forge_env && cd ~/avatar-forge
   rm -rf .venv                      # a stray venv from T12; never create another one
   python -m pip install -e ".[dev,models]"
   python -m pip install timm kornia
   python -c "import sys, torch, transformers, onnxruntime as o; print(sys.executable, torch.__version__, torch.cuda.is_available(), transformers.__version__, o.get_available_providers())"
   ```
   Must print `/opt/venv-af/bin/python 2.4.1+cu124 True 4.x.y [... 'CUDAExecutionProvider' ...]`.
2. Re-run the two trials:
   ```bash
   python scripts/trial_model.py --role pose --name vitpose-hf --images "samples/*.png"
   python scripts/trial_model.py --role bg_remove --name birefnet --images "samples/*.png"
   python scripts/trials_report.py
   ```
3. Append the install commands to `docs/INSTALL_LOG.md`, paste results into the Log, set T16 done,
   commit `T16: <summary>`, push.

## Must not
- Upgrade torch, create a new venv, or change `selected`/`licence_ok`.

## Verify
- `ruff check src tests` · `pytest -q`
- `REPORT.md` shows a result (ok or a new, different error) for both candidates.

## Escalate if
- Either still fails for a reason other than a bug in our wrapper after ~30 minutes.

## Log

- `nvidia-smi`: NVIDIA A40, 46,068 MiB VRAM.
- Installed `.[dev,models]`, `timm`, `kornia`; environment check reported `/opt/venv-af/bin/python 2.4.1+cu124 True 4.57.6 ['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']`.
- Initial trials: `vitpose-hf` passed 6/6; `birefnet` failed 0/6 because its Transformers dynamic module cache on `/workspace` could not be chmod'ed and `einops` was missing. Installed `einops` 0.8.2 and reran BiRefNet with `HF_MODULES_CACHE=/tmp/avatar-forge-hf-modules`.
- Final report: `jobs/_model_trials/REPORT.md` reports `vitpose-hf` 6/6 (mean 26.035 s, 1.532 GB max VRAM) and `birefnet` 6/6 (mean 13.207 s, 3.352 GB max VRAM). Outputs were generated for all six sample images.
- Blocked before final verification/commit/push: this card asks the worker to push, while D-004 in `docs/05_DECISIONS.md` says the owner does the push and workers never handle tokens. See E-005 in `tasks/ESCALATIONS.md`.
