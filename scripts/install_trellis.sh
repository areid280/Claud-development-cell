#!/usr/bin/env bash
# Idempotent install of TRELLIS, the selected image_to_3d model (G1, D-014), into /opt/venv-af.
# Called by setup_pod.sh; safe to run again. Commands are the ones proven in T15 (E-017,
# docs/INSTALL_LOG.md). nvdiffrast is compiled once and its wheel kept on the volume, so later
# pods install it in seconds. Never compiles any other CUDA op (no diff-gaussian-rasterization).
set -euo pipefail

SRC=/opt/src/TRELLIS
WHEELS="${AF_WHEELS_DIR:-/workspace/downloads/wheels}"   # cache only; see E-025
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

# nvdiffrast must build against the venv torch (E-017). pip cannot write to the volume: it copies
# files with their permissions and geesefs refuses chmod (E-025). So build on local disk, copy plain
# bytes to the volume as a cache, and always install from a local, zip-checked copy.
LOCAL_WHEELS="$HOME/.cache/af-wheels"
mkdir -p "$LOCAL_WHEELS"
rm -f "$LOCAL_WHEELS"/nvdiffrast-*.whl
find "$WHEELS" -name 'nvdiffrast-*.whl*' -size 0 -delete 2>/dev/null || true
cached=$(ls -t "$WHEELS"/nvdiffrast-*.whl 2>/dev/null | head -1 || true)
if [ -n "$cached" ] && cat "$cached" > "$LOCAL_WHEELS/$(basename "$cached")" \
    && python -m zipfile -t "$LOCAL_WHEELS/$(basename "$cached")" >/dev/null 2>&1; then
  echo "nvdiffrast: using cached wheel $cached"
else
  rm -f "$LOCAL_WHEELS"/nvdiffrast-*.whl
  python -m pip wheel --no-build-isolation --no-deps -w "$LOCAL_WHEELS" \
    git+https://github.com/NVlabs/nvdiffrast.git
  built=$(ls -t "$LOCAL_WHEELS"/nvdiffrast-*.whl | head -1)
  name=$(basename "$built")
  # plain byte copy (no chmod/utime); write to .part then rename so a cut-off copy is never used
  if cat "$built" > "$WHEELS/$name.part" && mv -f "$WHEELS/$name.part" "$WHEELS/$name"; then
    echo "nvdiffrast: cached $name on the volume"
  else
    rm -f "$WHEELS/$name.part" 2>/dev/null || true
    echo "WARNING: could not cache the nvdiffrast wheel on the volume; next pod rebuilds it" >&2
  fi
fi
python -m pip install --no-deps --force-reinstall "$(ls -t "$LOCAL_WHEELS"/nvdiffrast-*.whl | head -1)"

import_check
