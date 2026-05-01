# MCP Server

Exposes the UI DOM Inspector to Claude Code as MCP tools.

It reads from the local bridge (`http://127.0.0.1:47771`) and serves the data over the stdio MCP transport so Claude can call it directly during `qo-ui-analyze`, `qo-ui-build`, and `qo-ui-qa`.

---

## Start

```bash
cd ui-dom-inspector
npm run mcp
```

Or let Claude Code manage it via the MCP config (preferred):

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

---

## Tools

### `ui_dom_inspector_health`

Check whether the bridge is running and whether it has active session data.

Returns bridge port, `hasSession`, `hasSnapshot`, and `pinnedTab`.

Use this first to confirm the inspector is live before calling other tools.

---

### `ui_dom_inspector_pin_tab`

Pin a specific URL as the supervised tab — without requiring the user to click the popup.

Parameters:
- `url` (string, required) — full URL to pin, e.g. `http://localhost:3000`
- `openIfMissing` (boolean, default `true`) — if no tab with this URL is currently open, open one automatically

Use this at the start of a session when the dev server is running but no tab has been pinned yet. The tool enqueues a `pin-tab` command on the bridge; the content script picks it up within 500 ms, relays it to the service worker, which resolves or opens the tab and registers it as the pinned target. The tool polls until the bridge confirms the pin (up to 10 s).

Returns `{ ok: true, pinnedTab: { tabId, url, title, pinnedAt } }` on success, or `{ ok: false, error }` if the timeout is reached.

**Prerequisite:** At least one browser tab must be open so the content script poll can relay the command to the service worker.

---

### `ui_dom_inspector_get_pinned_tab`

Returns the URL and title of the tab the user has pinned as the supervised target.

**This is the Playwright coordination tool.** Use it to find out which URL to navigate to so Playwright and the inspector are both watching the same page.

```json
{
  "ok": true,
  "pinnedTab": {
    "tabId": 42,
    "url": "http://localhost:3000/campaigns",
    "title": "Campaigns",
    "pinnedAt": "2026-05-01T14:00:00Z"
  }
}
```

Returns `"pinnedTab": null` if the user has not pinned a tab yet.

---

### `ui_dom_inspector_get_selected_element`

Returns the full element payload for the element the user last selected in the browser.

Includes:
- selector
- tag, role, text
- class list
- bounding box (x, y, width, height)
- computed styles (color, background, border-radius, font family/size/weight, padding, margin, display, gap, dimensions)
- ancestry (up to 8 levels)
- children summary (up to 12 children)
- component hints (Button, Input, Modal, Navigation, Card, ToggleGroup, Chip)

---

### `ui_dom_inspector_get_page_state`

Returns the latest page state: page URL, title, and selected element (same payload as above but wrapped with page context).

**Auto-triggers a fresh capture.** Enqueues a `get-page-state` command on the bridge and waits up to 10 s for the content script to push updated data. No manual "Send page state" click needed.

---

### `ui_dom_inspector_get_latest_snapshot`

Returns the most recent screenshot as a **JPEG image** (not just a file path — the actual image content).

Also returns metadata: `pageUrl`, `capturedAt`, `filename`.

**Auto-triggers a fresh capture.** Enqueues a `capture-snapshot` command on the bridge and waits up to 10 s for the service worker to deliver the screenshot. No manual "Capture snapshot" click needed.

Use this to visually verify the current page state.

---

### `ui_dom_inspector_get_visual_diagnostics`

Returns a concise diagnostics summary focused on the selected element.

Parameters:
- `includeComputedStyles` (boolean, default `true`) — whether to include the full computed styles block

Returns: selector, tag, role, text, bounds, component hints, ancestry, and optionally computed styles.

Use this during QA to quickly audit what the selected element looks like without the full noise of `get_selected_element`.

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `UI_DOM_INSPECTOR_BRIDGE_URL` | `http://127.0.0.1:47771` | Bridge URL to read from |

---

## How it fits into the workflow

```
session start (no tab pinned yet):
  call ui_dom_inspector_pin_tab             → open and pin the dev server URL automatically

qo-ui-analyze:
  call ui_dom_inspector_get_pinned_tab      → confirm which page to inspect
  call ui_dom_inspector_get_page_state      → see existing DOM structure
  call ui_dom_inspector_get_visual_diagnostics → inspect specific elements

qo-ui-build:
  call ui_dom_inspector_get_pinned_tab      → tell Playwright the URL
  call ui_dom_inspector_get_latest_snapshot → see current visual state
  call ui_dom_inspector_get_selected_element → verify a specific element's styles

qo-ui-qa:
  call ui_dom_inspector_get_visual_diagnostics → audit token and component usage
  call ui_dom_inspector_get_latest_snapshot → visual evidence for the QA report
```
