import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import http from "node:http";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");
const artifactsDir = path.join(rootDir, "artifacts");
const statePath = path.join(rootDir, "bridge", "session-state.json");
const port = Number(process.env.UI_DOM_INSPECTOR_BRIDGE_PORT || 47771);

let sessionState = {
  updatedAt: null,
  payload: null,
  latestSnapshot: null,
  pinnedTab: null,      // { tabId, url, title } — set by the extension popup
  agentActive: false,   // true while an MCP tool call is in progress
  agentActiveAt: null   // ISO timestamp — auto-cleared after 30 s
};

// Command queue — agent enqueues, content script polls and executes
let pendingCommand = null;

// Auto-clear agentActive if the MCP server crashes mid-tool and never sends idle
const AGENT_ACTIVE_TIMEOUT_MS = 30_000;
setInterval(() => {
  if (sessionState.agentActive && sessionState.agentActiveAt) {
    const elapsed = Date.now() - new Date(sessionState.agentActiveAt).getTime();
    if (elapsed > AGENT_ACTIVE_TIMEOUT_MS) {
      sessionState.agentActive = false;
      sessionState.agentActiveAt = null;
    }
  }
}, 5_000);

async function ensureStorage() {
  await fs.mkdir(artifactsDir, { recursive: true });
  await fs.mkdir(path.dirname(statePath), { recursive: true });
}

async function persistState() {
  await fs.writeFile(statePath, JSON.stringify(sessionState, null, 2));
}

async function readBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  if (!chunks.length) return {};
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

function sendJson(res, statusCode, payload) {
  res.writeHead(statusCode, {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS"
  });
  res.end(JSON.stringify(payload));
}

function buildArtifactName(prefix, ext) {
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  return `${prefix}-${stamp}.${ext}`;
}

async function writeDataUrlArtifact(prefix, dataUrl) {
  const match = /^data:image\/([a-zA-Z0-9+.-]+);base64,(.+)$/.exec(dataUrl || "");
  if (!match) throw new Error("Invalid image data URL");
  const ext = match[1] === "jpeg" ? "jpg" : match[1];
  const filename = buildArtifactName(prefix, ext);
  const full = path.join(artifactsDir, filename);
  await fs.writeFile(full, Buffer.from(match[2], "base64"));
  return { path: full, filename };
}

await ensureStorage();

const server = http.createServer(async (req, res) => {
  if (!req.url) {
    sendJson(res, 404, { ok: false, error: "Missing URL" });
    return;
  }

  if (req.method === "OPTIONS") {
    sendJson(res, 204, {});
    return;
  }

  // ── Health ──────────────────────────────────────────────────────────────────
  if (req.method === "GET" && req.url === "/health") {
    sendJson(res, 200, {
      ok: true,
      port,
      hasSession: !!sessionState.payload,
      hasSnapshot: !!sessionState.latestSnapshot,
      pinnedTab: sessionState.pinnedTab,
      agentActive: sessionState.agentActive
    });
    return;
  }

  // ── Agent status ────────────────────────────────────────────────────────────
  // Called by the MCP server before and after each tool call.
  // The extension service worker polls /health to read agentActive and updates
  // the badge colour: green (idle) → yellow (agent reading) → green (done).
  if (req.method === "POST" && req.url === "/session/agent-status") {
    const body = await readBody(req);
    sessionState.agentActive = !!body.active;
    sessionState.agentActiveAt = body.active ? new Date().toISOString() : null;
    sendJson(res, 200, { ok: true, agentActive: sessionState.agentActive });
    return;
  }

  // ── Session: current state ──────────────────────────────────────────────────
  if (req.method === "GET" && req.url === "/session/current") {
    sendJson(res, 200, { ok: true, session: sessionState });
    return;
  }

  if (req.method === "POST" && req.url === "/session/update") {
    const body = await readBody(req);
    sessionState = {
      ...sessionState,
      updatedAt: new Date().toISOString(),
      payload: body
    };
    await persistState();
    sendJson(res, 200, { ok: true, updatedAt: sessionState.updatedAt });
    return;
  }

  // ── Pinned tab ──────────────────────────────────────────────────────────────
  // GET /session/pinned-tab → returns pinned tab info (URL used by Playwright)
  if (req.method === "GET" && req.url === "/session/pinned-tab") {
    sendJson(res, 200, {
      ok: true,
      pinnedTab: sessionState.pinnedTab
    });
    return;
  }

  // POST /session/pinned-tab → extension sets the supervised tab
  if (req.method === "POST" && req.url === "/session/pinned-tab") {
    const body = await readBody(req);
    sessionState.pinnedTab = {
      tabId: body.tabId || null,
      url: body.url || "",
      title: body.title || "",
      pinnedAt: new Date().toISOString()
    };
    await persistState();
    console.log(`Pinned tab set: ${sessionState.pinnedTab.url}`);
    sendJson(res, 200, { ok: true, pinnedTab: sessionState.pinnedTab });
    return;
  }

  // DELETE /session/pinned-tab → clear the pin
  if (req.method === "DELETE" && req.url === "/session/pinned-tab") {
    sessionState.pinnedTab = null;
    await persistState();
    sendJson(res, 200, { ok: true });
    return;
  }

  // ── Snapshot ────────────────────────────────────────────────────────────────
  if (req.method === "POST" && req.url === "/snapshot") {
    const body = await readBody(req);
    const artifact = await writeDataUrlArtifact("page-snapshot", body.screenshotDataUrl);
    sessionState = {
      ...sessionState,
      updatedAt: new Date().toISOString(),
      latestSnapshot: {
        pageUrl: body.pageUrl || sessionState.pinnedTab?.url || "",
        capturedAt: new Date().toISOString(),
        artifact
      }
    };
    await persistState();
    sendJson(res, 200, { ok: true, snapshot: sessionState.latestSnapshot });
    return;
  }

  // ── Command queue ────────────────────────────────────────────────────────────
  // POST /commands/enqueue  — MCP tool queues a command for the content script
  // GET  /commands/poll     — content script polls and consumes the next command
  if (req.method === "POST" && req.url === "/commands/enqueue") {
    const body = await readBody(req);
    pendingCommand = { type: body.type, enqueuedAt: new Date().toISOString() };
    sendJson(res, 200, { ok: true, command: pendingCommand });
    return;
  }

  if (req.method === "GET" && req.url === "/commands/poll") {
    const cmd = pendingCommand;
    pendingCommand = null;
    sendJson(res, 200, { ok: true, command: cmd, agentActive: sessionState.agentActive });
    return;
  }

  sendJson(res, 404, { ok: false, error: `Unknown route: ${req.method} ${req.url}` });
});

server.listen(port, "127.0.0.1", () => {
  console.log(`UI DOM Inspector bridge listening on http://127.0.0.1:${port}`);
  console.log(`Artifacts: ${artifactsDir}`);
});
