import fs from "node:fs/promises";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const bridgeUrl = process.env.UI_DOM_INSPECTOR_BRIDGE_URL || "http://127.0.0.1:47771";

async function getJson(path) {
  const response = await fetch(`${bridgeUrl}${path}`);
  if (!response.ok) {
    throw new Error(`Bridge responded ${response.status} on ${path}`);
  }
  return response.json();
}

const server = new McpServer({
  name: "ui-dom-inspector",
  version: "0.1.0"
});

// ── Health check ──────────────────────────────────────────────────────────────
server.tool(
  "ui_dom_inspector_health",
  "Check whether the UI DOM Inspector bridge is running and report active session status.",
  {},
  async () => {
    const data = await getJson("/health");
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }]
    };
  }
);

// ── Pinned tab URL (for Playwright) ───────────────────────────────────────────
server.tool(
  "ui_dom_inspector_get_pinned_tab",
  [
    "Returns the URL of the tab the user has pinned as the supervised target in the Chrome extension.",
    "Use this to tell Playwright which URL to navigate to so it operates on the same page the user is watching.",
    "If no tab is pinned, the result will have pinnedTab: null."
  ].join(" "),
  {},
  async () => {
    const data = await getJson("/session/pinned-tab");
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }]
    };
  }
);

// ── Selected element ──────────────────────────────────────────────────────────
server.tool(
  "ui_dom_inspector_get_selected_element",
  "Get the element the user last selected in the browser via the extension. Returns selector, computed styles, bounds, ancestry, and component hints.",
  {},
  async () => {
    const data = await getJson("/session/current");
    const selected = data.session?.payload?.selectedElement ?? null;
    return {
      content: [{ type: "text", text: JSON.stringify(selected, null, 2) }]
    };
  }
);

// ── Full page state ───────────────────────────────────────────────────────────
server.tool(
  "ui_dom_inspector_get_page_state",
  "Get the latest page state from the bridge: page URL, title, and selected element data.",
  {},
  async () => {
    const data = await getJson("/session/current");
    const payload = data.session?.payload ?? null;
    return {
      content: [{ type: "text", text: JSON.stringify(payload, null, 2) }]
    };
  }
);

// ── Latest snapshot (returns the actual image) ────────────────────────────────
server.tool(
  "ui_dom_inspector_get_latest_snapshot",
  "Get the latest screenshot captured by the extension. Returns the image so you can see the current state of the page.",
  {},
  async () => {
    const data = await getJson("/session/current");
    const snapshot = data.session?.latestSnapshot ?? null;

    if (!snapshot?.artifact?.path) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({ ok: false, error: "No snapshot available yet. Use the extension to capture one." })
        }]
      };
    }

    try {
      const imageBuffer = await fs.readFile(snapshot.artifact.path);
      const base64 = imageBuffer.toString("base64");
      return {
        content: [
          {
            type: "image",
            data: base64,
            mimeType: "image/jpeg"
          },
          {
            type: "text",
            text: JSON.stringify({
              pageUrl: snapshot.pageUrl,
              capturedAt: snapshot.capturedAt,
              filename: snapshot.artifact.filename
            }, null, 2)
          }
        ]
      };
    } catch (err) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({ ok: false, error: `Could not read snapshot file: ${err.message}` })
        }]
      };
    }
  }
);

// ── Visual diagnostics summary ────────────────────────────────────────────────
server.tool(
  "ui_dom_inspector_get_visual_diagnostics",
  "Extract a concise diagnostics summary from the selected element: selector, bounds, component hints, ancestry, and optionally computed styles. Use during build and QA passes.",
  {
    includeComputedStyles: z.boolean().optional().default(true)
  },
  async ({ includeComputedStyles }) => {
    const data = await getJson("/session/current");
    const selected = data.session?.payload?.selectedElement ?? null;

    if (!selected) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            ok: false,
            error: "No selected element. Use the extension to select one first."
          }, null, 2)
        }]
      };
    }

    const summary = {
      selector: selected.selector,
      tag: selected.tag,
      role: selected.role || null,
      text: selected.text || null,
      bounds: selected.bounds,
      componentHints: selected.componentHints,
      ancestry: selected.ancestry,
      ...(includeComputedStyles ? { computedStyles: selected.computedStyles } : {})
    };

    return {
      content: [{ type: "text", text: JSON.stringify(summary, null, 2) }]
    };
  }
);

// ── Connect and serve ─────────────────────────────────────────────────────────
const transport = new StdioServerTransport();
await server.connect(transport);
