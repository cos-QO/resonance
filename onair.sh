#!/usr/bin/env bash
# onair.sh — Start Resonance
#
# Verifies setup, then starts the orchestrator and dashboard.
# Milestone 2: once the TUI is built, this script will launch it
# alongside the orchestrator and tear both down on exit.

set -uo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'

ok()   { echo -e "${GREEN}✓${RESET}  $*"; }
fail() { echo -e "${RED}✗${RESET}  $*" >&2; }
info() { echo -e "${CYAN}→${RESET}  $*"; }
warn() { echo -e "${YELLOW}⚠${RESET}  $*"; }

# ── Pre-flight ────────────────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}Resonance${RESET}"
echo ""

# .env must exist
if [[ ! -f .env ]]; then
  fail ".env not found."
  echo -e "       Run ${BOLD}./setup.sh${RESET} to configure."
  echo ""
  exit 1
fi

# resonance CLI must be installed
if ! command -v resonance &>/dev/null; then
  info "resonance not installed — installing now..."
  for cmd in python3.13 python3.12 python3.11; do
    if command -v "$cmd" &>/dev/null; then
      "$cmd" -m pip install -e . -q && break
    fi
  done
  if ! command -v resonance &>/dev/null; then
    fail "Install failed. Run: pip install -e ."
    exit 1
  fi
  ok "Installed"
fi

# claude CLI must be present (the orchestrator launches it as a subprocess)
if ! command -v claude &>/dev/null; then
  fail "claude CLI not found."
  echo -e "       Install from ${DIM}https://claude.ai/code${RESET} then re-run."
  echo ""
  exit 1
fi

# Health check
info "Running doctor..."
echo ""
if ! resonance doctor; then
  echo ""
  fail "Doctor checks failed — fix the issues above then re-run."
  echo -e "       Run ${BOLD}./setup.sh update${RESET} to change a credential."
  echo ""
  exit 1
fi

# ── Launch ────────────────────────────────────────────────────────────────────

echo ""
ok "All checks passed."
echo ""
echo -e "  ${DIM}Ctrl+C to stop${RESET}"
echo ""

# ── Milestone 2: TUI dashboard ────────────────────────────────────────────────
# When tui/app.py is implemented, replace the block below with:
#
#   ORCHESTRATOR_PID=""
#   cleanup() {
#     echo ""; info "Shutting down..."
#     [[ -n "$ORCHESTRATOR_PID" ]] && kill "$ORCHESTRATOR_PID" 2>/dev/null
#   }
#   trap cleanup INT TERM EXIT
#
#   python -m orchestrator.main &
#   ORCHESTRATOR_PID=$!
#   python -m tui.app          # foreground — blocks until user quits
#
# Until then the orchestrator runs in the foreground.

cleanup() {
  echo ""
  info "Resonance stopped."
  echo ""
}
trap cleanup INT TERM

python -m orchestrator.main
