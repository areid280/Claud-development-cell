# T15 — Trials: image-to-3D
milestone: M1 · effort: medium · depends: T14 (render_previews.py written by Opus, E-012)
owner input: none

## Goal
Textured 3D outputs from each `image_to_3d` candidate on (a) the whole figure and
(b) one masked garment crop, so Opus can judge quality at G1.

## Read first
- config/models.yaml → role `image_to_3d` (read every `licence_note`)
- src/avatar_forge/blender/render_previews.py (exists; args `--in <glb> --out-dir <dir> [--size 768]`, writes front.png + back.png; call via `run_blender`)
- docs/INSTALL_LOG.md

## Do
1. **Before installing `hunyuan3d-2`**: its licence note mentions territory
   exclusions and the owner is in the UK. Do not install it. Write an
   escalation (E-entry) asking Opus to check the licence first, mark it
   "skipped pending licence" in Log, and continue with the others.
2. For each remaining candidate: install following its README (use its own
   setup script where provided; record commands in docs/INSTALL_LOG.md).
   Wrapper `src/avatar_forge/models/i23d_<shortname>.py`:
   `predict(image_rgba: PIL.Image, seed: int = 0) -> Path` writing a GLB into a given out dir.
3. Trial adapter `trial_adapters_i23d.py`: for each sample, run on
   - the full cut-out (`cutout.png` from the best T12 bg_remove trial), and
   - one garment crop: take the `boots` or `jacket` mask from the best T13 trial,
     crop the cut-out to the mask bbox +10%, set pixels outside the mask transparent.
   Write `full.glb`, `garment.glb`, render both with `render_previews.py`
   (front/back PNG), and record triangle count + whether the mesh is watertight (trimesh).
4. Re-run `scripts/trials_report.py`. Set T15 done and tell the human:
   "Gate G1 is due. Switch to Opus and run /gate G1."

## Opus notes (2026-10-08, E-013/E-014/E-015, D-009)
Always `source ~/.avatar_forge_env` first; all installs go into the venv and honour the torch pin.
- **hunyuan3d-2: do not install or trial** (UK excluded by its licence). Record "excluded: licence territory (D-009)".
- **stable-fast-3d:** trial only if the owner says they accepted the licence on Hugging Face and ran
  `huggingface-cli login`. Otherwise record "skipped: gated, owner has not enabled (optional)". Never handle tokens.
- **trellis:** source on local disk, prebuilt wheels only:
  ```bash
  git clone --recurse-submodules https://github.com/microsoft/TRELLIS.git /opt/src/TRELLIS
  pip install kaolin==0.17.0 -f https://nvidia-kaolin.s3.us-east-2.amazonaws.com/torch-2.4.1_cu124.html
  pip install xformers==0.0.28.post1 --index-url https://download.pytorch.org/whl/cu124
  pip install spconv-cu120 easydict plyfile utils3d@git+https://github.com/EasternJournalist/utils3d.git@9a4eb15e4021b67b12c460c7057d642626897ec8
  pip install git+https://github.com/NVlabs/nvdiffrast.git
  python -c "import torch, kaolin, xformers, spconv, nvdiffrast; print(torch.__version__, torch.cuda.is_available(), kaolin.__version__)"
  ```
  The check must print `2.4.1+cu124 True 0.17.0`. In the wrapper set `ATTN_BACKEND=xformers` and
  `SPCONV_ALGO=native` before importing `trellis`, add `/opt/src/TRELLIS` to `sys.path`, and export only
  the mesh (`postprocessing_utils.to_glb`). Skip Gaussian-splat outputs (no diff-gaussian-rasterization).
  If any of these fails, follow the 30-minute rule and record it; do not compile extra CUDA ops.
- **triposr:** source on local disk; do **not** `pip install -r requirements.txt` (it pins old transformers/Pillow):
  ```bash
  git clone https://github.com/VAST-AI-Research/TripoSR.git /opt/src/TripoSR
  pip install omegaconf xatlas git+https://github.com/tatsy/torchmcubes.git
  ```
  Wrapper: add `/opt/src/TripoSR` to `sys.path`; `from tsr.system import TSR`;
  `TSR.from_pretrained("stabilityai/TripoSR", config_name="config.yaml", weight_name="model.ckpt")`;
  input = the BiRefNet cut-out composited on #808080 at the face-forward crop (see the repo's `run.py`);
  `model.extract_mesh(scene_codes, True, resolution=256)` → export GLB.
- Add new pip packages to `docs/INSTALL_LOG.md` as usual. Code under /opt/src is rebuilt per pod (D-006).

## Must not
- Use a candidate whose licence note says "territory" before Opus clears it.

## Verify
- REPORT.md includes image_to_3d with preview PNG paths · `pytest -q` green.

GATE: G1

## Log
