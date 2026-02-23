#!/bin/bash
# ============================================================================
# build_app.sh — Build PitchCraft.app and PitchCraft.dmg
# ============================================================================
# Run this script once to produce a fully self-contained macOS app:
#
#   chmod +x build_app.sh && ./build_app.sh
#
# Output:
#   PitchCraft.app   — drag to /Applications to install
#   PitchCraft.dmg   — distribute or double-click to mount and install
#
# Requirements: macOS, Python 3.11+, Node 18+
# ============================================================================

set -euo pipefail

BOLD="\033[1m"; TEAL="\033[36m"; GREEN="\033[32m"
RED="\033[31m"; YELLOW="\033[33m"; RESET="\033[0m"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$SCRIPT_DIR/PitchCraft.app"
RESOURCES="$APP/Contents/Resources"
MACOS="$APP/Contents/MacOS"

step() { echo -e "\n${BOLD}${TEAL}▶ $1${RESET}"; }
ok()   { echo -e "  ${GREEN}✓${RESET} $1"; }
warn() { echo -e "  ${YELLOW}⚠${RESET}  $1"; }
die()  { echo -e "  ${RED}✗ $1${RESET}"; exit 1; }

echo -e "${TEAL}${BOLD}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   PitchCraft  ·  App Builder  v1.0    ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${RESET}"

# ── Prerequisites ─────────────────────────────────────────────────────────────
step "Checking prerequisites"
command -v python3 &>/dev/null || die "Python 3 required — install from python.org"
command -v node    &>/dev/null || die "Node.js required — install from nodejs.org"
command -v npm     &>/dev/null || die "npm required"

PYTHON_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
ok "Python $PYTHON_VER"
ok "Node $(node -v)"

# ── Step 1: Build React frontend ──────────────────────────────────────────────
step "Building React frontend"
cd "$SCRIPT_DIR/frontend"
npm install --silent
npm run build
ok "Frontend built → frontend/dist/"

# ── Step 2: Prepare .app Resources ───────────────────────────────────────────
step "Preparing .app bundle"
mkdir -p "$RESOURCES" "$MACOS"

# Copy pre-built frontend into the bundle
rm -rf "$RESOURCES/web"
cp -r "$SCRIPT_DIR/frontend/dist" "$RESOURCES/web"
ok "Frontend copied → Resources/web/"

# Copy backend source (exclude dev artifacts)
rm -rf "$RESOURCES/backend"
rsync -a \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.venv' \
    --exclude='.env' \
    --exclude='*.pptx' \
    "$SCRIPT_DIR/backend/" "$RESOURCES/backend/"
ok "Backend copied → Resources/backend/"

# ── Step 3: Install Python dependencies into bundled venv ────────────────────
step "Installing Python dependencies into bundle"
VENV="$RESOURCES/venv"

if [ -d "$VENV" ]; then
    warn "Existing venv found — updating packages"
else
    python3 -m venv "$VENV"
    ok "Virtual environment created"
fi

"$VENV/bin/pip" install --upgrade pip --quiet
"$VENV/bin/pip" install -r "$SCRIPT_DIR/backend/requirements.txt" --quiet
ok "All dependencies installed ($(du -sh "$VENV" | cut -f1))"

# ── Step 4: Make launcher executable ─────────────────────────────────────────
chmod +x "$MACOS/PitchCraft"
ok "Launcher is executable"

# ── Step 5: Regenerate icon ───────────────────────────────────────────────────
step "Generating app icon"
if [ -f "$SCRIPT_DIR/icon.svg" ]; then
    bash "$SCRIPT_DIR/create_icon.sh" 2>/dev/null && ok "AppIcon.icns generated" || warn "Icon generation failed — using existing"
else
    warn "icon.svg not found — skipping icon generation"
fi

# ── Step 6: App bundle size report ───────────────────────────────────────────
step "Bundle size"
echo "  $(du -sh "$APP" | cut -f1)  PitchCraft.app"
echo "  $(du -sh "$VENV" | cut -f1)  └─ venv (Python dependencies)"

# ── Step 7: Create DMG ───────────────────────────────────────────────────────
step "Creating DMG"
DMG="$SCRIPT_DIR/PitchCraft.dmg"
STAGING=$(mktemp -d)

# Copy .app into staging area
cp -r "$APP" "$STAGING/"

# Add /Applications shortcut for drag-to-install UX
ln -s /Applications "$STAGING/Applications"

# Create a background-less but cleanly sized DMG
rm -f "$DMG"
hdiutil create \
    -volname "PitchCraft" \
    -srcfolder "$STAGING" \
    -ov \
    -format UDZO \
    -imagekey zlib-level=9 \
    "$DMG" \
    2>/dev/null

rm -rf "$STAGING"

DMG_SIZE=$(du -sh "$DMG" | cut -f1)
ok "PitchCraft.dmg created (${DMG_SIZE})"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════╗"
echo   "║           Build complete! 🎉             ║"
echo -e "╚══════════════════════════════════════════╝${RESET}"
echo ""
echo "  PitchCraft.app  — drag to /Applications"
echo "  PitchCraft.dmg  — share or distribute  ($DMG_SIZE)"
echo ""
echo "  First launch will ask for your OpenAI API key."
echo "  The key is stored securely in ~/.pitchcraft/"
echo ""

# Open Finder at DMG location
open -R "$DMG" 2>/dev/null || true
