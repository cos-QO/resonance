# Implementation Notes

Decisions made during the v1 build of UI DOM Inspector.

---

## Manifest V3

The extension uses Manifest V3 (MV3), which is the current Chrome standard and required for new extensions.

Key MV3 implications:
- Background scripts must be service workers (no persistent background pages)
- `chrome.tabs.captureVisibleTab` now returns a Promise — we use the Promise API, not the callback form, to avoid a race condition where Chrome does not await async callbacks in `addListener`
- Content scripts can `fetch` URLs listed in `host_permissions` — this is how the content script posts directly to the bridge after element selection without going through the service worker

---

## Screenshot capture

We use `chrome.tabs.captureVisibleTab` at JPEG quality 70. This keeps file sizes small enough for LLM ingestion while preserving enough visual fidelity for colour and layout review.

The `windowId` (not `tabId`) is passed to `captureVisibleTab`. This is a Chrome API quirk — the function captures the visible tab of a window, not a specific tab by ID. The popup sends both `tabId` and `windowId` in the capture message; the service worker uses `windowId`.

---

## Tab pinning

Problem: the popup closes the moment the user clicks anything outside it (Chrome behaviour). This means the popup can't show post-selection feedback, and "active tab" would resolve to whatever tab is in focus — including the terminal.

Solution: store the pinned tab in `chrome.storage.session`. Session storage persists within a browser session (survives popup open/close, cleared on browser restart). The popup reads from storage on every open, so it always reflects the current pin.

All actions (select, capture, send state) resolve the target tab from storage rather than querying the active tab.

---

## Auto-bridge after selection

When the user clicks an element, the popup is already closed (Chrome closes it on click). So the content script posts the page state directly to the bridge via `fetch` immediately after selection, without routing through the service worker.

The content script can do this because `http://127.0.0.1:47771/*` is in `host_permissions`, which grants content scripts cross-origin access to that URL regardless of the page's CSP.

---

## Bridge persistence

Session state is written to `bridge/session-state.json` after every mutation. If the bridge restarts (e.g. `npm run bridge` again), the last known state is readable. This is not an append log — it is a single-file snapshot of the latest state.

Screenshot artifacts are written to `artifacts/` with ISO timestamp filenames. They are never automatically deleted.

---

## MCP snapshot returns image content

The `ui_dom_inspector_get_latest_snapshot` tool reads the artifact file and returns it as `{ type: "image", data: "<base64>", mimeType: "image/jpeg" }`. This is the correct MCP SDK content type for images. Returning only the file path would leave Claude unable to see the screenshot.

---

## Component hints

Component hints are simple DOM heuristics — tag name, role attribute, and class name patterns. They are intentionally coarse:

- `button` tag or `role="button"` → "Button"
- `input` / `textarea` → "Input"
- `role="dialog"` → "Modal"
- `nav` or `role="navigation"` → "Navigation"
- class containing `card` or `data-card` → "Card"
- class containing `toggle` or `role="group"` → "ToggleGroup"
- class containing `chip` or `tag` → "Chip"

Exact React component names would require React DevTools hooks or a build-time instrumentation step. That is out of scope for v1.

---

## Selection mode cursor

The crosshair cursor is applied via a `ui-dom-inspector-selecting` class on `document.body`, driven by `overlay.css`. This avoids injecting inline styles and respects the cascade — it applies to `body *` so nested elements all show crosshair.

---

## Bridge port

Default port is `47771`. Chosen to avoid conflicts with common dev server ports (3000, 5173, 8080, etc.). Configurable via `UI_DOM_INSPECTOR_BRIDGE_PORT`.
