# Escalations

Workers append an entry, set the task to `blocked` in STATUS.md, and tell the
human: "Escalation for T<id>. Switch to Opus and run /escalate."
Opus resolves the newest `open` entry.

Template:

```
## E-NNN — T<id> — <short title>   status: open
Trigger: <which AGENTS.md §4 rule>
What I tried:
1. <attempt> -> <result>
2. <attempt> -> <result>
Error / evidence: <last 40 lines, or file paths>
Files involved: <paths>
My best guess: <one sentence>

Resolution (Opus): <filled in by Opus>
```

---

## E-001 — T00 — Not running on the GPU pod   status: resolved
Trigger: §4 GPU / CUDA / environment problems; task card requires the RunPod pod ("owner input").
What I tried:
1. nvidia-smi, ls /workspace, which blender -> none exist (cloud container, not the pod)
2. pip install -e . then ruff + pytest -> ruff passes; pytest fails at conftest: PIL (Pillow) missing
Error / evidence: see tasks/M0/T00_install_and_verify.md ## Log
Files involved: tasks/M0/T00_install_and_verify.md, pyproject.toml (Pillow not installed by `pip install -e .`?)
My best guess: Owner must run T00 on the pod (setup_pod.sh); separately check whether Pillow is a missing dependency in pyproject.toml.

Worker note: trigger no longer applies. Owner ran T00 on the pod; all Verify items passed and
setup_pod.sh was fixed (silent exit under set -e). Pillow was installed by the pod run. Opus to confirm and close.

Resolution (Opus): status: resolved. Environment confirmed on the pod (RTX 4090, cuda=True,
Blender 4.2.3, 14 tests pass). The Pillow failure was only the cloud container lacking the venv. The real
defect found was the setup_pod.sh silent exit, fixed in 6d30baf. No architecture or schema change.

## E-002 — T02 — s00_ingest test runner API   status: resolved
Trigger: §4 task card ambiguity; the card does not specify the module exporting `run_job` and `StageFailedError`.
What I tried:
1. Imported `StageFailedError`, `create_job`, and `run_job` from `avatar_forge.core.job` -> `StageFailedError` not exported there.
2. Removed that exception import and kept the runner helpers from `avatar_forge.core.job` -> `run_job` not exported there.
Error / evidence: `pytest -q` cannot collect `tests/test_s00_ingest.py`: `ImportError: cannot import name 'run_job' from 'avatar_forge.core.job'`; see `tasks/M0/T02_s00_ingest.md` ## Log.
Files involved: `src/avatar_forge/stages/s00_ingest.py`, `tests/test_s00_ingest.py`, `tasks/M0/T02_s00_ingest.md`
My best guess: The job runner and failure exception are defined in another module.

Resolution (Opus): Card defect, not a code defect. `create_job` lives in `avatar_forge.core.job`, but
`run_job` and `StageFailedError` live in `avatar_forge.core.runner` (tests/test_core.py already imports them
that way). The T02 card now lists the exact imports and call pattern, adds tests/test_core.py to
"Read first", and asks for the `downscaled` key to be added to the stage docstring so it matches the card.
No code under core/ or schemas/ changes. T02 set back to `todo`; the worker keeps its s00_ingest.py work
and fixes only the test imports.

## E-003 — T12 — Unspecified rembg human-segmentation weights   status: resolved
Trigger: §4 model / asset choice requires licence resolution.
What I tried:
1. Checked `nvidia-smi` -> A40 with 46,068 MiB VRAM; the GPU prerequisite passes.
2. Installed the dependency commands listed for all four T12 candidates -> all four commands exited successfully; no model weights were downloaded.
Error / evidence: `config/models.yaml` identifies the rembg candidate weights only as "downloaded by rembg (choose a human-seg model)" and does not name the model or its licence.
Files involved: `config/models.yaml`, `tasks/M1/T12_trials_pose_bg.md`, `docs/INSTALL_LOG.md`
My best guess: Opus should identify an eligible human-segmentation model and verify its code/weights licence before T12 runs the rembg trial.

