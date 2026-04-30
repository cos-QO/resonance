#!/usr/bin/env bash
# wizard.sh — Resonance management wizard
#
# Usage:
#   ./wizard.sh              interactive menu (default)
#   ./wizard.sh setup        first-time setup — credentials + Linear states/labels
#   ./wizard.sh check        full health-check — diagnose and auto-fix everything
#   ./wizard.sh update       update API keys or configuration
#   ./wizard.sh kill         stop the running orchestrator
#   ./wizard.sh restart      kill and restart the orchestrator (no TUI)
#   ./wizard.sh wipe         remove .env and clear all runtime state
#   ./wizard.sh overwrite    redo everything from scratch

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
  grep "^${key}=" .env 2>/dev/null | cut -d= -f2- | tr -d '"' || echo ""
}

mask_key() {
  local val="$1"
  if [[ -z "$val" ]]; then echo "(not set)"; return; fi
  echo "${val:0:8}…"
}

prompt_optional_key() {
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

# ── Interactive menu (default) ────────────────────────────────────────────────

do_menu() {
  while true; do
    echo ""
    echo -e "${BOLD}${CYAN}Resonance Wizard${RESET}"
    echo -e "${DIM}What would you like to do?${RESET}"
    echo ""
    echo -e "  ${BOLD}1)  Setup${RESET}        ${DIM}First-time setup — credentials + Linear states/labels${RESET}"
    echo -e "  ${BOLD}2)  Check${RESET}        ${DIM}Full health-check — diagnose and auto-fix everything${RESET}"
    echo -e "  ${BOLD}3)  Test${RESET}         ${DIM}Run live integration tests — Python, MCP, worker env${RESET}"
    echo -e "  ${BOLD}4)  Update${RESET}       ${DIM}Update API keys or configuration${RESET}"
    echo ""
    echo -e "  ${BOLD}5)  Kill${RESET}         ${DIM}Stop the running orchestrator${RESET}"
    echo -e "  ${BOLD}6)  Restart${RESET}      ${DIM}Kill and restart the orchestrator (no TUI)${RESET}"
    echo ""
    echo -e "  ${BOLD}7)  Wipe${RESET}         ${DIM}Remove credentials and clear all runtime state${RESET}"
    echo -e "  ${BOLD}8)  Overwrite${RESET}    ${DIM}Redo everything from scratch${RESET}"
    echo ""
    echo -e "  ${DIM}q)  Quit${RESET}"
    echo ""
    read -rp "  Choice: " choice
    echo ""

    case "$choice" in
      1|setup)     do_setup;    echo ""; read -rp "  Press Enter to return to menu…" _; ;;
      2|check)     do_check;    echo ""; read -rp "  Press Enter to return to menu…" _; ;;
      3|test)      do_test;     echo ""; read -rp "  Press Enter to return to menu…" _; ;;
      4|update)    do_update;   ;;
      5|kill)      do_kill;     echo ""; read -rp "  Press Enter to return to menu…" _; ;;
      6|restart)   do_restart;  echo ""; read -rp "  Press Enter to return to menu…" _; ;;
      7|wipe)      do_wipe;     echo ""; read -rp "  Press Enter to return to menu…" _; ;;
      8|overwrite) do_overwrite; echo ""; read -rp "  Press Enter to return to menu…" _; ;;
      q|Q|"")      echo ""; exit 0 ;;
      *)           warn "Invalid choice — enter 1–8 or q." ;;
    esac
  done
}

# ── Modes ─────────────────────────────────────────────────────────────────────

do_setup() {
  header "Resonance Setup"
  ensure_resonance
  resonance setup
}

# ── Live integration tests ────────────────────────────────────────────────────

