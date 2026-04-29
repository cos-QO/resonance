#!/usr/bin/env bash
# setup.sh — Resonance environment setup
#
# Usage:
#   ./setup.sh              first-time setup
#   ./setup.sh overwrite    redo from scratch (re-enter all credentials)
#   ./setup.sh update       update one or more API keys interactively
#   ./setup.sh wipe         remove .env and clear all runtime state

set -uo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'

ok()     { echo -e "${GREEN}✓${RESET}  $*"; }
fail()   { echo -e "${RED}✗${RESET}  $*" >&2; }
info()   { echo -e "${CYAN}→${RESET}  $*"; }
warn()   { echo -e "${YELLOW}⚠${RESET}  $*"; }
header() { echo -e "\n${BOLD}$*${RESET}\n"; }
dim()    { echo -e "${DIM}$*${RESET}"; }

# ── Helpers ───────────────────────────────────────────────────────────────────

VENV_DIR="$PWD/.venv"

find_python() {
  for cmd in python3.13 python3.12 python3.11; do
    if command -v "$cmd" &>/dev/null; then
      ver=$("$cmd" -c "import sys; print(sys.version_info >= (3,11))" 2>/dev/null)
      if [[ "$ver" == "True" ]]; then
        echo "$cmd"; return 0
      fi
    fi
  done
  fail "Python 3.11+ not found. Install via: brew install python@3.11"
  exit 1
}

ensure_venv() {
  local py
  py=$(find_python)
  if [[ ! -d "$VENV_DIR" ]]; then
    info "Creating virtual environment..."
    "$py" -m venv "$VENV_DIR"
    ok "Created .venv"
  fi
  # Prepend venv to PATH so 'resonance' and 'python3' resolve to venv versions
  export PATH="$VENV_DIR/bin:$PATH"
}

ensure_resonance() {
  ensure_venv
  if ! command -v resonance &>/dev/null; then
    info "Installing resonance..."
    "$VENV_DIR/bin/python" -m pip install -e . -q
    ok "Installed"
  fi
}

# Update or insert a key=value in .env (uses stdlib only — works with any Python)
set_env_key() {
  local key="$1" value="$2"
  python3 - "$key" "$value" <<'PYEOF'
import sys, re
key, value = sys.argv[1], sys.argv[2]
try:
    content = open('.env').read()
except FileNotFoundError:
    content = ''
pattern = rf'^{re.escape(key)}=.*'
replacement = f'{key}={value}'
if re.search(pattern, content, flags=re.MULTILINE):
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
else:
    content = content.rstrip('\n') + f'\n{replacement}\n'
open('.env', 'w').write(content)
PYEOF
}

get_env_key() {
  local key="$1"
  grep "^${key}=" .env 2>/dev/null | cut -d= -f2- || echo ""
}

# ── Modes ─────────────────────────────────────────────────────────────────────

do_setup() {
  header "Resonance Setup"
  ensure_resonance
  resonance setup
}

do_overwrite() {
  header "Resonance Setup — Overwrite"
  warn "This will replace your existing credentials."
  read -rp "  Continue? [y/N] " confirm
  echo ""
  [[ "$confirm" =~ ^[Yy]$ ]] || { info "Cancelled."; exit 0; }

  ensure_resonance
  rm -f .env
  resonance setup
}

do_update() {
  header "Update Configuration"

  if [[ ! -f .env ]]; then
    fail ".env not found — run ./setup.sh first."
    exit 1
  fi

  ensure_resonance

  KEYS=("LINEAR_API_KEY" "LINEAR_TEAM_ID" "FIGMA_API_KEY" "GITHUB_TOKEN")
  DESCS=(
    "Linear personal API key  (Settings → API → Personal API keys)"
    "Linear team UUID         (from resonance setup or your Linear team URL)"
    "Figma API key            (optional — required for design_to_code tasks)"
    "GitHub token             (optional — required for PR creation, Milestone 3)"
  )

  while true; do
    echo -e "${BOLD}What would you like to update?${RESET}"
    for i in "${!KEYS[@]}"; do
      current=$(get_env_key "${KEYS[$i]}")
      masked="${current:0:8}…"
      [[ -z "$current" ]] && masked="(not set)"
      printf "  %d)  %-22s  %s\n" "$((i+1))" "${KEYS[$i]}" "${DIM}${DESCS[$i]}${RESET}"
      printf "       %-22s  current: %s\n" "" "${DIM}${masked}${RESET}"
      echo ""
    done
    echo -e "  5)  ${BOLD}Fix Linear labels / states${RESET}  ${DIM}Create missing 'plan', 'backend', and other required items${RESET}"
    echo ""
    echo -e "  q)  Done\n"
    read -rp "Choice: " choice
    echo ""

    case "$choice" in
      1|2|3|4)
        idx=$((choice - 1))
        key="${KEYS[$idx]}"
        read -rp "  New value for ${key}: " new_value
        echo ""
        if [[ -z "$new_value" ]]; then
          warn "Empty value — skipping ${key}."
        else
          set_env_key "$key" "$new_value"
          ok "Updated ${key}"
        fi
        echo ""
        ;;
      5)
        echo ""
        info "Creating missing Linear labels and workflow states..."
        echo ""
        resonance fix
        echo ""
        ;;
      q|Q|"")
        break
        ;;
      *)
        warn "Invalid choice — enter 1–5 or q."
        echo ""
        ;;
    esac
  done

  info "Running doctor to verify..."
  echo ""
  resonance doctor || true
}

do_wipe() {
  header "Wipe Setup"
  echo "  This will remove:"
  echo "    • .env  (all credentials)"
  echo "    • runs/state.json"
  echo "    • runs/events.jsonl"
  echo "    • runs/commands.jsonl"
  echo "    • runs/logs/"
  echo ""
  warn "Active runs will be lost. Git worktrees in workspaces/ are preserved."
  echo ""
  read -rp "  Continue? [y/N] " confirm
  echo ""
  [[ "$confirm" =~ ^[Yy]$ ]] || { info "Cancelled."; exit 0; }

  rm -f .env
  rm -f runs/state.json runs/events.jsonl runs/commands.jsonl
  rm -rf runs/logs/
  ok "Credentials and runtime state removed."
  dim "  → Run ./setup.sh to configure again."
  echo ""
}

# ── Entry point ───────────────────────────────────────────────────────────────

MODE="${1:-setup}"

case "$MODE" in
  setup)     do_setup    ;;
  overwrite) do_overwrite ;;
  update)    do_update   ;;
  wipe)      do_wipe     ;;
  *)
    echo ""
    echo -e "${BOLD}Resonance setup utility${RESET}"
    echo ""
    echo "  Usage: ./setup.sh [mode]"
    echo ""
    echo "  Modes:"
    echo "    setup      First-time setup — install, configure, create Linear states/labels"
    echo "    overwrite  Redo everything — replace all credentials"
    echo "    update     Update one or more API keys without touching the rest"
    echo "    wipe       Remove .env and clear all runtime state (worktrees preserved)"
    echo ""
    exit 1
    ;;
esac
