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

## D-008 — Personal / non-commercial use; NC licences acceptable  (2026-10-08, owner, T13)
Context: Sapiens (T13 candidate) is CC BY-NC 4.0 (checked: github.com/facebookresearch/sapiens LICENSE).
Several later candidates (e.g. SMPL-X-based body models) are also non-commercial.
Decision (owner): avatar-forge and the characters it produces are for personal, non-commercial use.
Models under non-commercial licences (CC BY-NC, research-only) may be trialled and selected.
Alternatives: commercial-safe only (would exclude Sapiens and SMPL-X-family models).
Consequences: At each gate, licence checks still verify: no territory exclusions that cover the owner
(UK), attribution requirements are met (recorded in third-party notices, T53), and no licence forbids
the use itself. `config/models.yaml` gains `licence_class: commercial | non_commercial` per selected
model so a future switch to commercial use shows exactly what must be replaced. Revisit if the owner's
plans change.
Addendum to D-007 (E-007, 2026-10-08): installing `sam2` in a terminal without the venv replaced the
template's system torch (2.4.1+cu124) with a CUDA 13 build; CUDA became unavailable. Fixes:
setup_pod.sh writes `/etc/pip.conf` so the constraints apply to every pip on the pod; AGENTS.md
requires `source ~/.avatar_forge_env` in every terminal. The open-vocabulary trial uses SAM v1
(`facebook/sam-vit-huge`, in transformers 4.x) instead of SAM 2; whether SAM 2 justifies moving the
torch stack is a G1 question. A damaged system Python is repaired by restarting/redeploying the pod.
Addendum to D-006 (E-010, 2026-10-08): a stale `HF_MODULES_CACHE` copy of Florence-2's remote code
lacked `Florence2Processor` (AttributeError). Clearing `~/.cache/hf_modules` fixed it; setup_pod.sh now
clears it on every run. If a remote-code model fails to import, clear that cache before escalating.

## D-009 — Image-to-3D candidates: drop Hunyuan3D-2, add TripoSR, SF3D optional  (2026-10-08, E-013–E-015)
Context: T15 blocked on three candidates.
Decision:
- Hunyuan3D-2 is **excluded**: its licence "does not apply in the European Union, United Kingdom and
  South Korea" (LICENSE, Tencent/Hunyuan3D-2, checked 2026-10-08). The owner is in the UK. This holds
  for non-commercial use too, so D-008 does not help.
- TRELLIS stays: NVIDIA publishes `kaolin==0.17.0` wheels for torch-2.4.1_cu124 / cp311, so it fits the
  pinned stack (D-007). nvdiffrast's NVIDIA licence is non-commercial, acceptable under D-008.
- TripoSR (MIT, ungated) is added as a reliable baseline.
- Stable Fast 3D is optional: its weights are gated behind the Stability Community Licence. It is trialled
  only if the owner accepts that licence on Hugging Face and logs in on the pod (`huggingface-cli login`).
Consequences: G1 compares TRELLIS and TripoSR (plus SF3D if enabled). Hunyuan3D models stay out unless
the licence territory changes.

## D-010 — Pose: RTMW via rtmlib  (2026-10-09, G1)
Context: T12/T16 trials, 6 samples. rtmlib-rtmw 6/6, vitpose-hf 6/6; skeletons near-identical on contact sheets.
Decision: rtmlib-rtmw primary (whole-body: heel/toe keypoints feed height and measurements; ONNX, light).
vitpose-hf fallback. Licence: Apache-2.0 (rtmlib, mmpose); training data includes research-only sets, fine under D-008.

## D-011 — Background removal: BiRefNet  (2026-10-09, G1)
Context: T12/T16; birefnet 6/6, rembg (u2net_human_seg) 6/6; both clean at review resolution.
Decision: birefnet primary (MIT, state-of-the-art edges on hair); rembg fallback (not licence-approved yet).

## D-012 — Parsing: SegFormer clothes  (2026-10-09, G1)
Context: T13/T17. segformer-clothes 6/6, sapiens-seg 6/6, florence2-plus-sam 5/6. SegFormer gives the most useful
garment classes (dress, belt, shoes; cloak partly), Sapiens is comparable but left holes on c_front, Florence+SAM
mislabelled parts and stalls on stylised art.
Decision: segformer-clothes primary (single model in M2); sapiens-seg fallback (CC BY-NC, D-008);
Florence+SAM reconsidered at G3 for open-vocabulary parts. Licence_ok for SegFormer is pending a read of its
Hugging Face model card (unreachable from the gate environment).
Risk: no model separates a jacket from the bodysuit beneath it (both "upper clothes"); M3 must handle layers.

## D-013 — Body measurement: in-house keypoint ratio  (2026-10-09, G1)
Context: T14 keypoint-ratio 6/6 against owner reference estimates; T18 sam-3d-body skipped (gated, HTTP 401),
smpler-x skipped (needs SMPL-X registration).
Decision: keypoint-ratio for M2 (no third-party licence). Revisit mesh-based measurement at G3 if accuracy is short.

## D-014 — Image-to-3D: TRELLIS  (2026-10-09, G1)
Context: T15 trellis vs triposr on 6 samples (front/back renders after E-018). TRELLIS gives clean faces, garment
detail and a coherent cloak; TripoSR is noisy and blobby.
Decision: trellis primary, triposr fallback (MIT, simpler install). Licence: TRELLIS code and weights MIT. Its
optional dependency nvdiffrast is NVIDIA research/evaluation-only, which personal use may not fit, so it must not be
used at runtime; our export path builds the GLB from the raw mesh and should not need it (verified in T25).

