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
