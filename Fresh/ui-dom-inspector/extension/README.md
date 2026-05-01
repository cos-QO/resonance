# Chrome Extension

Manifest V3 Chrome extension for the UI DOM Inspector.

It runs inside the browser and is the only layer with direct access to the live page — DOM, computed styles, element geometry, and screenshots.

---

## Files

| File | Role |
|---|---|
| `manifest.json` | Extension manifest: permissions, content scripts, service worker, popup |
| `popup.html` | Extension popup UI — what you see when you click the toolbar icon |
| `popup.js` | Popup logic: tab pinning, button actions, bridge health check |
| `content-script.js` | Injected into every page: selection mode, element inspection, DOM access |
| `service-worker.js` | Background: handles screenshot capture, relays page state to bridge |
| `overlay.css` | Injected styles: crosshair cursor during selection, hover/selected outlines |
| `icon.svg` | Source vector icon asset |
| `icon-16.png` / `icon-32.png` / `icon-48.png` / `icon-128.png` | Manifest-ready extension icons |

---

## Popup

The popup is the control panel.

**Header**: shows bridge connection status (green dot = connected, red = bridge not running).

**Target Tab section**:
- Displays the pinned tab URL when one is set
- **Pin toggle** — click to pin the current tab as the inspection target (toggle on = pinned, toggle off = unpinned). Replaces the old two-button Pin/Clear approach.

**Inspect section**:
- **Select element** — starts element selection mode on the pinned tab (or active tab if none is pinned). Click again or press Escape to cancel.
- **Capture snapshot** — takes a JPEG screenshot of the pinned tab and saves it via the bridge
- **Send page state** — manually pushes the current page state (URL + selected element) to the bridge. Normally this happens automatically after selection.

**Log area**: shows status messages, errors, and confirmations.

---

## Content script

Injected into every page at `document_idle`.

**Selection mode**:
- When activated, adds `ui-dom-inspector-selecting` to `document.body` (triggers crosshair cursor via CSS)
- On mousemove: adds `ui-dom-inspector-hover` class to element under cursor
- On click: locks selection, removes hover, adds `data-ui-dom-inspector-selected` attribute
- On Escape: exits selection mode without selecting

**After selection**:
- Immediately calls `fetch` to post the page state (URL + full element payload) to the bridge at `http://127.0.0.1:47771/session/update`
- Sends `ui-dom-inspector:selection-complete` runtime message to the popup if it is still open

**Agent command polling**:
- Polls `GET /commands/poll` every 500 ms
- When the agent enqueues a command on the bridge, the content script picks it up and executes it — no manual popup clicks needed
- Supported commands:
  - `get-page-state` — pushes current DOM state to the bridge
  - `capture-snapshot` — delegates screenshot to service worker
  - `pin-tab` — relays the pin request to the service worker, which finds or opens the tab and registers it as the pinned target
- Also relays `agentActive` from each poll response to the service worker so the badge updates within 500 ms of a tool call starting

**Element payload** includes:
- selector (id, data-qo-id, or tag+classes)
- tag, role, text content
- full class list
- bounding box (x, y, width, height — rounded integers)
- computed styles (color, background, border-radius, font, spacing, display, gap, dimensions)
- ancestry (up to 8 levels)
- children summary (up to 12 children)
- component hints (Button, Input, Modal, Navigation, Card, ToggleGroup, Chip)

---

## Service worker

Handles messages that require Chrome API access the content script does not have.

**`ui-dom-inspector:capture-snapshot`**:
- Calls `chrome.tabs.captureVisibleTab` using the Promise API
- Posts the JPEG data URL + page URL to the bridge `/snapshot` endpoint
- Returns the saved artifact metadata

**`ui-dom-inspector:bridge-page-state`**:
- Posts a page state payload to the bridge `/session/update` endpoint
- Used by the "Send page state" button as a manual re-send

**`ui-dom-inspector:auto-capture`**:
- Triggered by the content script when a `capture-snapshot` command arrives from the bridge
- Reads the pinned tab from session storage, calls `captureVisibleTab`, posts the JPEG to `/snapshot`

**`ui-dom-inspector:pin-tab`**:
- Triggered by the content script when a `pin-tab` command arrives from the bridge
- Receives `{ url, openIfMissing }` from the content script relay
- Calls `chrome.tabs.query` to find an existing tab matching the URL; if none is found and `openIfMissing` is true, calls `chrome.tabs.create`
- Writes the resolved tab to `chrome.storage.session` and POSTs to `/session/pinned-tab` on the bridge
- Returns `{ ok, tabId, url }` to the content script

**`ui-dom-inspector:set-badge`**:
- Triggered by the content script to relay `agentActive` state from poll responses
- Calls `setBadge("agent-active")` or `setBadge("connected")` so the badge turns yellow during agent tool calls without waiting for the 1-minute health alarm

---

## Permissions

| Permission | Why |
|---|---|
| `activeTab` | Access the current tab for snapshot capture |
| `tabs` | Read tab URL, title, favicon; switch to pinned tab |
| `storage` | Persist pinned tab across popup open/close (session storage) |
| `scripting` | Inject messages into the content script |
| `host_permissions: <all_urls>` | Content script runs on any page |
| `host_permissions: http://127.0.0.1:47771/*` | Content script can fetch the local bridge |

---

## Loading in Chrome

1. Open `chrome://extensions`
2. Enable **Developer Mode**
3. Click **Load unpacked**
4. Select this `extension/` folder

To reload after code changes: click the reload icon on the extension card.

---

## Icon

The extension now includes:

- `icon.svg` as the source asset
- `icon-16.png`
- `icon-32.png`
- `icon-48.png`
- `icon-128.png`

These PNGs are wired into `manifest.json`, so Chrome should show the custom icon after the extension is reloaded.

The icon visually represents:

- a UI surface
- a highlighted inspected element
- a lens / inspector metaphor

If Chrome still shows the old icon, reload the unpacked extension from `chrome://extensions`.
