#!/bin/bash
# ============================================================================
# PitchCraft — Install & Run Script
# ============================================================================
# Usage:
#   chmod +x install.sh && ./install.sh
#
# What this does:
#   1. Checks for Docker (recommended) or Python/Node (fallback)
#   2. Sets up the .env file with your OpenAI API key
#   3. Builds and starts the app
#   4. Opens http://localhost:3000 in your browser
# ============================================================================

set -euo pipefail

BOLD="\033[1m"
TEAL="\033[36m"
GREEN="\033[32m"
RED="\033[31m"
YELLOW="\033[33m"
RESET="\033[0m"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo -e "${TEAL}${BOLD}"
echo "  ██████╗ ██╗████████╗ ██████╗██╗  ██╗ ██████╗██████╗  █████╗ ███████╗████████╗"
echo "  ██╔══██╗██║╚══██╔══╝██╔════╝██║  ██║██╔════╝██╔══██╗██╔══██╗██╔════╝╚══██╔══╝"
echo "  ██████╔╝██║   ██║   ██║     ███████║██║     ██████╔╝███████║█████╗     ██║   "
echo "  ██╔═══╝ ██║   ██║   ██║     ██╔══██║██║     ██╔══██╗██╔══██║██╔══╝     ██║   "
echo "  ██║     ██║   ██║   ╚██████╗██║  ██║╚██████╗██║  ██║██║  ██║██║        ██║   "
echo "  ╚═╝     ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝        ╚═╝   "
echo -e "${RESET}"
echo -e "  ${BOLD}AI Presentation Engine${RESET} — Turn your template into a boardroom deck in seconds"
echo ""

# ── Step 1: Check prerequisites ───────────────────────────────────────────────
echo -e "${BOLD}[1/4] Checking prerequisites...${RESET}"

USE_DOCKER=false
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    USE_DOCKER=true
    echo -e "  ${GREEN}✓${RESET} Docker found — using containerised setup (recommended)"
elif command -v docker &>/dev/null; then
    echo -e "  ${YELLOW}⚠${RESET}  Docker found but not running — attempting to start..."
    open -a "Docker Desktop" 2>/dev/null || open -a "Docker" 2>/dev/null || true
    for i in $(seq 1 30); do
        sleep 1
        docker info &>/dev/null 2>&1 && { USE_DOCKER=true; break; }
    done
    if $USE_DOCKER; then
        echo -e "  ${GREEN}✓${RESET} Docker started"
    else
        echo -e "  ${YELLOW}⚠${RESET}  Docker not ready — falling back to manual setup"
    fi
fi

if ! $USE_DOCKER; then
    echo ""
    echo -e "  ${YELLOW}Docker not available — using local Python/Node setup${RESET}"
    command -v python3 &>/dev/null || { echo -e "  ${RED}✗ Python 3 required. Install from python.org${RESET}"; exit 1; }
    command -v node &>/dev/null    || { echo -e "  ${RED}✗ Node.js required. Install from nodejs.org${RESET}"; exit 1; }
    echo -e "  ${GREEN}✓${RESET} Python $(python3 --version | cut -d' ' -f2) and Node $(node -v) found"
fi

# ── Step 2: API Key ───────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[2/4] OpenAI API Key${RESET}"

if [ -f "$SCRIPT_DIR/backend/.env" ] && grep -q "OPENAI_API_KEY=sk-" "$SCRIPT_DIR/backend/.env" 2>/dev/null; then
    echo -e "  ${GREEN}✓${RESET} API key already configured in backend/.env"
else
    echo -e "  Enter your OpenAI API key (starts with sk-...):"
    echo -n "  > "
    read -r API_KEY
    if [ -z "$API_KEY" ]; then
        echo -e "  ${RED}✗ No API key provided. Exiting.${RESET}"
        exit 1
    fi
    echo "OPENAI_API_KEY=$API_KEY" > "$SCRIPT_DIR/backend/.env"
    echo -e "  ${GREEN}✓${RESET} Saved to backend/.env"
fi

# ── Step 3: Build ─────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[3/4] Building...${RESET}"

if $USE_DOCKER; then
    echo -e "  Building Docker containers (first run ~2 min)..."
    cd "$SCRIPT_DIR"
    docker compose build --quiet
    echo -e "  ${GREEN}✓${RESET} Containers built"
else
    # Backend
    echo -e "  Setting up Python virtual environment..."
    cd "$SCRIPT_DIR/backend"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q -r requirements.txt
    echo -e "  ${GREEN}✓${RESET} Backend dependencies installed"

    # Frontend
    echo -e "  Installing Node packages..."
    cd "$SCRIPT_DIR/frontend"
    npm install --silent
    npm run build
    echo -e "  ${GREEN}✓${RESET} Frontend built"
fi

# ── Step 4: Start ─────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[4/4] Starting PitchCraft...${RESET}"

if $USE_DOCKER; then
    cd "$SCRIPT_DIR"
    docker compose up -d
    echo -e "  Waiting for backend to be ready..."
    for i in $(seq 1 60); do
        sleep 1
        curl -sf http://localhost:8000/api/health &>/dev/null && break
    done
    echo -e "  ${GREEN}✓${RESET} PitchCraft is running"
    echo ""
    echo -e "  ${TEAL}${BOLD}→ Open http://localhost:3000 in your browser${RESET}"
    open "http://localhost:3000" 2>/dev/null || true
else
    # Start backend in background
    cd "$SCRIPT_DIR/backend"
    source .venv/bin/activate
    uvicorn main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!

    # Serve pre-built frontend with a simple Python server
    cd "$SCRIPT_DIR/frontend"
    python3 -m http.server 3000 --directory dist &
    FRONTEND_PID=$!

    echo -e "  ${GREEN}✓${RESET} PitchCraft running (backend PID $BACKEND_PID, frontend PID $FRONTEND_PID)"
    echo ""
    echo -e "  ${TEAL}${BOLD}→ Open http://localhost:3000 in your browser${RESET}"
    echo -e "  ${YELLOW}Press Ctrl+C to stop${RESET}"
    open "http://localhost:3000" 2>/dev/null || true

    # Keep script alive
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'PitchCraft stopped.'" EXIT
    wait
fi

echo ""
echo -e "${GREEN}${BOLD}Setup complete!${RESET}"
echo ""
echo "  Stop:    docker compose down"
echo "  Logs:    docker compose logs -f"
echo "  Restart: docker compose restart"
echo "  Update:  git pull && docker compose up -d --build"
echo ""
