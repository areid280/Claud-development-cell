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
