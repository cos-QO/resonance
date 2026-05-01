# UI DOM Inspector

A three-layer browser inspection tool for supervised UI work.

It gives Claude Code live visibility into a real rendered page — not just screenshots, but computed styles, element structure, bounds, and component hints — so that `qo-ui-analyze`, `qo-ui-build`, and `qo-ui-qa` can work with real data instead of guessing.

---

## What it does

You pin a browser tab. The Chrome extension watches that tab. Claude reads from it via an MCP server.

When you select an element in the page, the extension captures its styles, bounds, ancestry, and component hints and pushes that data to a local bridge server. Claude can then call MCP tools to inspect the element, view a screenshot, get diagnostics, or find out which URL to hand to Playwright.

```
┌─────────────────────────────────────────────────────────┐
│  Chrome tab (your running UI)                           │
│                                                         │
│  ┌─────────────────────────────────┐                   │
│  │  Chrome extension               │                   │
│  │  - popup: pin tab, select, snap │                   │
│  │  - content script: DOM, styles  │                   │
│  │  - service worker: screenshots  │                   │
│  └──────────────┬──────────────────┘                   │
└─────────────────│───────────────────────────────────────┘
                  │ HTTP POST
                  ▼
        ┌─────────────────┐
        │  Bridge server  │  http://127.0.0.1:47771
        │  (Node.js)      │  stores session state
        └────────┬────────┘  + snapshot artifacts
                 │ HTTP GET
                 ▼
        ┌─────────────────┐
        │  MCP server     │  stdio transport
        │  (Node.js)      │  exposes Claude tools
        └────────┬────────┘
                 │ MCP tools
                 ▼
        ┌─────────────────┐
        │  Claude Code    │
        │  qo-ui-analyze  │
        │  qo-ui-build    │
        │  qo-ui-qa       │
        └─────────────────┘
```

---

## Parts

| Directory | What it is |
|---|---|
| `extension/` | Chrome extension (MV3): popup, content script, service worker, overlay |
| `bridge/` | Local HTTP server that receives data from the extension |
| `mcp-server/` | MCP server that exposes bridge data to Claude as tools |
| `scripts/` | Setup checker |
| `docs/` | Implementation notes |

---

## Quick start

### 1. Install dependencies

```bash
cd ui-dom-inspector
npm install
```

### 2. Start the bridge

```bash
npm run bridge
```

The bridge listens at `http://127.0.0.1:47771`. Keep this terminal open.

### 3. Start the MCP server

In a second terminal:

```bash
npm run mcp
```

Or add it to Claude Code's MCP config (see below) and let Claude Code manage the process.

### 4. Load the Chrome extension

1. Open `chrome://extensions`
2. Enable **Developer Mode** (toggle, top right)
3. Click **Load unpacked**
4. Select the `ui-dom-inspector/extension` folder

The **UI DOM Inspector** icon appears in your Chrome toolbar.

### 5. Verify setup

```bash
npm run check
```

Or check the bridge health directly:

```bash
curl http://127.0.0.1:47771/health
```

---

## Enabling the MCP in Claude Code

Add this stanza to your project `.mcp.json`:

```json
{
  "ui-dom-inspector": {
    "command": "node",
    "args": ["ui-dom-inspector/mcp-server/server.js"],
    "env": {
      "UI_DOM_INSPECTOR_BRIDGE_URL": "http://127.0.0.1:47771"
    }
  }
}
```

This is intentionally not added to the repo's `.mcp.json` by default. Enable it when you are ready to use the inspector in your workflow.

---

## How to use it

### Pinning a tab

There are two ways to pin a tab.

**Manual (user-initiated):** Open the extension popup and click **Pin current tab as target**. This locks the extension's target to that specific tab immediately.

**Automatic (agent-initiated):** The agent can call the `ui_dom_inspector_pin_tab` MCP tool with a URL. The tool enqueues a `pin-tab` command on the bridge; the content script picks it up within 500 ms, relays it to the service worker, which finds or opens the tab and pins it. No popup click required. Use this at the start of a session when the dev server is already running but no tab has been pinned yet.

```
Agent calls ui_dom_inspector_pin_tab("http://localhost:3000")
  → bridge enqueues command
  → any open tab's content script relays to service worker
  → service worker finds or opens the tab, pins it
  → MCP tool polls until confirmed (≤10 s)
```

