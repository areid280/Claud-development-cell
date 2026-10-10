# Install Log

## T12 — 2026-10-07

Commands run in the repository's `.venv`:

```shell
/root/avatar-forge/.venv/bin/python -m pip install rtmlib onnxruntime-gpu
/root/avatar-forge/.venv/bin/python -m pip install transformers
/root/avatar-forge/.venv/bin/python -m pip install transformers timm kornia
/root/avatar-forge/.venv/bin/python -m pip install 'rembg[gpu]'
```

All four commands exited successfully. No candidate weights were downloaded.

## T12 — configured model venv — 2026-10-07

The commands below were run after `source ~/.avatar_forge_env`. The CUDA
environment check passed after each candidate install except the first RTMLib
install, which exposed the CPU `onnxruntime` dependency ahead of
`onnxruntime-gpu`. The GPU package was reinstalled and the required CUDA check
then passed.

```shell
python -m pip install rtmlib onnxruntime-gpu
python -m pip uninstall -y onnxruntime
python -m pip install onnxruntime-gpu
python -m pip install --force-reinstall --no-deps onnxruntime-gpu
python -m pip install transformers
python -m pip install transformers timm kornia
python -m pip install 'rembg[gpu]'
python -m pip install --force-reinstall --no-deps onnxruntime-gpu==1.20.1
python -m pip install --force-reinstall --no-deps onnxruntime-gpu==1.20.2
```

The `onnxruntime-gpu==1.20.1` install was attempted but that exact release is not
available from the configured package index; 1.20.2 installed successfully.

Post-install check:

```shell
python -c "import sys, torch, onnxruntime as o; print(sys.executable, torch.__version__, torch.cuda.is_available(), o.get_available_providers())"
```

It reports `/opt/venv-af/bin/python`, `2.4.1+cu124`, `True`, and
`CUDAExecutionProvider` after each successful verification.

RTMLib inference also needed the system-installed CUDA libraries visible to the
ONNX Runtime loader. Its rerun used:

```shell
LD_LIBRARY_PATH=/usr/local/lib/python3.11/dist-packages/nvidia/cudnn/lib:/usr/local/lib/python3.11/dist-packages/nvidia/cublas/lib:/usr/local/lib/python3.11/dist-packages/nvidia/cuda_runtime/lib python scripts/trial_model.py --role pose --name rtmlib-rtmw --images "samples/*.png"
```

## T16 — configured model venv — 2026-10-07

Commands run after `source ~/.avatar_forge_env` in `~/avatar-forge`:

```shell
python -m pip install -e '.[dev,models]'
python -m pip install timm kornia
python -m pip install einops
python -c "import sys, torch, transformers, onnxruntime as o; print(sys.executable, torch.__version__, torch.cuda.is_available(), transformers.__version__, o.get_available_providers())"
```

The environment check reported `/opt/venv-af/bin/python`, `2.4.1+cu124`,
`True`, Transformers `4.57.6`, and providers including
`CUDAExecutionProvider`. BiRefNet's first run failed because its dynamic module
cache was on the volume and could not be chmod'ed, and because `einops` was
missing. After installing `einops`, the rerun used a writable module cache:

```shell
HF_MODULES_CACHE=/tmp/avatar-forge-hf-modules python scripts/trial_model.py --role bg_remove --name birefnet --images "samples/*.png"
python scripts/trials_report.py
```

## T13 — 2026-10-08

```shell
/opt/venv-af/bin/python -m pip install sam2
```

The install completed with `sam2 1.1.0`, but pip upgraded Torch from
`2.4.1+cu124` to `2.14.1+cu130` and reported that installed `torchaudio 2.4.1`
requires Torch `2.4.1`. A post-install check reported `torch.cuda.is_available()
== False` with a driver-too-old warning (`found version 12080`). Florence/SAM2
trials were stopped for Opus escalation; see T13's task log and `tasks/ESCALATIONS.md`.

## T13 — resumed with SAM v1 — 2026-10-08

After sourcing `~/.avatar_forge_env`, `which python` reported
`/opt/venv-af/bin/python`; the environment check reported Torch `2.4.1+cu124`
and CUDA available. Florence-2's remote model code required two missing
dependencies, installed without changing the pinned Torch runtime:

```shell
python -m pip install timm einops
```

The first Florence trial found zero-byte entries in the existing model cache;
those cache entries were restored from their existing Hugging Face blobs.
Trials then used `florence2-plus-sam` (SAM v1) without installing `sam2`.
Five BiRefNet inputs completed; `c_front` stalled with no output and was marked
failed per the T13 30-minute rule. See `jobs/_model_trials/parsing/florence2-plus-sam/summary.json`.

## T15 — TripoSR dependencies — 2026-10-09

After `source ~/.avatar_forge_env`, installed the TripoSR runtime dependencies
without building `torchmcubes`:

```shell
git clone https://github.com/VAST-AI-Research/TripoSR.git /opt/src/TripoSR
python -m pip install omegaconf xatlas PyMCubes
```

All three packages were already installed in `/opt/venv-af` (`omegaconf 2.4.0`,
`xatlas 0.0.11`, `PyMCubes 0.1.6`).

The TripoSR source checkout is at `/opt/src/TripoSR`. Trials ran with
`/opt/venv-af/bin/python`, CUDA available, and the PyMCubes-backed shim. The
Hugging Face cache emitted permission warnings for incomplete download files
but continued successfully.

## T15 — TRELLIS dependencies — 2026-10-09

After `source ~/.avatar_forge_env`, the task-card commands installed Kaolin
`0.17.0`, xformers `0.0.28.post1`, `spconv-cu120`, `easydict`, `plyfile`, and
the pinned `utils3d` revision. The documented `nvdiffrast` install command:

```shell
python -m pip install git+https://github.com/NVlabs/nvdiffrast.git
```

failed during build requirement discovery because its CUDA extension could not
see PyTorch under build isolation. Per the T15 restriction against compiling
extra CUDA ops, it was not retried with `--no-build-isolation`; see E-017.

After E-017 resolution (`b0875de`), installed the allowed CUDA extension using:

```shell
python -m pip install ninja
python -m pip install --no-build-isolation git+https://github.com/NVlabs/nvdiffrast.git
```

The extension compiled successfully. The import smoke test printed
`2.4.1+cu124 True 0.17.0`. TRELLIS runtime imports also required:

```shell
python -m pip install open3d pyvista pymeshfix igraph
apt-get install -y libusb-1.0-0
```

The T15 TRELLIS trials initially reached `to_glb` but failed because its
texture-baking renderer imports the explicitly excluded
`diff_gaussian_rasterization`. No Gaussian rasterizer was built. Instead, the
wrapper requests mesh-only output and exports TRELLIS's decoded per-vertex
RGB attributes into a GLB with vertex colors; this avoids the prohibited
Gaussian-splat path and does not produce a texture atlas.

## T18 — mesh-based body measurement — 2026-10-09

No packages were installed. The SAM 3D Body checkpoint was checked without
credentials using:

```shell
curl --disable --max-time 30 -sS -o /dev/null -w '%{http_code}\n' \
  'https://huggingface.co/facebook/sam-3d-body-dinov3/resolve/main/model.ckpt'
```

The request returned HTTP 401, so the candidate was stopped per T18 and marked
`skipped: needs owner HF access request`. SMPLer-X was skipped because owner
SMPL-X registration was not provided. Both outcomes are recorded in
`jobs/_model_trials/REPORT.md`.

## E-024 — TRELLIS install automated — 2026-10-10

`scripts/install_trellis.sh` (run by `setup_pod.sh`; skip with `AF_SKIP_TRELLIS=1`) repeats the T15
commands above on every new pod, adds `open3d pyvista pymeshfix igraph` and `libusb-1.0-0`, and keeps the
compiled nvdiffrast wheel in `/workspace/downloads/wheels` so it is built only once. It ends with an
import check that prints `TRELLIS ready: <torch> kaolin <version>`.
E-025 (2026-10-10): pip cannot write into `/workspace` (geesefs refuses chmod), so the nvdiffrast wheel is
built in `~/.cache/af-wheels` and copied to `/workspace/downloads/wheels` as plain bytes. Rule for any
future cache on the volume: write with `cat`/`curl -o`, never `pip -w`, `cp -p` or `shutil.copy`.
