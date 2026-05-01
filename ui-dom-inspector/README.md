# UI DOM Inspector

`UI DOM Inspector` is the planned browser-side inspection layer for this repo's supervised UI workflow.

It is intended to give Claude Code better live visibility into the rendered page by combining:

- screenshot capture
- DOM inspection
- computed styles
- element geometry
- token diagnostics
- component hints

## Purpose

This project exists to support:

- `ui-analysis-agent`
- `ui-build-agent`
- `ui-qa-agent`

inside the current `qo-ui-*` workflow.

## Planned parts

- `extension/`
  Chrome extension for live page inspection
- `bridge/`
  Local bridge that receives extension data
- `mcp-server/`
  MCP wrapper exposing the inspector to Claude Code
- `docs/`
  Inspector-specific implementation notes

See [docs/ui-dom-inspector.md](../docs/ui-dom-inspector.md) for the main architecture and scope.

## Current v1 setup

The repo now includes a runnable skeleton:

- `extension/manifest.json`
- `extension/service-worker.js`
- `extension/content-script.js`
- `extension/popup.html`
- `extension/popup.js`
- `bridge/server.js`
- `mcp-server/server.js`
- `package.json`

## Intended startup

1. Install dependencies:

```bash
cd ui-dom-inspector
npm install
```

2. Start the local bridge:

```bash
npm run bridge
```

3. In another terminal, start the MCP server:

```bash
npm run mcp
```

4. Load the extension in Chrome:

- open `chrome://extensions`
- enable Developer Mode
- choose `Load unpacked`
- select `ui-dom-inspector/extension`

## MCP connection

The intended Claude Code MCP stanza is:

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

This is not enabled in the repo's top-level `.mcp.json` yet so the current workflow remains stable until you decide to switch it on.
