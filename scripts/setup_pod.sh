#!/usr/bin/env bash
# Idempotent setup on a RunPod PyTorch pod. Run from the repo root after every new pod:
#   bash scripts/setup_pod.sh
#
# Layout (D-006): /workspace is a RunPod network volume (geesefs). It survives pods but cannot
# hold executables or change file permissions, so it keeps DATA only. Code, venv and Blender
# live on the pod's local disk and are rebuilt here (fast: downloads are cached on the volume).
#   /workspace/weights, cache/{hf,torch,pip}, downloads/, jobs/, git/   <- persistent data
#   ~/avatar-forge (git clone), /opt/venv-af, /opt/tools/blender        <- rebuilt per pod
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WS="/workspace"
VENV="/opt/venv-af"

echo "== avatar-forge pod setup =="
echo "repo: $REPO_DIR"
case "$REPO_DIR" in
  "$WS"/*) echo "ERROR: the repo must not live on $WS (no chmod/exec there). Clone it to ~/avatar-forge." >&2; exit 1 ;;
esac

# 1. Persistent data locations on the volume
mkdir -p "$WS/weights" "$WS/cache/hf" "$WS/cache/pip" "$WS/cache/torch" "$WS/downloads" "$WS/jobs" "$WS/git"
PROFILE_SNIPPET="$HOME/.avatar_forge_env"
cat > "$PROFILE_SNIPPET" <<EOF
export AF_WEIGHTS_DIR=$WS/weights
export AF_JOBS_DIR=$WS/jobs
export HF_HOME=$WS/cache/hf
export PIP_CACHE_DIR=$WS/cache/pip
export TORCH_HOME=$WS/cache/torch
export PATH=/opt/tools/blender:\$PATH
if [ -f $VENV/bin/activate ]; then source $VENV/bin/activate; fi
EOF
# jobs/ is git-ignored; link it so job outputs on the volume show in the VS Code Explorer
[ -e "$REPO_DIR/jobs" ] || ln -s "$WS/jobs" "$REPO_DIR/jobs"
grep -qxF "source $PROFILE_SNIPPET" "$HOME/.bashrc" || echo "source $PROFILE_SNIPPET" >> "$HOME/.bashrc"
# shellcheck disable=SC1090
source "$PROFILE_SNIPPET"

# 2. Git: settings in ~/.gitconfig (local disk), identity + saved token kept on the volume
if [ -f "$WS/git/identity" ]; then
  # file format: two lines, "name=<Your Name>" and "email=<you@example.com>"
  git config --global user.name "$(sed -n 's/^name=//p' "$WS/git/identity")"
  git config --global user.email "$(sed -n 's/^email=//p' "$WS/git/identity")"
fi
git config --global credential.helper "store --file=$WS/git/credentials"
git config --global pull.rebase false

# 3. System packages Blender needs headless
if command -v apt-get >/dev/null; then
  NEED=""
  for p in libxi6 libxxf86vm1 libxfixes3 libxrender1 libgl1 libxkbcommon0 libsm6 xz-utils git-lfs; do
    dpkg -s "$p" >/dev/null 2>&1 || NEED="$NEED $p"
  done
  if [ -n "$NEED" ]; then
    apt-get update -y && apt-get install -y --no-install-recommends $NEED
  fi
fi

# 4. Python venv (local disk) that can see the template's preinstalled torch
if [ ! -d "$VENV" ]; then
  python3 -m venv --system-site-packages "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip >/dev/null
python -m pip install -e "$REPO_DIR[dev,models]"

# 5. Blender (tarball cached on the volume, unpacked to local disk)
bash "$REPO_DIR/scripts/install_blender.sh"

echo
echo "== done. Open a NEW terminal (or run: source $PROFILE_SNIPPET), then: =="
echo "   bash scripts/doctor.sh"
