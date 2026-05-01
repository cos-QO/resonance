# MCP Server

This folder is for the planned MCP wrapper for `UI DOM Inspector`.

## Purpose

Expose the inspector to Claude Code as tools.

## Planned tools

- `ui_dom_inspector_get_selected_element`
- `ui_dom_inspector_capture_snapshot`
- `ui_dom_inspector_get_page_structure`
- `ui_dom_inspector_get_visual_diagnostics`

## V1 expectation

The MCP server should stay small and only expose the useful structured outputs from the extension and bridge.

## Current v1 tools

The current skeleton exposes:

- `ui_dom_inspector_health`
- `ui_dom_inspector_get_selected_element`
- `ui_dom_inspector_get_page_state`
- `ui_dom_inspector_get_latest_snapshot`
- `ui_dom_inspector_get_visual_diagnostics`
