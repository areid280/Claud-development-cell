# T12 — Trials: pose and background removal
milestone: M1 · effort: medium · depends: T11
owner input: none

## Goal
Working wrappers + trial outputs for every `pose` and `bg_remove` candidate in config/models.yaml.

## Read first
- config/models.yaml → roles `pose`, `bg_remove`
- src/avatar_forge/models/base.py, src/avatar_forge/models/trials.py
- The candidate's own README (open the `source` link) for install and usage — **only** the usage section.

## Do
0. Run `nvidia-smi`. If the GPU has < 20 GB VRAM, stop and tell the human:
   "Switch to the RTX 4090 pod (D-005, docs/04 §B) before T12." Do not run trials on a budget GPU.
1. For each candidate, create `src/avatar_forge/models/<role>_<shortname>.py`
   with a `ModelWrapper` subclass. Canonical outputs:
   - pose: `predict(image: PIL.Image) -> list[Person]` where
     `Person = {"bbox": [x0, y0, x1, y1], "score": float,
     "keypoints": {coco_name: [x, y, score]}}` using the 17 COCO names
     (`nose, left_eye, right_eye, left_ear, right_ear, left_shoulder, …, right_ankle`).
     Whole-body models may add extra names (`left_heel`, `left_big_toe`, …).
   - bg_remove: `predict(image: PIL.Image) -> PIL.Image` in RGBA.
2. Create `src/avatar_forge/models/trial_adapters_pose_bg.py` registering one
   trial per candidate. Each writes into `out_dir`:
   - pose: `keypoints.json`, `overlay.png` (skeleton drawn with Pillow `ImageDraw`).
   - bg_remove: `cutout.png`, `on_grey.png` (cut-out composited on #808080).
   - **rembg (Opus, E-003):** use exactly one session, `new_session("u2net_human_seg")`, and
     set `os.environ.setdefault("U2NET_HOME", str(weights_dir() / "rembg"))` (`from avatar_forge.core.paths import weights_dir`) before importing rembg so
     the weights land on the volume, not in `~/.u2net`. Do not trial other rembg sessions.
     Running a trial does not need `licence_ok`; licences are judged at G1.
3. Install each candidate's dependencies **inside the venv** following its README
   (`PIP_CONSTRAINT` keeps torch at 2.4.1, D-007). After each install run
   `source ~/.avatar_forge_env && python -c "import sys, torch, onnxruntime as o; print(sys.executable, torch.__version__, torch.cuda.is_available(), o.get_available_providers())"`;
   it must print `/opt/venv-af/bin/python`, `2.4.1+cu124`, `True` and include `CUDAExecutionProvider`.
   Any other interpreter path means the terminal is not using the venv: fix that, do not escalate. If an install fails on the torch
   constraint, record that candidate as failed (needs newer torch) and move on.
   Record every install command you ran in `docs/INSTALL_LOG.md` (create it; Opus
   turns this into the extras at G1).
4. Run `python scripts/trial_model.py --role pose --name <each> --images "samples/*.png"`
   and the same for `bg_remove`. Then `python scripts/trials_report.py`.

## Must not
- Change `selected`/`licence_ok`. Commit weights or outputs.
- Spend more than ~30 minutes of attempts on one candidate: record it as failed in Log and move on.

## Verify
- `ruff check src tests` · `pytest -q` (keep CPU tests green; heavy imports inside functions)
- `jobs/_model_trials/REPORT.md` lists every candidate for both roles.

## Done when
- [ ] Each candidate has a summary.json (ok or with the error)
- [ ] REPORT.md path in Log

## Escalate if
- A candidate needs compiling CUDA extensions that fail twice.

## Log

- `nvidia-smi`: NVIDIA A40, 46,068 MiB VRAM; prerequisite passed.
- Environment check after `source ~/.avatar_forge_env`: `/opt/venv-af/bin/python 2.4.1+cu124 True ['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']`.
- Install commands recorded in `docs/INSTALL_LOG.md`. `rtmlib` installed CPU `onnxruntime` alongside the GPU package; removed the CPU package and reinstalled the GPU package. ONNX Runtime 1.30 required CUDA 13, so pinned the session to 1.20.2 and added the pod's cuDNN/cuBLAS/CUDA runtime libraries to `LD_LIBRARY_PATH` for RTMLib inference.
- E-003 resolved in `7e3e172`: the rembg trial uses only `u2net_human_seg`; its weights are stored under `weights_dir() / "rembg"` via `U2NET_HOME`.
- E-004 resolved in `4129b41`: the check must run after sourcing `~/.avatar_forge_env`.
- Trial results over 6 images each: `rtmlib-rtmw` 6/6; `vitpose-hf` 0/6 (Transformers 5.19 requires PyTorch >=2.5; the pinned PyTorch 2.4.1 also yielded an unrecognized RT-DETR processor); `birefnet` 0/6 (Transformers disabled PyTorch because 2.4.1 is below its minimum); `rembg` 6/6.
- Report: `jobs/_model_trials/REPORT.md` lists all four candidates, both roles, output images, and per-candidate summaries.
- Verify: `ruff check src tests` -> `All checks passed!`; `pytest -q` -> `28 passed in 5.73s`.
