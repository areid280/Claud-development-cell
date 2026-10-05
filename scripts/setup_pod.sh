#!/usr/bin/env bash
# One-time (idempotent) setup on a RunPod PyTorch pod. Run from the repo root:
#   bash scripts/setup_pod.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WS="/workspace"
VENV="$WS/venv-af"

echo "== avatar-forge pod setup =="
echo "repo: $REPO_DIR"

# 1. Persistent cache/weights locations (survive pod stop because they live in /workspace)
mkdir -p "$WS/weights" "$WS/cache/hf" "$WS/cache/pip" "$WS/cache/torch" "$WS/tools"
PROFILE_SNIPPET="$HOME/.avatar_forge_env"
cat > "$PROFILE_SNIPPET" <<EOF
export AF_WEIGHTS_DIR=$WS/weights
export HF_HOME=$WS/cache/hf
export PIP_CACHE_DIR=$WS/cache/pip
export TORCH_HOME=$WS/cache/torch
export PATH=$WS/tools/blender:\$PATH
[ -f $VENV/bin/activate ] && source $VENV/bin/activate
EOF
grep -qxF "source $PROFILE_SNIPPET" "$HOME/.bashrc" || echo "source $PROFILE_SNIPPET" >> "$HOME/.bashrc"
# shellcheck disable=SC1090
source "$PROFILE_SNIPPET"

# 2. System packages Blender needs headless
if command -v apt-get >/dev/null; then
  NEED=""
  for p in libxi6 libxxf86vm1 libxfixes3 libxrender1 libgl1 libxkbcommon0 libsm6 xz-utils git-lfs; do
    dpkg -s "$p" >/dev/null 2>&1 || NEED="$NEED $p"
  done
  if [ -n "$NEED" ]; then
    apt-get update -y && apt-get install -y --no-install-recommends $NEED
  fi
fi

# 3. Python venv that can see the template's preinstalled torch
if [ ! -d "$VENV" ]; then
  python3 -m venv --system-site-packages "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip >/dev/null
python -m pip install -e "$REPO_DIR[dev]"

# 4. Blender
bash "$REPO_DIR/scripts/install_blender.sh"

echo
echo "== done. Open a NEW terminal (or run: source $PROFILE_SNIPPET), then: =="
echo "   bash scripts/doctor.sh"
