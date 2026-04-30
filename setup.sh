#!/usr/bin/env bash
# setup.sh — Resonance environment setup
#
# Usage:
#   ./setup.sh              first-time setup
#   ./setup.sh check        full health-check wizard — diagnoses and auto-fixes everything
#   ./setup.sh overwrite    redo from scratch (re-enter all credentials)
#   ./setup.sh update       update one or more API keys without touching the rest
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
step()   { echo -e "\n${BOLD}${CYAN}[$1]${RESET}  ${BOLD}$2${RESET}\n"; }
fixed()  { echo -e "    ${GREEN}↳ fixed${RESET}"; }
skipped(){ echo -e "    ${DIM}↳ skipped${RESET}"; }

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

mask_key() {
  local val="$1"
  if [[ -z "$val" ]]; then echo "(not set)"; return; fi
  echo "${val:0:8}…"
}

prompt_optional_key() {
  # prompt_optional_key ENV_KEY "description" "instructions"
  local key="$1" desc="$2" hint="$3"
  local current
  current=$(get_env_key "$key")
  if [[ -n "$current" ]]; then
    ok "${key}  $(mask_key "$current")  — ${desc}"
    return
  fi
  warn "${key}  not set  — ${desc}"
  echo -e "    ${DIM}${hint}${RESET}"
  read -rp "    Enter value (press Enter to skip): " val
  echo ""
  if [[ -n "$val" ]]; then
    set_env_key "$key" "$val"
    ok "${key} saved"
  else
    skipped
  fi
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

# ── Check wizard ───────────────────────────────────────────────────────────────

do_check() {
  echo ""
  echo -e "${BOLD}${CYAN}Resonance Health Check${RESET}"
  echo -e "${DIM}Diagnoses and auto-fixes your Resonance setup.${RESET}"
  echo ""

  local issues=0
  local fixed_count=0

  # ────────────────────────────────────────────────────────────────────────────
  step "1/7" "Python Environment"

  # Python
  local py
  py=$(find_python 2>/dev/null) || {
    fail "Python 3.11+ not found"
    echo "    Install: brew install python@3.11"
    exit 1
  }
  local pyver
  pyver=$("$py" -c "import sys; print('.'.join(map(str,sys.version_info[:3])))")
  ok "Python ${pyver}  (${py})"

  # Venv
  if [[ -d "$VENV_DIR" ]]; then
    ok "Virtual environment  (.venv)"
  else
    warn "Virtual environment missing"
    info "Creating .venv..."
    "$py" -m venv "$VENV_DIR"
    ok "Created .venv"
    ((fixed_count++))
  fi
  export PATH="$VENV_DIR/bin:$PATH"

  # Resonance package
  if command -v resonance &>/dev/null; then
    local ver
    ver=$(resonance --version 2>/dev/null || echo "installed")
    ok "resonance  (${ver})"
  else
    warn "resonance not installed"
    info "Installing..."
    "$VENV_DIR/bin/python" -m pip install -e . -q
    ok "resonance installed"
    ((fixed_count++))
  fi

  # Python deps
  local missing_deps=()
  for mod in httpx typer rich yaml dotenv; do
    local import_name="$mod"
    [[ "$mod" == "yaml" ]] && import_name="yaml"
    [[ "$mod" == "dotenv" ]] && import_name="dotenv"
    "$VENV_DIR/bin/python" -c "import ${import_name}" 2>/dev/null || missing_deps+=("$mod")
  done
  if [[ ${#missing_deps[@]} -eq 0 ]]; then
    ok "Python dependencies  (httpx, typer, rich, pyyaml, python-dotenv)"
  else
    warn "Missing packages: ${missing_deps[*]}"
    info "Installing via pip..."
    "$VENV_DIR/bin/python" -m pip install -e . -q
    ok "Dependencies installed"
    ((fixed_count++))
  fi

  # ────────────────────────────────────────────────────────────────────────────
  step "2/7" "Configuration Files"

  # .env
  if [[ -f .env ]]; then
    ok ".env  found"
  else
    warn ".env  not found — creating skeleton"
    cat > .env <<'ENVEOF'
LINEAR_API_KEY=
LINEAR_TEAM_ID=
# LINEAR_PROJECT_ID=
# FIGMA_API_KEY=
# GITHUB_TOKEN=
ENVEOF
    ok ".env  skeleton created"
    ((fixed_count++))
  fi

  # WORKFLOW.md
  if [[ -f WORKFLOW.md ]]; then
    "$VENV_DIR/bin/python" -c "import yaml; yaml.safe_load(open('WORKFLOW.md'))" 2>/dev/null && \
      ok "WORKFLOW.md  (valid YAML)" || \
      { fail "WORKFLOW.md  parse error — file may be corrupted"; ((issues++)); }
  else
    fail "WORKFLOW.md  not found — this repo may be incomplete"
    ((issues++))
  fi

  # .mcp.json
  if [[ -f .mcp.json ]]; then
    if "$VENV_DIR/bin/python" -c "import json; d=json.load(open('.mcp.json')); assert 'linear' in str(d)" 2>/dev/null; then
      ok ".mcp.json  (linear MCP configured)"
    else
      warn ".mcp.json  found but linear server not detected — agents may lack Linear access"
      ((issues++))
    fi
  else
    warn ".mcp.json  not found — MCP tools will not be available to agents"
    dim "    See .mcp.json.example or run: resonance setup"
    ((issues++))
  fi

  # ────────────────────────────────────────────────────────────────────────────
  step "3/7" "API Keys"

  # LINEAR_API_KEY — required
  local api_key
  api_key=$(get_env_key "LINEAR_API_KEY")
  if [[ -z "$api_key" ]]; then
    fail "LINEAR_API_KEY  not set  (required)"
    echo ""
    echo -e "    ${DIM}Get it: Linear → Settings → API → Personal API keys${RESET}"
    read -rp "    Enter LINEAR_API_KEY: " api_key
    echo ""
    if [[ -z "$api_key" ]]; then
      fail "LINEAR_API_KEY is required — cannot continue without it."
      exit 1
    fi
    set_env_key "LINEAR_API_KEY" "$api_key"
    ok "LINEAR_API_KEY saved"
    ((fixed_count++))
  else
    ok "LINEAR_API_KEY  $(mask_key "$api_key")  (set)"
  fi

  # LINEAR_TEAM_ID — required, but we can discover it
  local team_id
  team_id=$(get_env_key "LINEAR_TEAM_ID")
  if [[ -z "$team_id" ]]; then
    warn "LINEAR_TEAM_ID  not set"
    echo ""
    echo -e "    ${DIM}Fetching your teams from Linear...${RESET}"
    # Use Python to list teams
    "$VENV_DIR/bin/python" - "$api_key" <<'PYEOF'
import sys
sys.path.insert(0, '.')
from orchestrator.linear_client import LinearClient
client = LinearClient(sys.argv[1])
try:
    teams = client.get_teams()
    if not teams:
        print("    No teams found.")
    else:
        for i, t in enumerate(teams, 1):
            print(f"    {i})  {t['name']}  [{t['key']}]  —  {t['id']}")
    client.close()
except Exception as e:
    print(f"    Could not fetch teams: {e}")
PYEOF
    echo ""
    read -rp "    Enter team UUID or number: " team_input
    echo ""
    if [[ -z "$team_input" ]]; then
      fail "LINEAR_TEAM_ID is required — cannot continue."
      exit 1
    fi
    # If it's a number, resolve it
    if [[ "$team_input" =~ ^[0-9]+$ ]]; then
      team_id=$("$VENV_DIR/bin/python" - "$api_key" "$team_input" <<'PYEOF'
import sys
sys.path.insert(0, '.')
from orchestrator.linear_client import LinearClient
client = LinearClient(sys.argv[1])
try:
    teams = client.get_teams()
    idx = int(sys.argv[2]) - 1
    print(teams[idx]['id'] if 0 <= idx < len(teams) else '')
    client.close()
except Exception:
    print('')
PYEOF
)
    else
      team_id="$team_input"
    fi
    if [[ -z "$team_id" ]]; then
      fail "Could not resolve team — enter a UUID directly."
      exit 1
    fi
    set_env_key "LINEAR_TEAM_ID" "$team_id"
    ok "LINEAR_TEAM_ID saved  (${team_id:0:8}…)"
    ((fixed_count++))
  else
    ok "LINEAR_TEAM_ID  $(mask_key "$team_id")  (set)"
  fi

  # Reload .env so subsequent calls see the new values
  set -a; source .env 2>/dev/null || true; set +a

  # LINEAR_PROJECT_ID — optional
  local project_id
  project_id=$(get_env_key "LINEAR_PROJECT_ID")
  if [[ -n "$project_id" ]]; then
    ok "LINEAR_PROJECT_ID  $(mask_key "$project_id")  (set)"
  else
    warn "LINEAR_PROJECT_ID  not set  (optional — scopes orchestrator to one project)"
    read -rp "    Enter project UUID or URL (Enter to skip): " proj_input
    echo ""
    if [[ -n "$proj_input" ]]; then
      # Strip tab-style URL suffixes if pasted from Linear
      proj_input="${proj_input%%\?*}"
      proj_input="${proj_input##*/}"
      set_env_key "LINEAR_PROJECT_ID" "$proj_input"
      ok "LINEAR_PROJECT_ID saved"
      ((fixed_count++))
    else
      skipped
    fi
  fi

  # FIGMA_API_KEY — optional
  prompt_optional_key "FIGMA_API_KEY" \
    "optional — required for design_to_code tasks" \
    "Get it: Figma → Settings → Security → Personal access tokens"

  # GITHUB_TOKEN — optional
  prompt_optional_key "GITHUB_TOKEN" \
    "optional — required for automated PR creation" \
    "Get it: GitHub → Settings → Developer settings → Personal access tokens"

  # ────────────────────────────────────────────────────────────────────────────
  step "4/7" "Linear API Validation"

  # Reload credentials from .env
  set -a; source .env 2>/dev/null || true; set +a
  api_key=$(get_env_key "LINEAR_API_KEY")
  team_id=$(get_env_key "LINEAR_TEAM_ID")

  local linear_ok=true
  "$VENV_DIR/bin/python" - "$api_key" "$team_id" <<'PYEOF'
import sys
sys.path.insert(0, '.')
from orchestrator.linear_client import LinearClient
api_key, team_id = sys.argv[1], sys.argv[2]
try:
    client = LinearClient(api_key)
    viewer = client.get_viewer()
    print(f"OK_AUTH:{viewer['name']}:{viewer['email']}")
    team = client.get_team(team_id)
    if team:
        print(f"OK_TEAM:{team['name']}:{team['key']}")
    else:
        print(f"FAIL_TEAM:team not found: {team_id}")
    client.close()
except Exception as e:
    print(f"FAIL_AUTH:{e}")
PYEOF
  while IFS= read -r line; do
    case "$line" in
      OK_AUTH:*)   IFS=: read -r _ name email <<< "$line"; ok "Linear authenticated as ${name} (${email})" ;;
      OK_TEAM:*)   IFS=: read -r _ tname tkey  <<< "$line"; ok "Linear team: ${tname} [${tkey}]" ;;
      FAIL_AUTH:*) fail "Linear API key invalid: ${line#FAIL_AUTH:}"; linear_ok=false; ((issues++)) ;;
      FAIL_TEAM:*) fail "Linear team not found: ${line#FAIL_TEAM:}"; linear_ok=false; ((issues++)) ;;
    esac
  done < <("$VENV_DIR/bin/python" - "$api_key" "$team_id" <<'PYEOF'
import sys
sys.path.insert(0, '.')
from orchestrator.linear_client import LinearClient
api_key, team_id = sys.argv[1], sys.argv[2]
try:
    client = LinearClient(api_key)
    viewer = client.get_viewer()
    print(f"OK_AUTH:{viewer['name']}:{viewer['email']}")
    team = client.get_team(team_id)
    if team:
        print(f"OK_TEAM:{team['name']}:{team['key']}")
    else:
        print(f"FAIL_TEAM:team not found: {team_id}")
    client.close()
except Exception as e:
    print(f"FAIL_AUTH:{e}")
PYEOF
  )

  # Check optional project if set
  project_id=$(get_env_key "LINEAR_PROJECT_ID")
  if [[ -n "$project_id" && "$linear_ok" == "true" ]]; then
    "$VENV_DIR/bin/python" - "$api_key" "$project_id" <<'PYEOF' | while IFS= read -r line; do
import sys
sys.path.insert(0, '.')
from orchestrator.linear_client import LinearClient
api_key, proj_id = sys.argv[1], sys.argv[2]
try:
    client = LinearClient(api_key)
    proj = client.get_project(proj_id)
    if proj:
        print(f"OK:{proj['name']}")
    else:
        print(f"FAIL:project not found: {proj_id}")
    client.close()
except Exception as e:
    print(f"FAIL:{e}")
PYEOF
      case "$line" in
        OK:*)   ok "LINEAR_PROJECT_ID: ${line#OK:}" ;;
        FAIL:*) warn "LINEAR_PROJECT_ID: ${line#FAIL:}" ;;
      esac
    done
  fi

  # ────────────────────────────────────────────────────────────────────────────
  step "5/7" "Linear Workflow States"

  if [[ "$linear_ok" == "true" ]]; then
    local states_out
    states_out=$("$VENV_DIR/bin/python" - "$api_key" "$team_id" <<'PYEOF'
import sys, json
sys.path.insert(0, '.')
from orchestrator.linear_client import LinearClient, STATES_TO_CREATE
api_key, team_id = sys.argv[1], sys.argv[2]
client = LinearClient(api_key)
existing = {s['name'] for s in client.get_team_states(team_id)}
standard = {'In Progress', 'Todo', 'Done', 'Cancelled'}
required = [s['default'] for s in STATES_TO_CREATE]
all_required = list(standard) + required
for name in all_required:
    status = 'OK' if name in existing else 'MISSING'
    print(f"{status}:{name}")
client.close()
PYEOF
    )
    local missing_states=()
    while IFS= read -r line; do
      case "$line" in
        OK:*)      ok "${line#OK:}" ;;
        MISSING:*) warn "${line#MISSING:}  — missing"; missing_states+=("${line#MISSING:}") ;;
      esac
    done <<< "$states_out"

    if [[ ${#missing_states[@]} -gt 0 ]]; then
      echo ""
      info "Creating ${#missing_states[@]} missing state(s) via 'resonance fix'..."
      resonance fix 2>&1 | grep -E "Created|already|Could not" | sed 's/^/    /'
      ok "States fixed"
      ((fixed_count++))
    fi
  else
    warn "Skipping state check — Linear API not connected"
  fi

  # ────────────────────────────────────────────────────────────────────────────
  step "6/7" "Linear Labels"

  if [[ "$linear_ok" == "true" ]]; then
    local labels_out
    labels_out=$("$VENV_DIR/bin/python" - "$api_key" "$team_id" <<'PYEOF'
import sys
sys.path.insert(0, '.')
from orchestrator.linear_client import LinearClient, REQUIRED_LABELS
api_key, team_id = sys.argv[1], sys.argv[2]
client = LinearClient(api_key)
existing = {l['name'].lower() for l in client.get_team_labels(team_id)}
for label in REQUIRED_LABELS:
    status = 'OK' if label['name'].lower() in existing else 'MISSING'
    print(f"{status}:{label['name']}")
client.close()
PYEOF
    )
    local missing_labels=()
    while IFS= read -r line; do
      case "$line" in
        OK:*)      ok "${line#OK:}" ;;
        MISSING:*) warn "${line#MISSING:}  — missing"; missing_labels+=("${line#MISSING:}") ;;
      esac
    done <<< "$labels_out"

    if [[ ${#missing_labels[@]} -gt 0 ]]; then
      echo ""
      info "Creating ${#missing_labels[@]} missing label(s)..."
      "$VENV_DIR/bin/python" - "$api_key" "$team_id" "${missing_labels[@]}" <<'PYEOF'
import sys
sys.path.insert(0, '.')
from orchestrator.linear_client import LinearClient, REQUIRED_LABELS
api_key, team_id = sys.argv[1], sys.argv[2]
to_create = set(sys.argv[3:])
client = LinearClient(api_key)
label_map = {l['name']: l for l in REQUIRED_LABELS}
for name in to_create:
    label = label_map.get(name)
    if not label:
        continue
    try:
        client.create_label(team_id, label['name'], label['color'])
        print(f"CREATED:{name}")
    except Exception as e:
        print(f"FAILED:{name}:{e}")
client.close()
PYEOF
      ok "Labels fixed"
      ((fixed_count++))
    fi
  else
    warn "Skipping label check — Linear API not connected"
  fi

  # ────────────────────────────────────────────────────────────────────────────
  step "7/7" "MCP Configuration"

  if [[ -f .mcp.json ]]; then
    local has_linear has_figma
    has_linear=$("$VENV_DIR/bin/python" -c "
import json
d = json.load(open('.mcp.json'))
servers = d.get('mcpServers', d)
print('yes' if 'linear' in servers else 'no')
" 2>/dev/null || echo "no")
    has_figma=$("$VENV_DIR/bin/python" -c "
import json
d = json.load(open('.mcp.json'))
servers = d.get('mcpServers', d)
print('yes' if 'figma' in servers else 'no')
" 2>/dev/null || echo "no")

    if [[ "$has_linear" == "yes" ]]; then
      # Check that LINEAR_ACCESS_TOKEN is wired (linear-mcp uses this, not LINEAR_API_KEY)
      has_token_env=$("$VENV_DIR/bin/python" -c "
import json
d = json.load(open('.mcp.json'))
servers = d.get('mcpServers', d)
linear = servers.get('linear', {})
env = linear.get('env', {})
print('yes' if 'LINEAR_ACCESS_TOKEN' in env else 'no')
" 2>/dev/null || echo "no")
      if [[ "$has_token_env" == "yes" ]]; then
        ok "MCP: linear server configured  (LINEAR_ACCESS_TOKEN wired)"
      else
        info "Auto-adding LINEAR_ACCESS_TOKEN env mapping to linear MCP..."
        "$VENV_DIR/bin/python" - <<'PYEOF'
import json
path = '.mcp.json'
with open(path) as f:
    cfg = json.load(f)
servers = cfg.setdefault('mcpServers', cfg)
servers['linear'].setdefault('env', {})['LINEAR_ACCESS_TOKEN'] = '${LINEAR_API_KEY}'
with open(path, 'w') as f:
    json.dump(cfg, f, indent=2)
    f.write('\n')
PYEOF
        ok "MCP: linear  LINEAR_ACCESS_TOKEN env added"; ((fixed_count++))
      fi
    else
      warn "MCP: linear server not found in .mcp.json"; ((issues++))
    fi
    figma_key=$(get_env_key "FIGMA_API_KEY")
    if [[ "$has_figma" == "yes" ]]; then
      ok "MCP: figma server configured"
    elif [[ -n "$figma_key" ]]; then
      info "Auto-adding figma MCP server to .mcp.json..."
      "$VENV_DIR/bin/python" - <<'PYEOF'
import json, sys
path = '.mcp.json'
with open(path) as f:
    cfg = json.load(f)
cfg.setdefault('mcpServers', {})['figma'] = {
    'command': 'npx',
    'args': ['-y', 'figma-developer-mcp', '--stdio'],
    'env': {'FIGMA_API_KEY': '${FIGMA_API_KEY}'}
}
with open(path, 'w') as f:
    json.dump(cfg, f, indent=2)
    f.write('\n')
print('done')
PYEOF
      ok "MCP: figma server added to .mcp.json"; ((fixed_count++))
    else
      dim "    MCP: figma server not configured (no FIGMA_API_KEY — optional)"
    fi
  else
    warn ".mcp.json not found"
    dim "    Copy .mcp.json.example or run: resonance setup"
    ((issues++))
  fi

  # ────────────────────────────────────────────────────────────────────────────
  echo ""
  echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo ""

  if [[ $issues -eq 0 ]]; then
    echo -e "${GREEN}${BOLD}✓ All checks passed.${RESET}"
    if [[ $fixed_count -gt 0 ]]; then
      echo -e "  Auto-fixed ${fixed_count} item(s) during this run."
    fi
    echo ""
    echo -e "  Ready to start:  ${BOLD}./onair.sh${RESET}"
  else
    echo -e "${YELLOW}${BOLD}⚠ ${issues} issue(s) need attention.${RESET}"
    if [[ $fixed_count -gt 0 ]]; then
      echo -e "  Auto-fixed ${fixed_count} item(s). Review the warnings above for what remains."
    fi
    echo ""
    echo -e "  Next steps:"
    echo -e "    ${BOLD}./setup.sh check${RESET}   — re-run after fixing"
    echo -e "    ${BOLD}resonance doctor${RESET}   — quick status check"
    echo -e "    ${BOLD}resonance fix${RESET}      — re-apply Linear states/labels"
  fi
  echo ""
}

do_update() {
  header "Update Configuration"

  if [[ ! -f .env ]]; then
    fail ".env not found — run ./setup.sh first."
    exit 1
  fi

  ensure_resonance

  KEYS=("LINEAR_API_KEY" "LINEAR_TEAM_ID" "LINEAR_PROJECT_ID" "FIGMA_API_KEY" "GITHUB_TOKEN")
  DESCS=(
    "Linear personal API key  (Settings → API → Personal API keys)"
    "Linear team UUID         (from resonance setup or your Linear team URL)"
    "Linear project UUID      (optional — scopes orchestrator to one project)"
    "Figma API key            (optional — required for design_to_code tasks)"
    "GitHub token             (optional — required for PR creation)"
  )

  while true; do
    echo -e "${BOLD}What would you like to update?${RESET}"
    for i in "${!KEYS[@]}"; do
      current=$(get_env_key "${KEYS[$i]}")
      masked=$(mask_key "$current")
      printf "  %d)  %-26s  %s\n" "$((i+1))" "${KEYS[$i]}" "${DIM}${DESCS[$i]}${RESET}"
      printf "       %-26s  current: %s\n" "" "${DIM}${masked}${RESET}"
      echo ""
    done
    echo -e "  6)  ${BOLD}Fix Linear labels / states${RESET}  ${DIM}Create missing required items in Linear${RESET}"
    echo -e "  7)  ${BOLD}Full health check${RESET}           ${DIM}Run ./setup.sh check${RESET}"
    echo ""
    echo -e "  q)  Done\n"
    read -rp "Choice: " choice
    echo ""

    case "$choice" in
      1|2|3|4|5)
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
      6)
        echo ""
        info "Creating missing Linear labels and workflow states..."
        echo ""
        resonance fix
        echo ""
        ;;
      7)
        do_check
        ;;
      q|Q|"")
        break
        ;;
      *)
        warn "Invalid choice — enter 1–7 or q."
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
  check)     do_check    ;;
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
    echo "    check      Full health-check wizard — diagnoses everything, auto-fixes what it can"
    echo "               prompts for missing API keys, creates missing Linear states/labels"
    echo "    overwrite  Redo everything — replace all credentials"
    echo "    update     Update one or more API keys without touching the rest"
    echo "    wipe       Remove .env and clear all runtime state (worktrees preserved)"
    echo ""
    exit 1
    ;;
esac
