#!/usr/bin/env bash
# Install Blender (headless use) into /workspace/tools/blender. Idempotent.
# Version is pinned so results are reproducible; change only at a gate.
set -euo pipefail

BLENDER_VERSION="4.2.3"          # LTS line; gatekeeper may bump at G0
SERIES="${BLENDER_VERSION%.*}"
DEST="/workspace/tools/blender"
URL="https://download.blender.org/release/Blender${SERIES}/blender-${BLENDER_VERSION}-linux-x64.tar.xz"

if [ -x "$DEST/blender" ] && "$DEST/blender" --version 2>/dev/null | grep -q "Blender ${BLENDER_VERSION}"; then
  echo "Blender ${BLENDER_VERSION} already installed at $DEST"
  exit 0
fi

mkdir -p /workspace/tools
TMP="$(mktemp -d)"
echo "Downloading Blender ${BLENDER_VERSION}..."
curl -fL --retry 3 -o "$TMP/blender.tar.xz" "$URL"
tar -xf "$TMP/blender.tar.xz" -C "$TMP"
rm -rf "$DEST"
mv "$TMP/blender-${BLENDER_VERSION}-linux-x64" "$DEST"
rm -rf "$TMP"
"$DEST/blender" --background --version | head -n 1
