Set up the UI DOM Inspector so Claude Code can inspect the live browser during UI work.

This command handles the full setup in one run. It is safe to re-run — every step is idempotent.

---

## What you are setting up

Three layers need to be running before Claude can use the inspector:

1. **Chrome extension** — loaded once in Chrome; persists across browser restarts
2. **Bridge server** — local Node.js process at `http://127.0.0.1:47771`; receives data from the extension
3. **MCP server** — started by Claude Code via `.mcp.json`; reads from the bridge and exposes tools

---

## Step 1 — Install dependencies

Check whether `ui-dom-inspector/node_modules` exists.

If it does not, run:

```bash
cd ui-dom-inspector && npm install
```

Report what was installed or confirm it was already present.

---

## Step 2 — Check and start the bridge

Check whether the bridge is already running:

```bash
curl -s --max-time 2 http://127.0.0.1:47771/health
```

If it returns a valid JSON response, the bridge is running. Report its status and continue.

If it is not running, start it as a background process:

```bash
REPO_ROOT=$(pwd)
nohup node "$REPO_ROOT/ui-dom-inspector/bridge/server.js" \
  > "$REPO_ROOT/ui-dom-inspector/bridge/bridge.log" 2>&1 &
echo $! > "$REPO_ROOT/ui-dom-inspector/bridge/bridge.pid"
```

Wait 2 seconds, then check health again:

```bash
curl -s --max-time 3 http://127.0.0.1:47771/health
```

Report the result. If it fails, show the last 20 lines of `ui-dom-inspector/bridge/bridge.log` to help diagnose the issue.

---

## Step 3 — Set up auto-start (macOS launchd)

This keeps the bridge running after reboots and restarts it if it crashes.

Check whether the launchd agent already exists:

```bash
ls ~/Library/LaunchAgents/com.queenone.ui-dom-inspector.plist 2>/dev/null
```

If it does not exist, generate and install it:

```bash
NODE_BIN=$(which node)
REPO_ROOT=$(pwd)
PLIST_PATH="$HOME/Library/LaunchAgents/com.queenone.ui-dom-inspector.plist"

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.queenone.ui-dom-inspector</string>
    <key>ProgramArguments</key>
    <array>
        <string>$NODE_BIN</string>
        <string>$REPO_ROOT/ui-dom-inspector/bridge/server.js</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$REPO_ROOT/ui-dom-inspector</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$REPO_ROOT/ui-dom-inspector/bridge/bridge.log</string>
    <key>StandardErrorPath</key>
    <string>$REPO_ROOT/ui-dom-inspector/bridge/bridge.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
PLIST
```

Then load it:

```bash
launchctl load ~/Library/LaunchAgents/com.queenone.ui-dom-inspector.plist 2>/dev/null || \
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.queenone.ui-dom-inspector.plist
```

If the plist already existed, check whether the service is loaded:

```bash
launchctl list | grep com.queenone.ui-dom-inspector
```

If it is listed, report it is already running. If it is not listed, run the load command above.

After installing or confirming, verify the bridge is responding:

```bash
curl -s --max-time 3 http://127.0.0.1:47771/health
```

---

## Step 4 — Verify the MCP stanza in .mcp.json

Read `.mcp.json` and check whether `ui-dom-inspector` is present in `mcpServers`.

If it is missing, add it. The stanza to add is:

```json
"ui-dom-inspector": {
  "command": "node",
  "args": ["ui-dom-inspector/mcp-server/server.js"],
  "env": {
    "UI_DOM_INSPECTOR_BRIDGE_URL": "http://127.0.0.1:47771"
  }
}
```

After adding it, tell the user: **Claude Code needs to be restarted for the new MCP server to connect.** The MCP server will be started automatically by Claude Code on next launch.

If the stanza is already present, confirm it and continue.

---

## Step 5 — Chrome extension instructions

Print these instructions clearly:

```
Chrome extension setup (one-time, takes 30 seconds):

1. Open Chrome and go to: chrome://extensions
2. Enable Developer Mode (toggle in the top-right corner)
3. Click "Load unpacked"
4. Select this folder:
   <REPO_ROOT>/ui-dom-inspector/extension

The "UI DOM Inspector" icon will appear in your Chrome toolbar.
You only need to do this once. The extension persists across Chrome restarts.

To reload the extension after code changes:
   Go to chrome://extensions and click the reload icon on the UI DOM Inspector card.
```

Replace `<REPO_ROOT>` with the actual absolute path.

---

## Step 6 — Final status summary

Run a final health check:

```bash
curl -s http://127.0.0.1:47771/health
```

Then print a clear summary:

```
UI DOM Inspector — setup complete

  Bridge:     running at http://127.0.0.1:47771
  Auto-start: installed (restarts on reboot and crash)
  MCP server: configured in .mcp.json
  Extension:  load manually in Chrome if not done yet (see instructions above)

Next steps:
  1. Restart Claude Code so the MCP server connects
  2. Load the Chrome extension if not done yet
  3. Open your dev server in Chrome and click "Pin current tab" in the extension popup
  4. Claude can now call ui_dom_inspector_* tools during qo-ui-analyze, qo-ui-build, qo-ui-qa
```

---

## Troubleshooting guidance

If the bridge fails to start, check for port conflicts:

```bash
lsof -i :47771
```

If something is using the port, either stop it or change the bridge port with `UI_DOM_INSPECTOR_BRIDGE_PORT=<port>` in the launchd plist and `.mcp.json` env.

If the launchd agent fails to load, show the exact error and suggest:

```bash
launchctl error <exit-code>
```

to look up the exit code meaning.

If `node` is not found in the launchd context, confirm that the PATH in the plist includes the directory where node is installed (shown by `which node`).
