#!/usr/bin/env bash
# wizard.sh — Queen One Claude Code Setup Wizard
# Run once from the Fresh/ project root to get everything ready.

set -euo pipefail

# ── Colours ───────────────────────────────────────────────────────────────────
BOLD='\033[1m'
DIM='\033[2m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC}  $*"; }
warn() { echo -e "  ${YELLOW}⚠${NC}   $*"; }
err()  { echo -e "  ${RED}✗${NC}  $*"; }
step() { echo -e "  ${CYAN}→${NC}  $*"; }
h()    { echo -e "\n${BOLD}${BLUE}$*${NC}"; }

ask_secret() {
  local label="$1" var="$2"
  echo -ne "  ${BOLD}${label}${NC}${DIM} (hidden, Enter to skip)${NC}: "
  read -rs val; echo
  printf -v "$var" '%s' "$val"
}

# ── Guard: must run from Fresh/ root ─────────────────────────────────────────
if [[ ! -f ".mcp.json" || ! -d "ui-dom-inspector" || ! -d ".claude" ]]; then
  err "Run this script from the Fresh/ project root (where .mcp.json and .claude/ live)."
  exit 1
fi

PROJECT_ROOT="$(pwd)"

# ── Welcome ───────────────────────────────────────────────────────────────────
clear
echo -e "${BOLD}${BLUE}"
cat << 'BANNER'
  ╔══════════════════════════════════════════════╗
  ║   Queen One  ·  Claude Code Setup Wizard    ║
  ╚══════════════════════════════════════════════╝
BANNER
echo -e "${NC}"
echo "  Sets up the full QO pipeline in five steps:"
echo "    1.  Check prerequisites"
echo "    2.  Configure API keys"
echo "    3.  Install inspector dependencies"
echo "    4.  Start the bridge (auto-start on login)"
echo "    5.  Load the Chrome extension"
echo ""
read -rp "  Press Enter to begin…"


# ── Step 1: Prerequisites ─────────────────────────────────────────────────────
h "1 / 5   Prerequisites"
echo ""

PREREQS_OK=true

if command -v node &>/dev/null; then
  ok "Node $(node --version)"
else
  err "Node.js not found — install from https://nodejs.org then re-run."
  PREREQS_OK=false
fi

if command -v npm &>/dev/null; then
  ok "npm $(npm --version)"
else
  err "npm not found."
  PREREQS_OK=false
fi

if command -v python3 &>/dev/null; then
  ok "python3 $(python3 --version 2>&1 | cut -d' ' -f2)"
else
  err "python3 not found — needed to patch .mcp.json."
  PREREQS_OK=false
fi

CHROME_FOUND=false
for p in \
  "/Applications/Google Chrome.app" \
  "/Applications/Chromium.app" \
  "/Applications/Google Chrome Canary.app"
do
  if [[ -d "$p" ]]; then
    ok "Chrome found: $p"
    CHROME_FOUND=true
    break
  fi
done
[[ "$CHROME_FOUND" == false ]] && warn "Chrome not found in /Applications — you can still load the extension manually."

[[ "$PREREQS_OK" == false ]] && { echo ""; err "Fix the above and re-run."; exit 1; }


# ── Step 2: API keys ──────────────────────────────────────────────────────────
h "2 / 5   API Keys"
echo ""
echo "  Keys are written into .mcp.json. Leave blank to skip that MCP server."
echo ""

ask_secret "Figma API key         " FIGMA_KEY
ask_secret "GitHub personal token " GITHUB_TOKEN
ask_secret "Mermaid chart token   " MERMAID_TOKEN

echo ""
ok "Linear uses browser OAuth — no key needed. Authenticate on first use via /mcp in Claude Code."

# Patch .mcp.json using python3 so JSON stays valid
python3 - "$PROJECT_ROOT/.mcp.json" "$FIGMA_KEY" "$GITHUB_TOKEN" "$MERMAID_TOKEN" << 'PYEOF'
import json, sys

path, figma, github, mermaid = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

with open(path) as f:
    cfg = json.load(f)

s = cfg.setdefault("mcpServers", {})

