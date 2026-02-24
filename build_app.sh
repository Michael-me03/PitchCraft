#!/bin/bash
# ============================================================================
# build_app.sh — Build PitchCraft Electron App + DMG
# ============================================================================
# Run once to produce a fully self-contained macOS Electron app:
#
#   chmod +x build_app.sh && ./build_app.sh
#
# Output:  dist-electron/PitchCraft-1.0.0.dmg
# Requires: macOS, Python 3.11+, Node 18+
# ============================================================================

set -euo pipefail

BOLD="\033[1m"; TEAL="\033[36m"; GREEN="\033[32m"
RED="\033[31m"; YELLOW="\033[33m"; RESET="\033[0m"

ROOT="$(cd "$(dirname "$0")" && pwd)"

step() { echo -e "\n${BOLD}${TEAL}▶  $1${RESET}"; }
ok()   { echo -e "  ${GREEN}✓${RESET}  $1"; }
warn() { echo -e "  ${YELLOW}⚠${RESET}   $1"; }
die()  { echo -e "  ${RED}✗  $1${RESET}"; exit 1; }

echo -e "${TEAL}${BOLD}"
echo "  ╔════════════════════════════════════════════╗"
echo "  ║   PitchCraft  ·  Electron Builder  v1.0   ║"
echo "  ╚════════════════════════════════════════════╝"
echo -e "${RESET}"

# ── Prerequisites ─────────────────────────────────────────────────────────────
step "Checking prerequisites"
command -v python3 &>/dev/null || die "Python 3 required — install from python.org"
command -v node    &>/dev/null || die "Node.js 18+ required — install from nodejs.org"
command -v npm     &>/dev/null || die "npm required"
ok "Python $(python3 --version | cut -d' ' -f2)"
ok "Node $(node -v) / npm $(npm -v)"

# ── Step 1: Build React frontend ──────────────────────────────────────────────
step "Building React frontend"
cd "$ROOT/frontend"
npm install --silent
npm run build
ok "Built → frontend/dist/  ($(du -sh dist | cut -f1))"

# ── Step 2: Install Python dependencies into Electron resources ───────────────
step "Setting up bundled Python environment"
VENV="$ROOT/electron/resources/venv"

if [ -d "$VENV" ]; then
  warn "Existing venv found — upgrading packages"
else
  python3 -m venv "$VENV"
  ok "Virtual environment created"
fi

"$VENV/bin/pip" install --upgrade pip --quiet
"$VENV/bin/pip" install -r "$ROOT/backend/requirements.txt" --quiet
ok "Dependencies installed  ($(du -sh "$VENV" | cut -f1))"

# ── Step 2b: Make venv fully portable (replace symlinks with real binaries) ──
step "Making Python venv self-contained (portable)"

# Replace all Python symlinks in bin/ with copies of the real binary
REAL_PYTHON="$(readlink -f "$VENV/bin/python3" 2>/dev/null || python3 -c 'import sys; print(sys.executable)')"
if [ ! -f "$REAL_PYTHON" ]; then
  die "Cannot find real Python binary to bundle"
fi

# Remove symlinks and copy the actual binary
for LINK in "$VENV/bin/python" "$VENV/bin/python3" "$VENV/bin/python3."*; do
  [ -e "$LINK" ] || continue
  rm -f "$LINK"
done
cp "$REAL_PYTHON" "$VENV/bin/python3"
chmod +x "$VENV/bin/python3"
# Create python -> python3 hardlink
ln -f "$VENV/bin/python3" "$VENV/bin/python"
ok "Real Python binary copied ($(du -sh "$VENV/bin/python3" | cut -f1))"

# Copy Python standard library into the venv so it's fully standalone
SYS_PREFIX="$(python3 -c 'import sys; print(sys.prefix)')"
PYVER_SHORT="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
SYS_LIB="$SYS_PREFIX/lib/python${PYVER_SHORT}"

if [ -d "$SYS_LIB" ]; then
  VENV_LIB="$VENV/lib/python${PYVER_SHORT}"
  # Copy standard library modules that aren't already present
  rsync -a --ignore-existing "$SYS_LIB/" "$VENV_LIB/" 2>/dev/null || true
  ok "Standard library bundled"
fi

# Patch pyvenv.cfg — point home to venv's own bin so no external Python needed
cat > "$VENV/pyvenv.cfg" <<PYCFG
home = ${VENV}/bin
include-system-site-packages = false
version = ${PYVER_SHORT}
PYCFG
ok "pyvenv.cfg patched for portability"

# ── Step 3: Copy icon to Electron assets ─────────────────────────────────────
step "Preparing Electron assets"
mkdir -p "$ROOT/electron/assets"

if [ -f "$ROOT/PitchCraft.app/Contents/Resources/AppIcon.icns" ]; then
  cp "$ROOT/PitchCraft.app/Contents/Resources/AppIcon.icns" \
     "$ROOT/electron/assets/AppIcon.icns"
  ok "AppIcon.icns copied"
elif [ -f "$ROOT/icon.svg" ]; then
  warn "No .icns found — regenerating from icon.svg"
  bash "$ROOT/create_icon.sh" 2>/dev/null || true
  cp "$ROOT/PitchCraft.app/Contents/Resources/AppIcon.icns" \
     "$ROOT/electron/assets/AppIcon.icns" 2>/dev/null || warn "Icon generation failed"
fi

# ── Step 4: Install Electron dependencies ─────────────────────────────────────
step "Installing Electron & electron-builder"
cd "$ROOT/electron"
npm install --silent
ok "node_modules ready"

# ── Step 5: Build with electron-builder ──────────────────────────────────────
step "Building with electron-builder (this takes a minute...)"
npm run build
echo ""

# ── Step 6: Report ────────────────────────────────────────────────────────────
DMG=$(ls "$ROOT/dist-electron/"*.dmg 2>/dev/null | head -1)

if [ -n "$DMG" ]; then
  SIZE=$(du -sh "$DMG" | cut -f1)
  echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════╗"
  echo   "║           Build complete! 🎉                ║"
  echo -e "╚══════════════════════════════════════════════╝${RESET}"
  echo ""
  echo -e "  DMG:  ${BOLD}$(basename "$DMG")${RESET}  (${SIZE})"
  echo "  Path: $DMG"
  echo ""
  echo "  Install: double-click the DMG, drag to Applications"
  echo "  First launch: enter your OpenAI API key"
  echo ""
  open -R "$DMG" 2>/dev/null || true
else
  warn "DMG not found in dist-electron/ — check output above"
fi
