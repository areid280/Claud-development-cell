#!/usr/bin/env bash
# Environment report. Paste the output into task logs or escalations.
set -uo pipefail
echo "== system =="
uname -a
echo "date: $(date -u +%FT%TZ)"
echo
echo "== gpu =="
if command -v nvidia-smi >/dev/null; then
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
else
  echo "nvidia-smi not found"
fi
echo
echo "== disk (/workspace) =="
df -h /workspace 2>/dev/null || df -h .
echo
echo "== blender =="
if command -v blender >/dev/null; then blender --background --version 2>/dev/null | head -n 1; else echo "blender not on PATH"; fi
echo
echo "== python / avatar-forge =="
command -v avatar-forge >/dev/null && avatar-forge doctor || echo "avatar-forge not installed (run scripts/setup_pod.sh)"
