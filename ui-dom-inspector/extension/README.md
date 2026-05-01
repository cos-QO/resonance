# Extension

Planned Chrome extension for `UI DOM Inspector`.

## V1 responsibilities

- selected-element mode
- DOM inspection
- computed-style export
- bounds and ancestry export
- visible-tab screenshot capture
- selected-element crop capture
- lightweight compression
- overlay for diagnostics

## Likely files

- `manifest.json`
- `service-worker.js`
- `content-script.js`
- `overlay.css`

## Current v1 behavior

- popup can enable element selection
- content script tracks the selected element
- popup can request a visible-tab snapshot
- service worker sends screenshots and page state to the local bridge

This is a first-pass skeleton, not the finished inspector.
