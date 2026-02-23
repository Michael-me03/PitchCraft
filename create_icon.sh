#!/bin/bash
# ============================================================================
# create_icon.sh — Generate AppIcon.icns from icon.svg
#
# Requires: macOS (uses built-in sips + iconutil)
# Usage:    ./create_icon.sh
# Output:   PitchCraft.app/Contents/Resources/AppIcon.icns
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SVG="$SCRIPT_DIR/icon.svg"
ICONSET="$SCRIPT_DIR/AppIcon.iconset"
ICNS_DEST="$SCRIPT_DIR/PitchCraft.app/Contents/Resources/AppIcon.icns"

# Convert SVG → 1024×1024 PNG via Safari/qlmanage
echo "Converting SVG to PNG..."
TMPNG="$SCRIPT_DIR/icon_tmp_1024.png"
qlmanage -t -s 1024 -o "$SCRIPT_DIR" "$SVG" 2>/dev/null
mv "$SCRIPT_DIR/icon.svg.png" "$TMPNG" 2>/dev/null || \
  sips -s format png "$SVG" --out "$TMPNG" --resampleWidth 1024 2>/dev/null || {
    echo "Error: Could not convert SVG. Install Inkscape or use sips with a PNG source."
    exit 1
  }

# Build iconset at all required sizes
mkdir -p "$ICONSET"
echo "Building iconset..."
for SIZE in 16 32 64 128 256 512; do
  sips -s format png "$TMPNG" --out "$ICONSET/icon_${SIZE}x${SIZE}.png"       --resampleWidth $SIZE       2>/dev/null
  DOUBLE=$((SIZE * 2))
  sips -s format png "$TMPNG" --out "$ICONSET/icon_${SIZE}x${SIZE}@2x.png"    --resampleWidth $DOUBLE    2>/dev/null
done

# Build .icns
mkdir -p "$(dirname "$ICNS_DEST")"
iconutil -c icns "$ICONSET" -o "$ICNS_DEST"
echo "Icon created: $ICNS_DEST"

# Cleanup
rm -rf "$ICONSET" "$TMPNG"

# Refresh the .app icon in Finder
touch "$SCRIPT_DIR/PitchCraft.app"
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
  -f "$SCRIPT_DIR/PitchCraft.app" 2>/dev/null || true

echo "Done. The PitchCraft.app icon has been updated."
