# 05 — Decision log

Append-only. Opus writes entries at gates and escalations. Newest at the bottom.

Template:

```
## D-NNN — <title>  (YYYY-MM-DD, gate/escalation id)
Context: <why a decision was needed>
Decision: <what we chose>
Alternatives: <what we rejected and why>
Consequences: <what this changes for later tasks>
```

## D-001 — MetaHuman-first, measurement-based body  (2026-10-05, planning)
Context: Generating a full body from one image gives poor topology and no rig.
Decision: Use a MetaHuman-compatible body driven by measurements in cm.
Alternatives: Raw image-to-3D body (ugly, unrigged); a parametric research body model as the final asset (licence limits, not UE-native).
Consequences: Body-fitting models only need to output measurements; they can be swapped without touching later stages.

## D-002 — Rented NVIDIA GPU for development  (2026-10-05, planning)
Context: Most 3D research code is NVIDIA/CUDA-only; owner has an AMD 7900 XT.
Decision: Develop and run on a RunPod RTX 4090. Revisit AMD at G5.
Consequences: Small hourly GPU cost outside the GitHub budget.

## D-003 — Three garment strategies  (2026-10-05, planning)
Context: Garment reconstruction from one image is unreliable for loose items.
Decision: `skin_layer` for tight items, `template` from a garment library for common items, `generated` image-to-3D for unusual items.
Consequences: Quality depends heavily on the garment library (assets/garment_library).

## D-004 — Public repo; M0 work lands on main by direct push  (2026-10-06, T03 pre-gate)
Context: Owner made the repo public so the pod could clone without credentials. T03 assumed a
private repo and work on `main`, but M0 work lives on `claude/next-task-card-lscp12`, and CI
(`.github/workflows/ci.yml`) only runs on pushes to `main` or on pull requests.
Decision: Keep the repo public (owner decision). Merge the working branch into `main` on the pod
and push `main` directly so CI runs on it. The owner does the push; workers never handle tokens (AGENTS.md §4).
Alternatives: Private repo (rejected by owner); a PR to `main` (rejected by owner as an extra step).
Consequences: All history is public, so the CI secret scan and `.gitignore` rules are the only
guard against leaking secrets, weights or real-person images. Never commit test images of people.
Pushing from the pod needs a fine-grained token (this repo only, Contents: read/write), kept by the owner.

## D-005 — Network volume; budget GPU until model trials  (2026-10-07, after G0)
Context: The first pod had no persistent volume (`/workspace` was on the container overlay), and
M0 to T11 need no large GPU.
Decision: Keep all state on a RunPod **Network Volume** (~100 GB) mounted at `/workspace`, in a
datacenter that also has RTX 4090s. Use the cheapest NVIDIA pod for T04, T10, T11; switch to a
≥ 24 GB NVIDIA pod (RTX 4090 or A40; same template, same volume) from T12. Stay on the template's torch 2.4.1/CUDA 12.4.
Alternatives: 4090 throughout (pays GPU rates for code-only work); RTX 5090 (needs CUDA 12.8+/
torch 2.7+, a different stack; revisit at a gate if 24 GB proves too small).
Consequences: Before T12 the GPU will show < 20 GB VRAM; that is expected, not an escalation.
T12 cards must check `nvidia-smi` shows ≥ 20 GB before running trials. Volume costs a small
monthly fee even with no pod running.
Addendum (2026-10-07): an A40 (48 GB) is acceptable for both phases. Git storage on the volume:
see D-006.

## D-006 — Network volume holds data only; code, venv and Blender on local disk  (2026-10-07, T04 setup)
Context: The RunPod network volume mounts as `fuse.geesefs` (object storage). Tested on the pod:
`chmod` fails ("Operation not permitted"), files cannot be executed (exec → Permission denied),
and `git clone` onto it fails setting `core.filemode`.
Decision: `/workspace` keeps data only: weights, HF/torch/pip caches, the Blender tarball
(`downloads/`), job outputs (`jobs/`, via `AF_JOBS_DIR`), and git identity + saved token (`git/`).
The repo is cloned to `~/avatar-forge`, the venv is `/opt/venv-af`, Blender is unpacked to
`/opt/tools/blender`; `setup_pod.sh` rebuilds these on each new pod from the volume caches and
refuses to run from a repo on `/workspace`.
Alternatives: a pod-bound Volume Disk (supports chmod, but cannot move to a bigger GPU pod);
another datacenter's storage type (availability uncertain).
Consequences: Uncommitted work is lost when a pod is terminated, so commit and push before
terminating. `config/pipeline.yaml` points Blender at `/opt/tools/blender/blender`. Paths like
`/workspace/avatar-forge` in older task logs are historical. T10 must confirm a Hugging Face
download into `HF_HOME` on the volume works (its cache uses symlinks); if it fails, escalate.

## D-007 — Pin the template torch inside the venv  (2026-10-07, E-004)
Context: Installing T12 candidate dependencies pulled a CUDA 13 PyTorch build into `/opt/venv-af`.
It shadowed the template's torch 2.4.1+cu124, so CUDA became unavailable on the 12.8 driver; a
CPU-only onnxruntime likewise shadowed onnxruntime-gpu. Earlier the same pod reported cuda=True.
Decision: `config/pip-constraints.txt` (torch==2.4.1, numpy<2) is applied to every pip install via
`PIP_CONSTRAINT` (set by setup_pod.sh). A candidate that needs a newer torch now fails to install and
is recorded as failed; moving the torch/CUDA stack is a gate decision. Never `pip install onnxruntime`
(CPU) alongside `onnxruntime-gpu`.
Alternatives: per-candidate venvs (heavier; revisit at G1 if many candidates need newer torch).
Consequences: Workers check `python -c "import torch; print(torch.cuda.is_available())"` after any
install in T12–T15; False means stop and escalate.
Addendum (E-004 diagnosis): on inspection the pod was healthy (venv had no torch; system torch
2.4.1+cu124 cuda=True; onnxruntime-gpu 1.30.0 with CUDAExecutionProvider). The worker's report most
likely came from a terminal not using the venv. The constraints stay as a guard; T12's check now
prints the interpreter path.
Addendum (T12): `transformers>=4.48,<5` added to the constraints; 5.x needs torch>=2.5. T16 re-runs the two affected trials.
Addendum to D-004 (E-005, 2026-10-07): workers may run `git push`/`git pull` using the credential
the owner saved on the volume (`/workspace/git/credentials`). They must never read, print, type,
create or edit a token or credential file. If a push asks for a password, stop and tell the owner.
Addendum to D-006 (T16): Hugging Face `trust_remote_code` modules (e.g. BiRefNet) are Python files
that need normal permissions, so `HF_MODULES_CACHE` points at local disk (`~/.cache/hf_modules`);
weights stay on the volume under `HF_HOME`.

