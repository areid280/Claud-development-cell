#!/usr/bin/env bash
# Idempotent install of TRELLIS, the selected image_to_3d model (G1, D-014), into /opt/venv-af.
# Called by setup_pod.sh; safe to run again. Commands are the ones proven in T15 (E-017,
# docs/INSTALL_LOG.md). nvdiffrast is compiled once and its wheel kept on the volume, so later
# pods install it in seconds. Never compiles any other CUDA op (no diff-gaussian-rasterization).
set -euo pipefail

SRC=/opt/src/TRELLIS
WHEELS=/workspace/downloads/wheels
# shellcheck disable=SC1090
source "$HOME/.avatar_forge_env"

import_check() {
  python - <<'EOF'
import os, sys
os.environ["ATTN_BACKEND"] = "xformers"
os.environ["SPCONV_ALGO"] = "native"
sys.path.insert(0, "/opt/src/TRELLIS")
import torch, kaolin, nvdiffrast, spconv  # noqa: E401,F401
import xformers.ops.fmha as fmha
from xformers.ops.fmha.attn_bias import BlockDiagonalMask
fmha.BlockDiagonalMask = BlockDiagonalMask  # same patch as models/i23d_trellis.py
from trellis.pipelines import TrellisImageTo3DPipeline  # noqa: F401
assert torch.cuda.is_available(), "CUDA not available"
print("TRELLIS ready:", torch.__version__, "kaolin", kaolin.__version__)
EOF
}

mkdir -p /opt/src "$WHEELS"
if [ ! -d "$SRC/.git" ]; then
  git clone --recurse-submodules https://github.com/microsoft/TRELLIS.git "$SRC"
fi
if [ -d "$SRC/.git" ] && import_check 2>/dev/null; then
  exit 0
fi

echo "== installing TRELLIS dependencies =="
if command -v apt-get >/dev/null && ! dpkg -s libusb-1.0-0 >/dev/null 2>&1; then
  apt-get install -y --no-install-recommends libusb-1.0-0 || { apt-get update -y && apt-get install -y --no-install-recommends libusb-1.0-0; }
fi
python -m pip install kaolin==0.17.0 -f https://nvidia-kaolin.s3.us-east-2.amazonaws.com/torch-2.4.1_cu124.html
python -m pip install xformers==0.0.28.post1 --index-url https://download.pytorch.org/whl/cu124
python -m pip install spconv-cu120 easydict plyfile ninja open3d pyvista pymeshfix igraph \
  "utils3d@git+https://github.com/EasternJournalist/utils3d.git@9a4eb15e4021b67b12c460c7057d642626897ec8"

# nvdiffrast must build against the venv torch (E-017). geesefs can leave 0-byte files: drop them.
find "$WHEELS" -name 'nvdiffrast-*.whl' -size 0 -delete
if ! ls "$WHEELS"/nvdiffrast-*.whl >/dev/null 2>&1; then
  python -m pip wheel --no-build-isolation --no-deps -w "$WHEELS" git+https://github.com/NVlabs/nvdiffrast.git
fi
python -m pip install --no-deps "$(ls -t "$WHEELS"/nvdiffrast-*.whl | head -1)"

import_check
