# Local Bridge

The local bridge is the connector between the Chrome extension and the MCP server.

## Responsibilities

- receive structured inspection data from the extension
- store temporary session state
- expose a stable local API to the MCP server

## V1 expectation

Keep it simple:

- localhost HTTP or WebSocket
- no multi-user complexity
- no durable database requirement

## Current v1 behavior

The bridge currently provides:

- `GET /health`
- `GET /session/current`
- `POST /session/update`
- `POST /snapshot`

It stores:

- latest page state
- latest selected element payload
- latest screenshot artifact metadata
