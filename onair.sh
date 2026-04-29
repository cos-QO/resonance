#!/usr/bin/env bash
# onair.sh — Start Resonance
#
# Usage:
#   ./onair.sh                         start normally (uses configured project)
#   ./onair.sh --project               pick a project interactively before starting
#   ./onair.sh --project <url-or-id>   set a specific project then start
#   ./onair.sh --clear-project         remove project scope (watch all team issues)

set -uo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'

ok()   { echo -e "${GREEN}✓${RESET}  $*"; }
fail() { echo -e "${RED}✗${RESET}  $*" >&2; }
info() { echo -e "${CYAN}→${RESET}  $*"; }
warn() { echo -e "${YELLOW}⚠${RESET}  $*"; }

echo ""
echo -e "${BOLD}Resonance${RESET}"
echo ""

# ── Argument parsing ──────────────────────────────────────────────────────────

SET_PROJECT=""      # "" = no change, "interactive" = pick from list, else = URL/UUID
CLEAR_PROJECT=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project|-p)
      if [[ -n "${2:-}" && "$2" != --* ]]; then
        SET_PROJECT="$2"; shift 2
      else
        SET_PROJECT="interactive"; shift
      fi
      ;;
    --clear-project)
      CLEAR_PROJECT=true; shift ;;
    *)
      shift ;;
  esac
done

# ── Pre-flight ────────────────────────────────────────────────────────────────

if [[ ! -f .env ]]; then
  fail ".env not found."
  echo -e "       Run ${BOLD}./setup.sh${RESET} to configure."
  echo ""
  exit 1
fi

if ! command -v claude &>/dev/null; then
  fail "claude CLI not found."
  echo -e "       Install from ${DIM}https://claude.ai/code${RESET} then re-run."
  echo ""
  exit 1
fi

# ── Find Python 3.11+ ─────────────────────────────────────────────────────────

SYSTEM_PYTHON=""
for cmd in python3.13 python3.12 python3.11 python3 python; do
  if command -v "$cmd" &>/dev/null; then
    ver=$("$cmd" -c "import sys; print(sys.version_info >= (3,11))" 2>/dev/null)
    if [[ "$ver" == "True" ]]; then
      SYSTEM_PYTHON="$cmd"; break
    fi
  fi
done
if [[ -z "$SYSTEM_PYTHON" ]]; then
  fail "Python 3.11+ not found. Install via: brew install python@3.11"
  exit 1
fi

# ── Create / reuse virtual environment ───────────────────────────────────────

VENV_DIR="$PWD/.venv"

if [[ ! -d "$VENV_DIR" ]]; then
  info "Creating virtual environment..."
  "$SYSTEM_PYTHON" -m venv "$VENV_DIR"
  ok "Created .venv"
fi

PYTHON="$VENV_DIR/bin/python"
RESONANCE_CMD="$VENV_DIR/bin/resonance"

ok "Using $($PYTHON --version)"

# ── Install dependencies into venv ───────────────────────────────────────────

if ! "$PYTHON" -c "import yaml, httpx, typer, rich, textual" 2>/dev/null; then
  info "Installing dependencies..."
  "$PYTHON" -m pip install -e . -q
  ok "Dependencies installed"
fi

if [[ ! -f "$RESONANCE_CMD" ]]; then
  "$PYTHON" -m pip install -e . -q
fi

# ── Project selection ─────────────────────────────────────────────────────────

if [[ "$CLEAR_PROJECT" == "true" ]]; then
  echo ""
  info "Clearing project scope..."
  "$RESONANCE_CMD" project set "" 2>/dev/null || true
  # Manually remove key from .env if CLI fails
  if grep -q "^LINEAR_PROJECT_ID=" .env 2>/dev/null; then
    sed -i.bak '/^LINEAR_PROJECT_ID=/d' .env && rm -f .env.bak
    ok "Project scope cleared — watching all team issues"
  else
    ok "No project scope was set"
  fi
  echo ""

elif [[ "$SET_PROJECT" == "interactive" ]]; then
  echo ""
  info "Select a project to scope Resonance to:"
  echo ""
  if ! "$RESONANCE_CMD" project set; then
    echo ""
    fail "Project selection failed."
    exit 1
  fi
  echo ""

elif [[ -n "$SET_PROJECT" ]]; then
  echo ""
  info "Setting project: $SET_PROJECT"
  if ! "$RESONANCE_CMD" project set "$SET_PROJECT"; then
    echo ""
    fail "Could not resolve project. Use a Linear project URL or UUID."
    echo -e "       Example: ${DIM}./onair.sh --project https://linear.app/…/project/my-project-abc123${RESET}"
    echo ""
    exit 1
  fi
  echo ""