do_test() {
  echo ""
  echo -e "${BOLD}${CYAN}Resonance Live Integration Tests${RESET}"
  echo -e "${DIM}Tests the full auth chain — Python client, MCP server, worker env.${RESET}"
  echo ""

  ensure_venv
  local issues=0

  local api_key
  api_key=$(get_env_key "LINEAR_API_KEY")

  if [[ -z "$api_key" ]]; then
    fail "LINEAR_API_KEY not set — cannot run tests."
    echo ""
    return 1
  fi

  # ── Test 1: Python Linear client ────────────────────────────────────────────
  echo -e "${BOLD}[1/4]${RESET}  Python Linear client (orchestrator auth path)"
  local py_result
  py_result=$("$VENV_DIR/bin/python" - "$api_key" <<'PYEOF' 2>&1
import sys
sys.path.insert(0, '.')
from orchestrator.linear_client import LinearClient
try:
    client = LinearClient(sys.argv[1])
    viewer = client.get_viewer()
    teams = client.get_teams()
    client.close()
    print(f"OK:{viewer['name']}:{viewer['email']}:{len(teams)}")
except Exception as e:
    print(f"FAIL:{e}")
PYEOF
  )
  case "$py_result" in
    OK:*) IFS=: read -r _ name email n_teams <<< "$py_result"
          ok "Authenticated as ${name} <${email}>  (${n_teams} teams visible)" ;;
    FAIL:*) fail "${py_result#FAIL:}"; ((issues++)) ;;
    *)      fail "Unexpected: ${py_result}"; ((issues++)) ;;
  esac
  echo ""

  # ── Test 2: linear-mcp Node.js auth ─────────────────────────────────────────
  echo -e "${BOLD}[2/4]${RESET}  linear-mcp MCP server auth (worker agent path)"
  local auth_js=""
  for try_path in \
    "$(npm root -g 2>/dev/null)/linear-mcp/build/auth.js" \
    "$HOME/.npm-global/lib/node_modules/linear-mcp/build/auth.js" \
    "/usr/local/lib/node_modules/linear-mcp/build/auth.js"; do
    [[ -f "$try_path" ]] && { auth_js="$try_path"; break; }
  done

  if [[ -z "$auth_js" ]]; then
    fail "linear-mcp not found (npm install -g linear-mcp)"
    ((issues++))
  elif ! command -v node &>/dev/null; then
    fail "node not found — cannot test MCP auth"
    ((issues++))
  else
    local mcp_dir
    mcp_dir=$(dirname "$auth_js")
    local node_result
    node_result=$(LINEAR_ACCESS_TOKEN="$api_key" node --input-type=module <<JSEOF 2>&1
import { LinearAuth } from '${auth_js}';
import { LinearGraphQLClient } from '${mcp_dir}/graphql/client.js';
const auth = new LinearAuth();
auth.initialize({ type: 'pat', accessToken: process.env.LINEAR_ACCESS_TOKEN });
const graphql = new LinearGraphQLClient(auth.getClient());
try {
  const result = await graphql.getCurrentUser();
  const name = result.viewer?.name || result.viewer?.email || 'unknown';
  const hdr = auth.getClient().client.options?.headers?.Authorization || '';
  const hasBearer = hdr.startsWith('Bearer ');
  console.log('OK:' + name + ':' + (hasBearer ? 'BEARER_BUG' : 'OK'));
} catch (e) {
  console.log('FAIL:' + e.message.slice(0, 200));
}
JSEOF
    )
    case "$node_result" in
      OK:*:OK)
        IFS=: read -r _ name _ <<< "$node_result"
        ok "Authenticated as ${name}  (Authorization header: no Bearer prefix)" ;;
      OK:*:BEARER_BUG)
        IFS=: read -r _ name _ <<< "$node_result"
        fail "Authenticated but auth.js still sends Bearer prefix — patch not applied"
        warn "Run: ./wizard.sh check  to re-apply the fix"
        ((issues++)) ;;
      FAIL:*)
        fail "${node_result#FAIL:}"
        dim "    Worker agents will not have Linear MCP access."
        dim "    If Linear rejects Bearer tokens: run ./wizard.sh check to patch auth.js"
        ((issues++)) ;;
      *)
        fail "Unexpected output: ${node_result}"; ((issues++)) ;;
    esac
  fi
  echo ""

  # ── Test 3: Worker env injection ─────────────────────────────────────────────
  echo -e "${BOLD}[3/4]${RESET}  Worker environment injection (runner.py)"
  if grep -q "LINEAR_ACCESS_TOKEN" orchestrator/runner.py 2>/dev/null; then
    ok "runner.py injects LINEAR_ACCESS_TOKEN into worker subprocess env"
  else
    fail "runner.py does not set LINEAR_ACCESS_TOKEN — worker agents will lack MCP auth"
    dim "    Edit orchestrator/runner.py: add proc_env['LINEAR_ACCESS_TOKEN'] = LINEAR_API_KEY"
    ((issues++))
  fi
  echo ""

  # ── Test 3b: linear_create_issue schema has required fields ─────────────────
  if [[ -n "$auth_js" ]]; then
    local types_js
    types_js="$(dirname "$auth_js")/core/types/tool.types.js"
    if [[ -f "$types_js" ]]; then
      local missing_fields=()
      for field in projectId parentId stateId labelIds; do
        grep -q "$field" "$types_js" 2>/dev/null || missing_fields+=("$field")
      done
      if [[ ${#missing_fields[@]} -eq 0 ]]; then
        ok "linear_create_issue schema  (projectId, parentId, stateId, labelIds present)"
      else
        fail "linear_create_issue schema missing fields: ${missing_fields[*]}"
        dim "    Agents won't be able to set project/parent/state/labels on created issues."
        dim "    Run: ./wizard.sh check  to auto-apply the schema patch."
        ((issues++))
      fi
    fi
  fi
  echo ""

  # ── Test 4: MCP config files ──────────────────────────────────────────────────
  echo -e "${BOLD}[4/4]${RESET}  MCP config files"
  local config_issues=0
  for f in .mcp.json .claude/cc-pipeline/.mcp.json; do
    if [[ -f "$f" ]]; then
      if grep -q '\${' "$f" 2>/dev/null; then
        fail "${f}: contains unexpanded \${...} — run ./wizard.sh check to fix"
        ((config_issues++))
      else
        ok "${f}  (clean)"
      fi
    fi
  done
  local user_settings="$HOME/.claude/settings.json"
  if [[ -f "$user_settings" ]]; then
    local bad_key
    bad_key=$(python3 -c "
import json, re
try:
    d = json.load(open('$user_settings'))
    env = d.get('mcpServers', {}).get('linear', {}).get('env', {})
    bad = [k for k, v in env.items()
           if k == 'LINEAR_API_KEY' or (isinstance(v, str) and re.search(r'\\\${', v))]
    print(','.join(bad))
except Exception:
    print('')
" 2>/dev/null || echo "")
    if [[ -n "$bad_key" ]]; then
      fail "~/.claude/settings.json: wrong MCP env key(s): ${bad_key} — run ./wizard.sh check to fix"
      ((config_issues++))
    else
      ok "~/.claude/settings.json  (linear MCP env: correct)"
    fi
  fi
  [[ $config_issues -gt 0 ]] && ((issues++))
  echo ""

  # ── Summary ───────────────────────────────────────────────────────────────────
  echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo ""
  if [[ $issues -eq 0 ]]; then
    echo -e "${GREEN}${BOLD}✓ All tests passed.${RESET}  Resonance is ready."
    echo ""
    echo -e "  Start:  ${BOLD}./onair.sh${RESET}"
  else
    echo -e "${RED}${BOLD}✗ ${issues} test(s) failed.${RESET}  See failures above."
    echo ""
    echo -e "  Run ${BOLD}./wizard.sh check${RESET} to auto-fix most issues."
  fi
  echo ""
}

do_overwrite() {
  header "Resonance Setup — Overwrite"
  warn "This will replace your existing credentials."
  read -rp "  Continue? [y/N] " confirm
  echo ""
  [[ "$confirm" =~ ^[Yy]$ ]] || { info "Cancelled."; return; }

  ensure_resonance
  rm -f .env
  resonance setup
}

# ── Check wizard ──────────────────────────────────────────────────────────────

do_check() {
  echo ""
  echo -e "${BOLD}${CYAN}Resonance Health Check${RESET}"
  echo -e "${DIM}Diagnoses and auto-fixes your Resonance setup.${RESET}"
  echo ""

  local issues=0
  local fixed_count=0

  # ────────────────────────────────────────────────────────────────────────────
  step "1/8" "Python Environment"

  local py
  py=$(find_python 2>/dev/null) || {
    fail "Python 3.11+ not found"
    echo "    Install: brew install python@3.11"
    exit 1
  }
  local pyver
  pyver=$("$py" -c "import sys; print('.'.join(map(str,sys.version_info[:3])))")
  ok "Python ${pyver}  (${py})"

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

  local missing_deps=()
  for mod in httpx typer rich yaml dotenv; do
    "$VENV_DIR/bin/python" -c "import ${mod}" 2>/dev/null || missing_deps+=("$mod")
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
  step "2/8" "Configuration Files"

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

  if [[ -f WORKFLOW.md ]]; then
    "$VENV_DIR/bin/python" -c "import yaml; yaml.safe_load(open('WORKFLOW.md'))" 2>/dev/null && \
      ok "WORKFLOW.md  (valid YAML)" || \
      { fail "WORKFLOW.md  parse error — file may be corrupted"; ((issues++)); }
  else
    fail "WORKFLOW.md  not found — this repo may be incomplete"
    ((issues++))
  fi

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
  step "3/8" "API Keys"

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

  local team_id
  team_id=$(get_env_key "LINEAR_TEAM_ID")
  if [[ -z "$team_id" ]]; then
    warn "LINEAR_TEAM_ID  not set"
    echo ""
    echo -e "    ${DIM}Fetching your teams from Linear...${RESET}"
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

  set -a; source .env 2>/dev/null || true; set +a

  local project_id
  project_id=$(get_env_key "LINEAR_PROJECT_ID")
  if [[ -n "$project_id" ]]; then
    ok "LINEAR_PROJECT_ID  $(mask_key "$project_id")  (set)"
  else
    warn "LINEAR_PROJECT_ID  not set  (optional — scopes orchestrator to one project)"
    read -rp "    Enter project UUID or URL (Enter to skip): " proj_input
    echo ""
    if [[ -n "$proj_input" ]]; then
      proj_input="${proj_input%%\?*}"
      proj_input="${proj_input##*/}"
      set_env_key "LINEAR_PROJECT_ID" "$proj_input"
      ok "LINEAR_PROJECT_ID saved"
      ((fixed_count++))
    else
      skipped
    fi
  fi

  prompt_optional_key "FIGMA_API_KEY" \
    "optional — required for design_to_code tasks" \
    "Get it: Figma → Settings → Security → Personal access tokens"

  prompt_optional_key "GITHUB_TOKEN" \
    "optional — required for automated PR creation" \
    "Get it: GitHub → Settings → Developer settings → Personal access tokens"

  # ────────────────────────────────────────────────────────────────────────────
  step "4/8" "Linear API Validation"

  set -a; source .env 2>/dev/null || true; set +a
  api_key=$(get_env_key "LINEAR_API_KEY")
  team_id=$(get_env_key "LINEAR_TEAM_ID")

  local linear_ok=true
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
  step "5/8" "Linear Workflow States"

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
  step "6/8" "Linear Labels"

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
  step "7/8" "MCP Configuration"

  # Note: Claude CLI does NOT expand ${VAR} syntax in MCP env fields.
  # LINEAR_ACCESS_TOKEN is the var that linear-mcp reads (not LINEAR_API_KEY).
  # It must be set correctly in ~/.claude/settings.json (user-level MCP config) and
  # injected by runner.py into subprocess env as a fallback for project-level .mcp.json.

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

    # Remove any broken env field that has literal ${...} variable references
    "$VENV_DIR/bin/python" - <<'PYEOF'
import json, re
path = '.mcp.json'
with open(path) as f:
    cfg = json.load(f)
changed = False
for srv in cfg.get('mcpServers', {}).values():
    env = srv.get('env', {})
    bad_keys = [k for k, v in env.items() if isinstance(v, str) and re.search(r'\$\{', v)]
    for k in bad_keys:
        del env[k]
        changed = True
    if env == {} and 'env' in srv:
        del srv['env']
        changed = True
if changed:
    with open(path, 'w') as f:
        json.dump(cfg, f, indent=2)
        f.write('\n')
    print('patched')
PYEOF

    if [[ "$has_linear" == "yes" ]]; then
      local api_key_in_env
      api_key_in_env=$(get_env_key "LINEAR_API_KEY")
      if [[ -n "$api_key_in_env" ]]; then
        ok "MCP: linear server configured  (LINEAR_ACCESS_TOKEN injected at runtime from LINEAR_API_KEY)"
      else
        warn "MCP: linear server configured but LINEAR_API_KEY not set — MCP auth will fail"
        ((issues++))
      fi
    else
      warn "MCP: linear server not found in .mcp.json"; ((issues++))
    fi

    # Fix user-level ~/.claude/settings.json if it has wrong key name or unexpanded vars
    local user_settings="$HOME/.claude/settings.json"
    if [[ -f "$user_settings" ]]; then
      local bad_user_key
      bad_user_key=$("$VENV_DIR/bin/python" -c "
import json, re
try:
    d = json.load(open('$user_settings'))
    env = d.get('mcpServers', {}).get('linear', {}).get('env', {})
    bad = [k for k, v in env.items()
           if k == 'LINEAR_API_KEY' or (isinstance(v, str) and re.search(r'\\\${', v))]
    print(','.join(bad) if bad else '')
except Exception:
    print('')
" 2>/dev/null || echo "")
      if [[ -n "$bad_user_key" ]]; then
        local api_key_in_env
        api_key_in_env=$(get_env_key "LINEAR_API_KEY")
        if [[ -n "$api_key_in_env" ]]; then
          info "Fixing ~/.claude/settings.json: renaming LINEAR_API_KEY → LINEAR_ACCESS_TOKEN..."
          "$VENV_DIR/bin/python" - "$api_key_in_env" <<'PYEOF'
import json, sys
from pathlib import Path
path = Path.home() / '.claude' / 'settings.json'
val = sys.argv[1]
with open(path) as f:
    cfg = json.load(f)
env = cfg.get('mcpServers', {}).get('linear', {}).setdefault('env', {})
env.pop('LINEAR_API_KEY', None)
env = {k: v for k, v in env.items() if not (isinstance(v, str) and '${' in v)}
env['LINEAR_ACCESS_TOKEN'] = val
cfg['mcpServers']['linear']['env'] = env
with open(path, 'w') as f:
    json.dump(cfg, f, indent=2)
    f.write('\n')
PYEOF
          ok "~/.claude/settings.json: LINEAR_ACCESS_TOKEN fixed"
          ((fixed_count++))
        else
          warn "~/.claude/settings.json has wrong MCP env key — fix manually after setting LINEAR_API_KEY"
          ((issues++))
        fi
      fi
    fi

    local figma_key
    figma_key=$(get_env_key "FIGMA_API_KEY")
    if [[ "$has_figma" == "yes" ]]; then
      ok "MCP: figma server configured"
    elif [[ -n "$figma_key" ]]; then
      info "Auto-adding figma MCP server to .mcp.json..."
      "$VENV_DIR/bin/python" - <<'PYEOF'
import json
path = '.mcp.json'
with open(path) as f:
    cfg = json.load(f)
cfg.setdefault('mcpServers', {})['figma'] = {
    'command': 'npx',
    'args': ['-y', 'figma-developer-mcp', '--stdio']
}
with open(path, 'w') as f:
    json.dump(cfg, f, indent=2)
    f.write('\n')
PYEOF
      ok "MCP: figma server added to .mcp.json"
      ((fixed_count++))
    else
      dim "    MCP: figma server not configured (no FIGMA_API_KEY — optional)"
    fi
  else
    warn ".mcp.json not found"
    dim "    Copy .mcp.json.example or run: resonance setup"
    ((issues++))
  fi

  # ── linear-mcp Bearer prefix fix ──────────────────────────────────────────
  # @linear/sdk uses `accessToken` → adds "Bearer " prefix.
  # Linear now rejects "Bearer lin_api_..." for PATs; must send the token raw.
  # Patch auth.js to use `apiKey` instead of `accessToken` for PAT init.
  local auth_js
  auth_js=$(node -e "console.log(require.resolve('linear-mcp/build/auth.js'))" 2>/dev/null || true)
  if [[ -z "$auth_js" ]]; then
    # Fallback: look in common global npm paths
    for try_path in \
      "$(npm root -g 2>/dev/null)/linear-mcp/build/auth.js" \
      "$HOME/.npm-global/lib/node_modules/linear-mcp/build/auth.js" \
      "/usr/local/lib/node_modules/linear-mcp/build/auth.js"; do
      [[ -f "$try_path" ]] && { auth_js="$try_path"; break; }
    done
  fi

  if [[ -n "$auth_js" && -f "$auth_js" ]]; then
    # Check specifically: does the LinearClient() PAT init still use accessToken (broken)?
    # The tokenData assignment also has `accessToken: config.accessToken` — skip that.
    # We need to detect `new LinearClient({` followed by `accessToken: config.accessToken`.
    if "$VENV_DIR/bin/python" - "$auth_js" <<'PYEOF' 2>/dev/null | grep -q "NEEDS_PATCH"; then
import sys, re
content = open(sys.argv[1]).read()
# Find the PAT LinearClient block: new LinearClient({ ... accessToken: config.accessToken ... })
if re.search(r'new LinearClient\(\{\s*accessToken:\s*config\.accessToken', content):
    print('NEEDS_PATCH')
PYEOF
      info "Patching linear-mcp auth.js: replacing accessToken → apiKey for PAT (Bearer prefix fix)..."
      sed -i.bak \
        's/new LinearClient({\s*accessToken: config\.accessToken/new LinearClient({ apiKey: config.accessToken/' \
        "$auth_js" 2>/dev/null || \
      "$VENV_DIR/bin/python" - "$auth_js" <<'PYEOF'
import sys, re
path = sys.argv[1]
content = open(path).read()
# Replace only the LinearClient PAT instantiation, not the tokenData assignment
patched = re.sub(
    r'(new LinearClient\(\{)\s*\n\s*accessToken: config\.accessToken,',
    r'\1\n                apiKey: config.accessToken,',
    content
)
open(path, 'w').write(patched)
PYEOF
      rm -f "${auth_js}.bak"
      ok "linear-mcp auth.js patched (PATs now sent without Bearer prefix)"
      ((fixed_count++))
    else
      ok "linear-mcp auth.js  (Bearer prefix fix already applied)"
    fi

    # Fix tool.types.js — add projectId/parentId/stateId/labelIds to linear_create_issue schema
    local types_js
    types_js="$(dirname "$auth_js")/core/types/tool.types.js"
    if [[ -f "$types_js" ]]; then
      local missing_schema_fields=()
      for field in projectId parentId stateId labelIds; do
        grep -q "\"$field\"" "$types_js" 2>/dev/null || missing_schema_fields+=("$field")
      done
      if [[ ${#missing_schema_fields[@]} -gt 0 ]]; then
        info "Patching linear-mcp tool.types.js: adding ${missing_schema_fields[*]} to linear_create_issue schema..."
        "$VENV_DIR/bin/python" - "$types_js" <<'PYEOF'
import sys, re

path = sys.argv[1]
content = open(path).read()

insert_before = '            },\n            required: ["title", "description", "teamId"],'

new_fields = '''                projectId: {
                    type: "string",
                    description: "Project ID to assign the issue to",
                    optional: true,
                },
                parentId: {
                    type: "string",
                    description: "Parent issue ID (UUID) to nest this issue under",
                    optional: true,
                },
                stateId: {
                    type: "string",
                    description: "Workflow state ID to set on creation",
                    optional: true,
                },
                labelIds: {
                    type: "array",
                    items: { type: "string" },
                    description: "List of label IDs to attach to the issue",
                    optional: true,
                },
'''

# Only patch if fields not already present
if 'projectId:' not in content:
    content = content.replace(insert_before, new_fields + insert_before, 1)
    open(path, 'w').write(content)
    print('patched')
else:
    print('already patched')
PYEOF
        ok "linear-mcp tool.types.js patched (create_issue now accepts projectId/parentId/stateId/labelIds)"
        ((fixed_count++))
      else
        ok "linear-mcp tool.types.js  (create_issue schema complete)"
      fi
    fi
  else
    warn "linear-mcp not found — cannot verify auth.js patch (install with: npm install -g linear-mcp)"
    ((issues++))
  fi

  # ────────────────────────────────────────────────────────────────────────────
  step "8/8" "Live Integration Tests"

  # Test 1: Python Linear client (orchestrator auth path)
  local api_key_live
  api_key_live=$(get_env_key "LINEAR_API_KEY")
  if [[ -n "$api_key_live" ]]; then
    local py_test_result
    py_test_result=$("$VENV_DIR/bin/python" - "$api_key_live" <<'PYEOF' 2>&1
import sys
sys.path.insert(0, '.')
from orchestrator.linear_client import LinearClient
try:
    client = LinearClient(sys.argv[1])
    viewer = client.get_viewer()
    teams = client.get_teams()
    client.close()
    print(f"OK:{viewer['name']}:{len(teams)}")
except Exception as e:
    print(f"FAIL:{e}")
PYEOF
    )
    case "$py_test_result" in
      OK:*) IFS=: read -r _ name n_teams <<< "$py_test_result"
            ok "Python Linear client  →  ${name} (${n_teams} team(s))" ;;
      FAIL:*) fail "Python Linear client failed: ${py_test_result#FAIL:}"; ((issues++)) ;;
      *) fail "Python Linear client unexpected output: ${py_test_result}"; ((issues++)) ;;
    esac
  else
    warn "Skipping Python client test — LINEAR_API_KEY not set"
    ((issues++))
  fi

  # Test 2: Node.js linear-mcp auth (MCP worker path — uses the Bearer-prefix fix)
  local node_bin
  node_bin=$(command -v node 2>/dev/null || true)
  if [[ -n "$node_bin" && -n "$auth_js" && -f "$auth_js" && -n "$api_key_live" ]]; then
    local mcp_auth_dir
    mcp_auth_dir=$(dirname "$auth_js")
    local node_test_result
    node_test_result=$(LINEAR_ACCESS_TOKEN="$api_key_live" "$node_bin" --input-type=module <<JSEOF 2>&1
import { LinearAuth } from '${auth_js}';
import { LinearGraphQLClient } from '${mcp_auth_dir}/graphql/client.js';
const auth = new LinearAuth();
auth.initialize({ type: 'pat', accessToken: process.env.LINEAR_ACCESS_TOKEN });
const graphql = new LinearGraphQLClient(auth.getClient());
try {
  const result = await graphql.getCurrentUser();
  const name = result.viewer?.name || result.viewer?.email || 'unknown';
  const hdr = auth.getClient().client.options?.headers?.Authorization || '';
  const hasBearer = hdr.startsWith('Bearer ');
  console.log('OK:' + name + ':' + (hasBearer ? 'BEARER_BUG' : 'NO_BEARER'));
} catch (e) {
  console.log('FAIL:' + e.message.slice(0, 120));
}
JSEOF
    )
    case "$node_test_result" in
      OK:*:NO_BEARER)
        IFS=: read -r _ name _ <<< "$node_test_result"
        ok "linear-mcp MCP auth  →  ${name}  (no Bearer prefix — correct)" ;;
      OK:*:BEARER_BUG)
        IFS=: read -r _ name _ <<< "$node_test_result"
        fail "linear-mcp MCP auth  →  ${name} authenticated BUT auth.js still sends Bearer prefix"
        warn "Run: ./wizard.sh check  to re-apply the patch"
        ((issues++)) ;;
      FAIL:*)
        fail "linear-mcp MCP auth failed: ${node_test_result#FAIL:}"
        dim "    This means worker agents will not have Linear MCP access."
        dim "    Check: npm install -g linear-mcp  then re-run this check."
        ((issues++)) ;;
      *)
        warn "linear-mcp MCP auth: unexpected output: ${node_test_result}"; ((issues++)) ;;
    esac
  elif [[ -z "$node_bin" ]]; then
    warn "node not found — cannot test linear-mcp auth (install Node.js)"
    ((issues++))
  elif [[ -z "$auth_js" ]]; then
    warn "linear-mcp not installed — cannot test MCP auth (npm install -g linear-mcp)"
    ((issues++))
  fi

  # Test 3: Verify worker env injection (runner.py injects LINEAR_ACCESS_TOKEN)
  if grep -q "LINEAR_ACCESS_TOKEN" orchestrator/runner.py 2>/dev/null; then
    ok "runner.py  →  injects LINEAR_ACCESS_TOKEN into worker env"
  else
    fail "runner.py does not inject LINEAR_ACCESS_TOKEN — worker agents will lack MCP auth"
    ((issues++))
  fi

  # Test 4: cc-pipeline .mcp.json has no broken ${...} env vars
  local cc_mcp=".claude/cc-pipeline/.mcp.json"
  if [[ -f "$cc_mcp" ]]; then
    if grep -q '\${' "$cc_mcp" 2>/dev/null; then
      fail "${cc_mcp} still has unexpanded \${...} env vars — fix with: ./wizard.sh check"
      ((issues++))
    else
      ok "${cc_mcp}  (clean — no unexpanded variables)"
    fi
  fi

  # ────────────────────────────────────────────────────────────────────────────
  echo ""
  echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo ""

  if [[ $issues -eq 0 ]]; then
    echo -e "${GREEN}${BOLD}✓ All checks passed.${RESET}"
    [[ $fixed_count -gt 0 ]] && echo -e "  Auto-fixed ${fixed_count} item(s) during this run."
    echo ""
    echo -e "  Ready to start:  ${BOLD}./onair.sh${RESET}"
  else
    echo -e "${YELLOW}${BOLD}⚠ ${issues} issue(s) need attention.${RESET}"
    [[ $fixed_count -gt 0 ]] && echo -e "  Auto-fixed ${fixed_count} item(s). Review the warnings above for what remains."
    echo ""
    echo -e "  Next steps:"
    echo -e "    ${BOLD}./wizard.sh check${RESET}  — re-run after fixing"
    echo -e "    ${BOLD}resonance doctor${RESET}   — quick status check"
    echo -e "    ${BOLD}resonance fix${RESET}      — re-apply Linear states/labels"
  fi
  echo ""
}

