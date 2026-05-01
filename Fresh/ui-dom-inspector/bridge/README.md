# Bridge Server

Local HTTP server at `http://127.0.0.1:47771`.

It is the connector between the Chrome extension and the MCP server. The extension pushes data to it; the MCP server reads from it.

---

## Start

```bash
cd ui-dom-inspector
npm run bridge
```

---

## What it stores

The bridge holds one session in memory (and persists it to `bridge/session-state.json`):

- **`payload`** — the latest page state sent by the extension: page URL + title + selected element data
- **`latestSnapshot`** — metadata about the most recent screenshot artifact (path, filename, page URL, timestamp)
- **`pinnedTab`** — the tab the user has pinned as the supervised target: tabId, URL, title

Screenshots are saved as JPEG files in `../artifacts/` with timestamped filenames.

---

## API

### `GET /health`

Returns bridge status.

```json
{
  "ok": true,
  "port": 47771,
  "hasSession": true,
  "hasSnapshot": true,
  "pinnedTab": { "tabId": 42, "url": "http://localhost:3000/campaigns", "title": "Campaigns" }
}
```

---

### `GET /session/current`

Returns the full current session state.

```json
{
  "ok": true,
  "session": {
    "updatedAt": "2026-05-01T14:00:00Z",
    "payload": { "page": { "url": "...", "title": "..." }, "selectedElement": { ... } },
    "latestSnapshot": { "pageUrl": "...", "capturedAt": "...", "artifact": { "path": "...", "filename": "..." } },
    "pinnedTab": { "tabId": 42, "url": "...", "title": "..." }
  }
}
```

---

### `POST /session/update`

Stores a new page state payload. Called by the extension content script after element selection and by the "Send page state" button.

Request body:
```json
{
  "page": { "url": "http://localhost:3000/campaigns", "title": "Campaigns" },
  "selectedElement": { "selector": "#filter-panel", "tag": "div", ... }
}
```

---

### `POST /snapshot`

Saves a screenshot. Called by the service worker after `captureVisibleTab`.

Request body:
```json
{
  "pageUrl": "http://localhost:3000/campaigns",
  "screenshotDataUrl": "data:image/jpeg;base64,..."
}
```

Response:
```json
{
  "ok": true,
  "snapshot": {
    "pageUrl": "http://localhost:3000/campaigns",
    "capturedAt": "2026-05-01T14:00:00Z",
    "artifact": { "path": "/absolute/path/to/artifacts/page-snapshot-2026-05-01T14-00-00Z.jpg", "filename": "page-snapshot-2026-05-01T14-00-00Z.jpg" }
  }
}
```

---

### `GET /session/pinned-tab`

Returns the currently pinned tab.

```json
{
  "ok": true,
  "pinnedTab": { "tabId": 42, "url": "http://localhost:3000/campaigns", "title": "Campaigns", "pinnedAt": "2026-05-01T14:00:00Z" }
}
```

Returns `"pinnedTab": null` if no tab is pinned.

---

### `POST /session/pinned-tab`

Sets the pinned tab. Called by the extension popup when the user clicks "Pin current tab".

Request body:
```json
{ "tabId": 42, "url": "http://localhost:3000/campaigns", "title": "Campaigns" }
```

---

### `DELETE /session/pinned-tab`

Clears the pinned tab. Called when the user toggles the pin off in the popup.

---

### `POST /commands/enqueue`

Queues a command for the content script to execute. Called by the MCP server when a tool needs fresh data.

Supported command types:

```json
{ "type": "get-page-state" }
```
```json
{ "type": "capture-snapshot" }
```
```json
{ "type": "pin-tab", "url": "http://localhost:3000", "openIfMissing": true }
```

The `pin-tab` command is relayed by the content script to the service worker, which finds or opens the tab and registers it as the pinned target. `openIfMissing` defaults to `true`.

Response:
```json
{ "ok": true, "command": { "type": "pin-tab", "url": "http://localhost:3000", "openIfMissing": true, "enqueuedAt": "2026-05-01T14:00:00Z" } }
```

Only one command can be pending at a time. A new enqueue overwrites the previous one.

---

### `GET /commands/poll`

Returns and clears the current pending command. Called by the content script every 500 ms.

Also includes `agentActive` so the content script can relay badge state to the service worker.

Response when a command is pending:
```json
{ "ok": true, "command": { "type": "get-page-state", "enqueuedAt": "2026-05-01T14:00:00Z" }, "agentActive": true }
```

Response when idle:
```json
{ "ok": true, "command": null, "agentActive": false }
```

---

## Port

Default: `47771`. Override with:

```bash
UI_DOM_INSPECTOR_BRIDGE_PORT=9000 npm run bridge
```

---

## Persistence

Session state is written to `bridge/session-state.json` after every update. This means if the bridge restarts, the last known session state is restored.

Screenshots are not deleted automatically. Clean `artifacts/` manually when needed.
