#!/usr/bin/env bash
# Install Blender (headless use) into /opt/tools/blender. Idempotent.
# The download is cached on the network volume (/workspace/downloads) so new pods only unpack it;
# the binary itself must be on local disk because the volume cannot execute files (D-006).
# Version is pinned so results are reproducible; change only at a gate.
set -euo pipefail

BLENDER_VERSION="4.2.3"          # LTS line; gatekeeper may bump at a gate
SERIES="${BLENDER_VERSION%.*}"
DEST="/opt/tools/blender"
CACHE="/workspace/downloads/blender-${BLENDER_VERSION}-linux-x64.tar.xz"
URL="https://download.blender.org/release/Blender${SERIES}/blender-${BLENDER_VERSION}-linux-x64.tar.xz"

if [ -x "$DEST/blender" ] && "$DEST/blender" --version 2>/dev/null | grep -q "Blender ${BLENDER_VERSION}"; then
  echo "Blender ${BLENDER_VERSION} already installed at $DEST"
  exit 0
fi

mkdir -p "$(dirname "$CACHE")" /opt/tools
if [ ! -s "$CACHE" ]; then
  echo "Downloading Blender ${BLENDER_VERSION} (cached for future pods)..."
  curl -fL --retry 3 -o "$CACHE.part" "$URL"
  mv "$CACHE.part" "$CACHE"
else
  echo "Using cached Blender download: $CACHE"
fi
TMP="$(mktemp -d)"
tar -xf "$CACHE" -C "$TMP"
rm -rf "$DEST"
mv "$TMP/blender-${BLENDER_VERSION}-linux-x64" "$DEST"
rm -rf "$TMP"
"$DEST/blender" --background --version | head -n 1