If the URL is not yet open in Chrome and `openIfMissing` is `true` (the default), the service worker opens a new tab automatically.

Every subsequent action — select element, capture snapshot, send page state — operates on the pinned tab regardless of which tab you have in the foreground.

The pinned tab URL is also posted to the bridge so Claude can read it and tell Playwright which URL to navigate to.

### Selecting an element

1. Click **Select element** in the popup. The button shows an active/cancel state.
2. Switch to the pinned tab. The cursor becomes a crosshair.
3. Hover to preview elements (blue dashed outline).
4. Click an element to select it (orange solid outline).
5. The extension immediately pushes the element data to the bridge. No manual send needed.
6. Press **Escape** to cancel selection without selecting anything.

### Capturing a snapshot

Click **Capture snapshot** in the popup. The service worker captures a JPEG screenshot of the pinned tab and saves it to `ui-dom-inspector/artifacts/`.

### Bridge connection status

The popup header shows a dot and label:
- Green dot + "connected" → bridge is running
- Red dot + "offline" → start the bridge with `npm run bridge`

---

## MCP tools

Claude can call these tools when the MCP server is connected:

| Tool | What it returns |
|---|---|
| `ui_dom_inspector_health` | Bridge status, whether session and snapshot data are present |
| `ui_dom_inspector_pin_tab` | Pin a URL as the supervised tab — finds or opens the tab, no popup click needed |
| `ui_dom_inspector_get_pinned_tab` | URL and title of the pinned tab — use this to tell Playwright where to navigate |
| `ui_dom_inspector_get_selected_element` | Selector, tag, role, text, classes, bounds, computed styles, ancestry, component hints |
| `ui_dom_inspector_get_page_state` | Page URL, title, and selected element data |
| `ui_dom_inspector_get_latest_snapshot` | The actual screenshot image (JPEG, returned as image content) |
| `ui_dom_inspector_get_visual_diagnostics` | Concise diagnostics summary for the selected element: bounds, hints, ancestry, styles |

---

## Playwright coordination

The pinned tab URL connects the inspector to Playwright.

Typical pattern at the start of a new session (no tab pinned yet):

1. Agent starts the dev server (e.g. `npm run dev`)
2. Agent calls `ui_dom_inspector_pin_tab("http://localhost:3000")` — extension opens and pins the tab automatically
3. Agent calls `ui_dom_inspector_get_pinned_tab` to confirm the URL
4. Agent tells Playwright to navigate to the same URL

Typical pattern when the user has already pinned a tab:

1. Agent calls `ui_dom_inspector_get_pinned_tab` to get that URL
2. Agent tells Playwright to navigate to the same URL
3. Playwright takes its own screenshots; the inspector adds element-level detail
4. Both tools are working on the same page

---

## Bridge API reference

The bridge runs at `http://127.0.0.1:47771` by default. Port is configurable via `UI_DOM_INSPECTOR_BRIDGE_PORT`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Returns bridge status, pinned tab, and session summary |
| `GET` | `/session/current` | Returns full session state: payload, snapshot, pinned tab |
| `POST` | `/session/update` | Stores a new page state payload (sent by extension after element selection) |
| `POST` | `/snapshot` | Stores a screenshot artifact (sent by service worker) |
| `GET` | `/session/pinned-tab` | Returns the currently pinned tab info |
| `POST` | `/session/pinned-tab` | Sets the pinned tab (sent by popup on manual pin, or service worker on agent-initiated pin) |
| `DELETE` | `/session/pinned-tab` | Clears the pinned tab |
| `POST` | `/commands/enqueue` | Queues a command for the content script — supports `get-page-state`, `capture-snapshot`, `pin-tab` |
| `GET` | `/commands/poll` | Content script polls this every 500 ms to consume the next queued command |

---

## What is not built yet

- Selected-element crop (screenshot cropped to element bounds)
- Richer token diagnostics (matching computed values to design token source)
- Richer component identity (React component names beyond heuristics)
- Polished overlay panel (currently just outline highlights)

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `UI_DOM_INSPECTOR_BRIDGE_PORT` | `47771` | Port for the bridge server |
| `UI_DOM_INSPECTOR_BRIDGE_URL` | `http://127.0.0.1:47771` | Bridge URL used by the MCP server |
