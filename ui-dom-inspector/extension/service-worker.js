const BRIDGE = "http://127.0.0.1:47771";
const HEALTH_ALARM = "ui-dom-inspector:health";

// ── Icon drawing ───────────────────────────────────────────────────────────────
// Draws the inspector icon at any size using OffscreenCanvas.
// No PNG files needed — icon is generated at runtime.

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.arcTo(x + w, y, x + w, y + r, r);
  ctx.lineTo(x + w, y + h - r);
  ctx.arcTo(x + w, y + h, x + w - r, y + h, r);
  ctx.lineTo(x + r, y + h);
  ctx.arcTo(x, y + h, x, y + h - r, r);
  ctx.lineTo(x, y + r);
  ctx.arcTo(x, y, x + r, y, r);
  ctx.closePath();
}

function drawIconAtSize(size) {
  const c = new OffscreenCanvas(size, size);
  const ctx = c.getContext("2d");
  const s = size / 128;

  // Background
  ctx.fillStyle = "#0f0f1a";
  roundRect(ctx, 0, 0, size, size, Math.round(22 * s));
  ctx.fill();

  // Inner border
  ctx.strokeStyle = "#1e1e40";
  ctx.lineWidth = Math.max(1, 2 * s);
  roundRect(ctx, 2 * s, 2 * s, size - 4 * s, size - 4 * s, Math.round(20 * s));
  ctx.stroke();

  if (size >= 32) {
    // Scan corner brackets
    ctx.strokeStyle = "#3d7eff";
    ctx.lineWidth = Math.max(1.5, 4.5 * s);
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    const brackets = [
      [[20, 40], [20, 20], [40, 20]],   // top-left
      [[88, 20], [108, 20], [108, 40]], // top-right
      [[20, 88], [20, 108], [40, 108]], // bottom-left
      [[88, 108], [108, 108], [108, 88]] // bottom-right
    ];
    for (const [a, b, c_] of brackets) {
      ctx.beginPath();
      ctx.moveTo(a[0] * s, a[1] * s);
      ctx.lineTo(b[0] * s, b[1] * s);
      ctx.lineTo(c_[0] * s, c_[1] * s);
      ctx.stroke();
    }
  }

  // Cursor arrow
  ctx.fillStyle = "#ffffff";
  ctx.beginPath();
  const pts = [[38,26],[38,72],[46,63],[53,80],[59,77],[52,60],[64,60]];
  ctx.moveTo(pts[0][0] * s, pts[0][1] * s);
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0] * s, pts[i][1] * s);
  ctx.closePath();
  ctx.fill();

  return ctx.getImageData(0, 0, size, size);
}

async function applyIcon() {
  try {
    await chrome.action.setIcon({
      imageData: {
        16: drawIconAtSize(16),
        32: drawIconAtSize(32),
        48: drawIconAtSize(48)
      }
    });
  } catch {
    // Extension context may be invalid during startup — non-fatal
  }
}

// ── Badge ──────────────────────────────────────────────────────────────────────
// Three states shown as a coloured dot next to the toolbar icon:
//   green  — bridge connected, idle
//   yellow — an agent is actively reading the page (MCP tool call in progress)
//   red    — bridge not reachable

const BADGE_STATES = {
  connected:    { text: "●", bg: [34, 187, 85, 255],   label: "Connected" },
  "agent-active": { text: "●", bg: [245, 166, 35, 255], label: "Agent reading…" },
  offline:      { text: "●", bg: [204, 51, 51, 255],   label: "Bridge offline" }
};

async function setBadge(state) {
  const cfg = BADGE_STATES[state] ?? BADGE_STATES.offline;
  try {
    await chrome.action.setBadgeText({ text: cfg.text });
    await chrome.action.setBadgeBackgroundColor({ color: cfg.bg });
    // Chrome 110+: make the text colour match so the badge reads as a pure dot
    await chrome.action.setBadgeTextColor?.({ color: cfg.bg });
  } catch {
    // Older Chrome — badge still works, just shows white "●" on coloured bg
  }
  try {
    await chrome.action.setTitle({ title: `UI DOM Inspector — ${cfg.label}` });
  } catch {}
}

async function clearBadge() {
  try {
    await chrome.action.setBadgeText({ text: "" });
    await chrome.action.setTitle({ title: "UI DOM Inspector" });
  } catch {}
}

// ── Health check ───────────────────────────────────────────────────────────────

async function checkHealth() {
  try {
    const res = await fetch(`${BRIDGE}/health`, { signal: AbortSignal.timeout(2000) });
    const data = await res.json();
    if (data.agentActive) {
      await setBadge("agent-active");
    } else {
      await setBadge("connected");
    }
  } catch {
    await setBadge("offline");
  }
}

// ── Bridge helper ──────────────────────────────────────────────────────────────

async function postJson(path, payload) {
  const response = await fetch(`${BRIDGE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) throw new Error(`Bridge responded ${response.status} on ${path}`);
  return response.json();
}

// ── Lifecycle ──────────────────────────────────────────────────────────────────

async function init() {
  await applyIcon();
  await checkHealth();
  // Periodic badge refresh every 1 minute (Chrome's minimum alarm interval)
  chrome.alarms.get(HEALTH_ALARM, (existing) => {
    if (!existing) {
      chrome.alarms.create(HEALTH_ALARM, { periodInMinutes: 1 });
    }
  });
}

chrome.runtime.onInstalled.addListener(() => init());
chrome.runtime.onStartup.addListener(() => init());

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === HEALTH_ALARM) checkHealth();
});

// ── Message handlers ───────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {

  // Popup opened — refresh badge immediately so the status dot is current
  if (message.type === "ui-dom-inspector:popup-opened") {
    checkHealth().then(() => sendResponse({ ok: true })).catch(() => sendResponse({ ok: false }));
    return true;
  }

  // Content script relays agentActive state from poll responses so the badge
  // updates within 2 s of a tool call starting — no waiting for the 1-min alarm.
  if (message.type === "ui-dom-inspector:set-badge") {
    setBadge(message.state).then(() => sendResponse({ ok: true })).catch(() => sendResponse({ ok: false }));
    return true;
  }

  // Capture visible tab screenshot
  if (message.type === "ui-dom-inspector:capture-snapshot") {
    chrome.tabs.captureVisibleTab(message.windowId, { format: "jpeg", quality: 70 })
      .then((dataUrl) =>
        postJson("/snapshot", {
          pageUrl: message.pageUrl || "",
          screenshotDataUrl: dataUrl
        })
      )
      .then((result) => { checkHealth(); sendResponse(result); })
      .catch((err) => sendResponse({ ok: false, error: err.message }));
    return true;
  }

  // Push page state to bridge
  if (message.type === "ui-dom-inspector:bridge-page-state") {
    postJson("/session/update", message.payload)
      .then((result) => { checkHealth(); sendResponse(result); })
      .catch((err) => sendResponse({ ok: false, error: err.message }));
    return true;
  }

  // Agent-initiated capture — content script relays here because only the
  // service worker can call captureVisibleTab.
  if (message.type === "ui-dom-inspector:auto-capture") {
    chrome.storage.session.get(["pinnedTabId", "pinnedTabUrl"])
      .then(async (stored) => {
        const tabId = stored.pinnedTabId;
        if (!tabId) return;
        const tab = await chrome.tabs.get(tabId);
        const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: "jpeg", quality: 70 });
        await postJson("/snapshot", {
          pageUrl: message.pageUrl || stored.pinnedTabUrl || "",
          screenshotDataUrl: dataUrl
        });
        checkHealth();
      })
      .catch(() => {});
    return false;
  }

  return false;
});