Resolution (Opus): rembg trial uses only session u2net_human_seg; set U2NET_HOME to weights_dir()/rembg before importing rembg so weights land on the volume. Trials do not need licence_ok; licences are judged at G1. models.yaml and the T12 card updated in 7e3e172.

## E-004 — T12 — GPU runtime unavailable on model pod   status: resolved
Trigger: §4 GPU / CUDA / driver problem; `docs/04_ENVIRONMENT.md` says not to repair pod drivers in place.
What I tried:
1. Checked `nvidia-smi` -> NVIDIA A40, driver 570.195.03, CUDA 12.8.
2. Checked the configured venv -> PyTorch 2.14.1+cu130 (built for CUDA 13.0) reports `torch.cuda.is_available() == False`; ONNX Runtime 1.30.0 reports only `AzureExecutionProvider` and `CPUExecutionProvider`.
3. Ran `ruff check src tests` -> passed. `pytest -q` failed collection because `scripts` was not importable; `PYTHONPATH=. pytest -q` -> 28 passed, 1 warning.
Error / evidence: PyTorch warns that the NVIDIA driver is too old for the installed CUDA build; ONNX Runtime has no CUDA execution provider. No model trials were launched.
Files involved: `tasks/M1/T12_trials_pose_bg.md`, `tasks/STATUS.md`, `docs/04_ENVIRONMENT.md`
My best guess: Deploy the A40 with the documented CUDA 12.x RunPod PyTorch template and rebuild the venv with `setup_pod.sh`.

Resolution (Opus): Resolved in `4129b41` (D-007 addendum). The prior check used a terminal outside the configured virtual environment; after `source ~/.avatar_forge_env`, the documented CUDA check reports `/opt/venv-af/bin/python`, PyTorch `2.4.1+cu124`, CUDA available, and `CUDAExecutionProvider`.

## E-005 — T16 — Push instruction conflicts with D-004   status: resolved
Trigger: §4 task card contradicts another file.
What I tried:
1. Compared the T16 instruction to "commit and push" with D-004 -> D-004 says the owner pushes and workers never handle tokens.
2. Ran the requested install and trials -> `vitpose-hf` 6/6 and `birefnet` 6/6; documented commands and results in T16's Log and `docs/INSTALL_LOG.md`.
Error / evidence: T16's final push requirement conflicts with `docs/05_DECISIONS.md` D-004. Model results are in `jobs/_model_trials/REPORT.md`.
Files involved: `tasks/M1/T16_rerun_vitpose_birefnet.md`, `tasks/STATUS.md`, `docs/05_DECISIONS.md`, `docs/INSTALL_LOG.md`, `jobs/_model_trials/REPORT.md`
My best guess: Opus should clarify that T16 workers may commit locally but only the owner pushes, or update D-004 if the policy has changed.

Resolution (Opus, commit 9661370): Workers may run `git push` and `git pull` using
the owner's saved credential. Never read, print, or edit a token or credential
file; if a push asks for a password, stop and tell the owner. The Transformers
module cache is set permanently via `HF_MODULES_CACHE` on local disk.

## E-006 — T13 — Unspecified background-removal trial input   status: resolved
Trigger: §4 visual quality must be judged; the task card requires the "best-looking" T12 background-removal output as the parsing input.
What I tried:
1. Checked the T12 task log -> it reports candidate success counts but does not identify a best-looking candidate or image.
2. Checked the T13 card -> it requires an image chosen by visual quality, which I must not judge as a worker.
Error / evidence: T13 requires an input under `jobs/_model_trials/bg_remove/<name>/<stem>/cutout.png`, but neither T13 nor the T12 log names the candidate/image to use.
Files involved: `tasks/M1/T13_trials_parsing.md`, `tasks/M1/T12_trials_pose_bg.md`, `tasks/STATUS.md`
My best guess: Opus should review the T12 cutouts, specify the chosen candidate and image path, then return T13 to `todo`.