# ── Update ────────────────────────────────────────────────────────────────────

do_update() {
  header "Update Configuration"

  if [[ ! -f .env ]]; then
    fail ".env not found — run ./wizard.sh setup first."
    return
  fi

  ensure_resonance

  local KEYS=("LINEAR_API_KEY" "LINEAR_TEAM_ID" "LINEAR_PROJECT_ID" "FIGMA_API_KEY" "GITHUB_TOKEN")
  local DESCS=(
    "Linear personal API key  (Settings → API → Personal API keys)"
    "Linear team UUID         (from resonance setup or your Linear team URL)"
    "Linear project UUID      (optional — scopes orchestrator to one project)"
    "Figma API key            (optional — required for design_to_code tasks)"
    "GitHub token             (optional — required for PR creation)"
  )

  while true; do
    echo -e "${BOLD}What would you like to update?${RESET}"
    for i in "${!KEYS[@]}"; do
      local current masked
      current=$(get_env_key "${KEYS[$i]}")
      masked=$(mask_key "$current")
      printf "  %d)  %-26s  %s\n" "$((i+1))" "${KEYS[$i]}" "${DIM}${DESCS[$i]}${RESET}"
      printf "       %-26s  current: %s\n" "" "${DIM}${masked}${RESET}"
      echo ""
    done
    echo -e "  6)  ${BOLD}Fix Linear labels / states${RESET}   ${DIM}Create any missing required items in Linear${RESET}"
    echo -e "  7)  ${BOLD}Full health check${RESET}            ${DIM}Run check wizard${RESET}"
    echo -e "  8)  ${BOLD}Kill orchestrator${RESET}            ${DIM}Stop the running orchestrator process${RESET}"
    echo -e "  9)  ${BOLD}Restart orchestrator${RESET}         ${DIM}Kill and restart without TUI${RESET}"
    echo ""
    echo -e "  q)  Done\n"
    read -rp "Choice: " choice
    echo ""

    case "$choice" in
      1|2|3|4|5)
        local idx=$((choice - 1))
        local key="${KEYS[$idx]}"
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
      7) do_check ;;
      8) do_kill ;;
      9) do_restart ;;
      q|Q|"") break ;;
      *) warn "Invalid choice — enter 1–9 or q."; echo "" ;;
    esac
  done

  info "Running doctor to verify..."
  echo ""
  resonance doctor || true
}