if figma and "figma" in s:
    s["figma"].setdefault("env", {})["FIGMA_API_KEY"] = figma

if github and "github" in s:
    s["github"].setdefault("env", {})["GITHUB_PERSONAL_ACCESS_TOKEN"] = github

if mermaid and "mermaid" in s:
    s["mermaid"].setdefault("headers", {})["Authorization"] = mermaid

with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")
PYEOF

ok ".mcp.json updated"


# ── Step 3: Inspector dependencies ───────────────────────────────────────────
h "3 / 5   Inspector dependencies"
echo ""

INSP="$PROJECT_ROOT/ui-dom-inspector"
step "npm install in ui-dom-inspector/ …"
(cd "$INSP" && npm install --silent)
ok "Dependencies installed"


# ── Step 4: Bridge ───────────────────────────────────────────────────────────
h "4 / 5   Bridge"
echo ""

BRIDGE_SCRIPT="$INSP/bridge/server.js"
BRIDGE_LOG="$INSP/bridge/bridge.log"
LABEL="com.queenone.ui-dom-inspector-bridge"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
NODE_BIN="$(command -v node)"

# Stop existing instance if already loaded
if launchctl list "$LABEL" &>/dev/null; then
  step "Stopping existing bridge instance…"
  launchctl unload "$PLIST" 2>/dev/null || true
fi

step "Writing launchd plist → $PLIST"
cat > "$PLIST" << PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>             <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${NODE_BIN}</string>
    <string>${BRIDGE_SCRIPT}</string>
  </array>
  <key>RunAtLoad</key>         <true/>
  <key>KeepAlive</key>         <true/>
  <key>StandardOutPath</key>   <string>${BRIDGE_LOG}</string>
  <key>StandardErrorPath</key> <string>${BRIDGE_LOG}</string>
</dict>
</plist>
PLIST_EOF

launchctl load "$PLIST"
sleep 1

if curl -sf http://127.0.0.1:47771/health | grep -q '"ok":true'; then
  ok "Bridge running on port 47771 — auto-starts on login"
else
  warn "Bridge may still be starting. Check: $BRIDGE_LOG"
fi


# ── Step 5: Chrome extension ─────────────────────────────────────────────────
h "5 / 5   Chrome extension"
echo ""

EXT_PATH="$INSP/extension"

echo "  Chrome extensions can't be loaded automatically."
echo "  Follow these steps:"
echo ""
echo -e "  ${BOLD}1.${NC} Open: ${CYAN}chrome://extensions${NC}"
echo -e "  ${BOLD}2.${NC} Enable ${BOLD}Developer Mode${NC} (toggle top-right)"
echo -e "  ${BOLD}3.${NC} Click ${BOLD}Load unpacked${NC}"
echo -e "  ${BOLD}4.${NC} Select this folder:"
echo ""
echo -e "     ${CYAN}${EXT_PATH}${NC}"
echo ""

# Copy extension path to clipboard (macOS)
if command -v pbcopy &>/dev/null; then
  echo -n "$EXT_PATH" | pbcopy
  ok "Extension path copied to clipboard — paste it in the file picker."
fi

# Open the extensions page
if command -v open &>/dev/null; then
  open "chrome://extensions" 2>/dev/null || true
fi


# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}"
cat << 'DONE'
  ╔══════════════════════════════════════════════╗
  ║   Setup complete — ready to use!            ║
  ╚══════════════════════════════════════════════╝
DONE
echo -e "${NC}"
echo "  What to do next:"
echo ""
echo -e "  ${BOLD}1.${NC} Load the Chrome extension (step 5 above)"
echo -e "  ${BOLD}2.${NC} Open this folder in Claude Code"
echo -e "  ${BOLD}3.${NC} Run ${CYAN}/mcp${NC} to authenticate Linear in the browser"
echo -e "  ${BOLD}4.${NC} Open your target page in Chrome → click the extension icon → pin the tab"
echo -e "  ${BOLD}5.${NC} Run ${CYAN}/qo-ui-kickoff${NC} to start your first UI task"
echo ""
echo -e "  ${DIM}Bridge log: $BRIDGE_LOG${NC}"
echo ""