Resolution (Opus, commit 9897e93): No visual judgment is needed for T13. Use
BiRefNet cut-outs for every parsing candidate at
`jobs/_model_trials/bg_remove/birefnet/<stem>/cutout.png`; if one is missing,
fall back to the corresponding rembg cut-out and note the fallback in the T13
log. Evaluate background-removal quality at G1.

## E-007 — T13 — SAM2 install broke CUDA runtime   status: resolved
Trigger: §4 GPU / CUDA / driver problem; the configured model dependency install replaced the working CUDA-enabled Torch runtime and the documented environment guidance does not authorize repairing it in place.
What I tried:
1. Updated Sapiens to load the configured TorchScript `.pt2` from `facebook/sapiens-seg-1b-torchscript` -> all six BiRefNet cut-outs passed; `summary.json` reports 6/6.
2. Ran `/opt/venv-af/bin/python -m pip install sam2` to enable the configured Florence/SAM2 candidate -> install completed but replaced Torch `2.4.1+cu124` with `2.14.1+cu130`; pip reported the installed `torchaudio 2.4.1` requires Torch `2.4.1`.
3. Checked the runtime -> `torch.cuda.is_available()` is now `False`, with a driver-too-old warning (`found version 12080`).
Error / evidence: the install output reported the Torch/torchaudio dependency conflict; the post-install runtime check reports `torch 2.14.1+cu130`, `cuda_available False`, and the CUDA initialization warning. Before the install, `/opt/venv-af/bin/python` reported `torch 2.4.1+cu124` and CUDA available.
Files involved: `config/models.yaml`, `src/avatar_forge/models/parsing_sapiens_seg.py`, `tests/test_parsing_sapiens_seg.py`, `tasks/M1/T13_trials_parsing.md`, `tasks/STATUS.md`, `docs/INSTALL_LOG.md`
My best guess: Opus should restore or provision a Torch build compatible with the pod's CUDA driver, then rerun Florence/SAM2 and the remaining T13 verification; do not attempt an in-place CUDA repair as a worker.

Resolution (Opus, commits 8d833b1 and 606777d): RunPod's `/etc/rp_environment`
reset `PATH` in new terminals, so commands were using system Python rather than
the project venv. `setup_pod.sh` now leaves the venv environment line last in
`~/.bashrc`, and the Torch pin applies to every pip through `/etc/pip.conf`.
T13 uses Florence-2 plus SAM v1 (`transformers.SamModel` and
`facebook/sam-vit-huge`) instead of SAM 2; do not install `sam2` because it
requires Torch >= 2.5.1. Workers must source `~/.avatar_forge_env` and confirm
`which python` is `/opt/venv-af/bin/python` before running commands.

## E-008 — T14 — Mesh slice levels and model asset approval   status: open
Trigger: §4 task card ambiguity and model / asset choice requires licence resolution.
What I tried:
1. Read T14's mesh contract -> it requests bust, underbust, waist, and hip planes "at the same relative heights as above", but the mesh wrapper returns only vertices and faces; no shoulder/hip landmarks or mapping to the image is defined.
2. Read the body-measurement candidates in `config/models.yaml` -> SAM 3D Body and SMPLer-X have unverified licences; SMPL-X assets require owner registration. No model files were accessed or used.
3. Added the requested in-house fallback configuration and implementation scaffolding, and saved the owner-provided reference measurements -> mesh trials, report wiring, and verification are not complete.
Error / evidence: T14 does not specify how to identify anatomical slice heights from vertices/faces alone. Choosing fractions would introduce unapproved measurement assumptions. Model assets remain unapproved/unregistered.
Files involved: `tasks/M1/T14_trials_body_measure.md`, `config/models.yaml`, `config/pipeline.yaml`, `src/avatar_forge/body/keypoint_ratio.py`, `tests/test_keypoint_ratio.py`, `samples/reference.yaml`
My best guess: Opus should define the mesh slice-level convention and resolve candidate asset/licence availability, then return T14 to `todo` for completion and verification.

Resolution (Opus):