# ── Kill / Restart ────────────────────────────────────────────────────────────

do_kill() {
  local PID_FILE="runs/orchestrator.pid"
  local pid=""

  [[ -f "$PID_FILE" ]] && pid=$(cat "$PID_FILE" 2>/dev/null)

  local ps_pids
  ps_pids=$(pgrep -f "orchestrator.main" 2>/dev/null || true)

  local killed=false

  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    info "Stopping orchestrator (PID $pid)..."
    kill "$pid" 2>/dev/null
    for i in 1 2 3 4 5; do
      sleep 1
      kill -0 "$pid" 2>/dev/null || break
    done
    kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
    ok "Orchestrator stopped (PID $pid)"
    killed=true
  fi

  for p in $ps_pids; do
    if [[ "$p" != "$pid" ]]; then
      kill "$p" 2>/dev/null && ok "Stopped orphaned orchestrator (PID $p)" || true
      killed=true
    fi
  done

  rm -f "$PID_FILE"

  [[ "$killed" == "false" ]] && warn "No running orchestrator found."
  echo ""
}

do_restart() {
  header "Restart Orchestrator"

  ensure_venv
  local PYTHON="$VENV_DIR/bin/python"

  do_kill

  local PID_FILE="runs/orchestrator.pid"
  mkdir -p runs/logs
  local ORCH_LOG="runs/logs/orchestrator-$(date +%Y%m%dT%H%M%S).log"

  info "Starting orchestrator..."
  "$PYTHON" -m orchestrator.main >> "$ORCH_LOG" 2>&1 &
  local new_pid=$!
  echo "$new_pid" > "$PID_FILE"

  sleep 1
  if kill -0 "$new_pid" 2>/dev/null; then
    ok "Orchestrator started (PID $new_pid, log: $ORCH_LOG)"
    dim "  → Open dashboard: ${BOLD}resonance watch${RESET}"
  else
    fail "Orchestrator failed to start — check: $ORCH_LOG"
    exit 1
  fi
  echo ""
}