fi

# ── Health check ──────────────────────────────────────────────────────────────

info "Running doctor..."
echo ""
if ! "$RESONANCE_CMD" doctor; then
  echo ""
  info "Auto-fixing what I can (missing labels and workflow states)..."
  echo ""
  "$RESONANCE_CMD" fix

  echo ""
  info "Re-checking..."
  echo ""
  if ! "$RESONANCE_CMD" doctor; then
    echo ""
    fail "Setup incomplete — some items need manual action (see above)."
    echo ""
    echo -e "       ${BOLD}What to do:${RESET}"
    echo -e "       ${DIM}• Missing credentials  →  run ${BOLD}resonance setup${RESET}"
    echo -e "       ${DIM}• Missing Linear states/labels that couldn't be created${RESET}"
    echo -e "         ${DIM}→  create them in Linear → Settings, then re-run ${BOLD}./onair.sh${RESET}"
    echo ""
    exit 1
  fi
fi

echo ""
ok "All checks passed."
echo ""

# ── Project scope (after doctor so credentials are confirmed) ─────────────────

_read_project_id() {
  grep "^LINEAR_PROJECT_ID=" .env 2>/dev/null | cut -d= -f2 | tr -d '[:space:]'
}

PROJECT_ID="$(_read_project_id)"

if [[ -n "$PROJECT_ID" ]]; then
  # Already set — look up the name and confirm
  PROJECT_NAME=$("$RESONANCE_CMD" project list 2>/dev/null \
    | grep -o "[a-f0-9-]\{8\}[^ ]*" | head -1 || echo "")
  info "Project: ${CYAN}${PROJECT_ID:0:8}…${RESET}"
  echo ""
else
  # Not set — interactive prompt
  echo -e "  ${BOLD}Select a project${RESET}"
  echo ""
  echo -e "  ${DIM}Resonance needs to know which Linear project to watch.${RESET}"
  echo -e "  ${DIM}Pick a project below, or press Enter to watch all team issues.${RESET}"
  echo -e "  ${DIM}You can change this anytime with ${BOLD}p${RESET}${DIM} in the dashboard.${RESET}"
  echo ""
  "$RESONANCE_CMD" project set || true
  echo ""

  # Re-read after selection
  PROJECT_ID="$(_read_project_id)"
  if [[ -n "$PROJECT_ID" ]]; then
    ok "Project scope set."
  else
    warn "No project scope — watching all team issues."
  fi
  echo ""
fi

# ── Launch ────────────────────────────────────────────────────────────────────

mkdir -p runs/logs

PID_FILE="runs/orchestrator.pid"
ORCHESTRATOR_PID=""
ORCH_OWNED=false   # true only if THIS invocation started the orchestrator

# Reuse a running orchestrator rather than spawning a duplicate
if [[ -f "$PID_FILE" ]]; then
  EXISTING=$(cat "$PID_FILE" 2>/dev/null)
  if [[ -n "$EXISTING" ]] && kill -0 "$EXISTING" 2>/dev/null; then
    ok "Orchestrator already running (PID $EXISTING)"
    ORCHESTRATOR_PID="$EXISTING"
  else
    info "Stale PID file — starting fresh orchestrator..."
    rm -f "$PID_FILE"
  fi
fi

if [[ -z "$ORCHESTRATOR_PID" ]]; then
  ORCH_LOG="runs/logs/orchestrator-$(date +%Y%m%dT%H%M%S).log"
  "$PYTHON" -m orchestrator.main >> "$ORCH_LOG" 2>&1 &
  ORCHESTRATOR_PID=$!
  echo "$ORCHESTRATOR_PID" > "$PID_FILE"
  ORCH_OWNED=true
  info "Orchestrator started (PID $ORCHESTRATOR_PID, log: $ORCH_LOG)"
fi
echo ""

cleanup() {
  echo ""
  info "Shutting down..."
  if [[ "$ORCH_OWNED" == "true" && -n "$ORCHESTRATOR_PID" ]]; then
    kill "$ORCHESTRATOR_PID" 2>/dev/null
    wait "$ORCHESTRATOR_PID" 2>/dev/null || true
    rm -f "$PID_FILE"
    info "Orchestrator stopped."
  fi
  info "Resonance stopped."
  echo ""
}
trap cleanup INT TERM

"$PYTHON" -m tui.app

# TUI exited cleanly — run cleanup
cleanup
trap - INT TERM