# ── Wipe ──────────────────────────────────────────────────────────────────────

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
  [[ "$confirm" =~ ^[Yy]$ ]] || { info "Cancelled."; return; }

  rm -f .env
  rm -f runs/state.json runs/events.jsonl runs/commands.jsonl
  rm -rf runs/logs/
  ok "Credentials and runtime state removed."
  dim "  → Run ./wizard.sh to configure again."
  echo ""
}

# ── Entry point ───────────────────────────────────────────────────────────────

MODE="${1:-menu}"

case "$MODE" in
  ""|menu)   do_menu    ;;
  setup)     do_setup   ;;
  check)     do_check   ;;
  test)      do_test    ;;
  update)    do_update  ;;
  kill)      do_kill    ;;
  restart)   do_restart ;;
  wipe)      do_wipe    ;;
  overwrite) do_overwrite ;;
  *)
    echo ""
    echo -e "${BOLD}Resonance Wizard${RESET}"
    echo ""
    echo "  Usage: ./wizard.sh [command]"
    echo ""
    echo "  Commands:"
    echo "    (none)     Interactive menu"
    echo "    setup      First-time setup — credentials + Linear states/labels"
    echo "    check      Full health-check — diagnose and auto-fix everything"
    echo "    test       Run live integration tests (Python + MCP + worker env)"
    echo "    update     Update API keys or configuration"
    echo "    kill       Stop the running orchestrator"
    echo "    restart    Kill and restart the orchestrator (no TUI)"
    echo "    wipe       Remove credentials and clear all runtime state"
    echo "    overwrite  Redo everything from scratch"
    echo ""
    exit 1
    ;;
esac
