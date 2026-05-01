const BRIDGE = "http://127.0.0.1:47772";
const STORAGE_TAB_ID  = "pinnedTabId";
const STORAGE_TAB_URL = "pinnedTabUrl";
const STORAGE_TAB_TITLE = "pinnedTabTitle";
const STORAGE_TAB_FAVICON = "pinnedTabFavicon";

// ── DOM refs ──────────────────────────────────────────────────────────────────
const bridgeDot   = document.getElementById("bridge-dot");
const bridgeLabel = document.getElementById("bridge-label");
const tabUrlEl    = document.getElementById("tab-url");
const tabFavicon  = document.getElementById("tab-favicon");
const logEl       = document.getElementById("log");
const selectBtn   = document.getElementById("select-element");
const selectIcon  = document.getElementById("select-icon");
const selectLabel = document.getElementById("select-label");
const pinToggle   = document.getElementById("pin-toggle");

let selectingActive = false;

// ── Logging ───────────────────────────────────────────────────────────────────
function log(text, type = "info") {
  logEl.textContent = text;
  logEl.className = `log-line ${type}`;
}

// ── Bridge health ─────────────────────────────────────────────────────────────
async function checkBridge() {
  try {
    const res = await fetch(`${BRIDGE}/health`, { signal: AbortSignal.timeout(2000) });
    const data = await res.json();
    bridgeDot.className = "bridge-dot ok";
    bridgeLabel.textContent = "connected";
    return data;
  } catch {
    bridgeDot.className = "bridge-dot err";
    bridgeLabel.textContent = "offline";
    log("Bridge not running — start with: npm run bridge", "err");
    return null;
  }
}

// ── Pinned tab ────────────────────────────────────────────────────────────────
async function loadPinnedTab() {
  const stored = await chrome.storage.session.get([
    STORAGE_TAB_ID, STORAGE_TAB_URL, STORAGE_TAB_TITLE, STORAGE_TAB_FAVICON
  ]);
  if (stored[STORAGE_TAB_ID]) {
    // Verify tab still exists
    try {
      await chrome.tabs.get(stored[STORAGE_TAB_ID]);
      renderPinnedTab(stored[STORAGE_TAB_URL], stored[STORAGE_TAB_FAVICON]);
      return stored[STORAGE_TAB_ID];
    } catch {
      // Tab was closed — clear
      await clearPinnedStorage();
    }
  }
  renderPinnedTab(null, null);
  return null;
}

function renderPinnedTab(url, favicon) {
  if (url) {
    tabUrlEl.textContent = url;
    tabUrlEl.className = "tab-url set";
    pinToggle.classList.add("on");
    if (favicon) {
      tabFavicon.src = favicon;
      tabFavicon.style.display = "";
    }
  } else {
    tabUrlEl.textContent = "No tab pinned — actions use active tab";
    tabUrlEl.className = "tab-url";
    tabFavicon.style.display = "none";
    pinToggle.classList.remove("on");
  }
}

async function clearPinnedStorage() {
  await chrome.storage.session.remove([
    STORAGE_TAB_ID, STORAGE_TAB_URL, STORAGE_TAB_TITLE, STORAGE_TAB_FAVICON
  ]);
}

async function getTargetTab() {
  const stored = await chrome.storage.session.get([STORAGE_TAB_ID]);
  const pinnedId = stored[STORAGE_TAB_ID];
  if (pinnedId) {
    try {
      return await chrome.tabs.get(pinnedId);
    } catch {
      await clearPinnedStorage();
      renderPinnedTab(null, null);
      log("Pinned tab was closed. Pin a new tab.", "err");
      return null;
    }
  }
  const [active] = await chrome.tabs.query({ active: true, currentWindow: true });
  return active || null;
}

// ── Init ──────────────────────────────────────────────────────────────────────
(async () => {
  // Tell the service worker the popup opened so it refreshes the badge immediately
  chrome.runtime.sendMessage({ type: "ui-dom-inspector:popup-opened" }).catch(() => {});

  const [bridgeData] = await Promise.all([checkBridge(), loadPinnedTab()]);
  if (bridgeData) {
    log("Ready", "dim");
  }
})();

// ── Pin toggle ────────────────────────────────────────────────────────────────
pinToggle.addEventListener("click", async () => {
  const isPinned = pinToggle.classList.contains("on");

  if (isPinned) {
    await clearPinnedStorage();
    renderPinnedTab(null, null);
    fetch(`${BRIDGE}/session/pinned-tab`, { method: "DELETE" }).catch(() => {});
    log("Pin cleared", "dim");
  } else {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab?.id) throw new Error("No active tab found");

      await chrome.storage.session.set({
        [STORAGE_TAB_ID]: tab.id,
        [STORAGE_TAB_URL]: tab.url,
        [STORAGE_TAB_TITLE]: tab.title,
        [STORAGE_TAB_FAVICON]: tab.favIconUrl || ""
      });
      renderPinnedTab(tab.url, tab.favIconUrl);

      fetch(`${BRIDGE}/session/pinned-tab`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tabId: tab.id, url: tab.url, title: tab.title })
      }).catch(() => {});

      log(`Pinned: ${tab.url}`, "ok");
    } catch (err) {
      log(`Pin failed: ${err.message}`, "err");
    }
  }
});

// ── Select element ────────────────────────────────────────────────────────────
selectBtn.addEventListener("click", async () => {
  try {
    const tab = await getTargetTab();
    if (!tab?.id) {
      log("No target tab available.", "err");
      return;
    }

    if (!selectingActive) {
      await chrome.tabs.sendMessage(tab.id, { type: "ui-dom-inspector:start-selection" });
      selectingActive = true;
      selectBtn.classList.add("active");
      selectIcon.textContent = "■"; // stop square
      selectLabel.textContent = "Cancel selection (or press Esc)";
      log("Click an element in the target tab…", "info");
    } else {
      await chrome.tabs.sendMessage(tab.id, { type: "ui-dom-inspector:stop-selection" });
      selectingActive = false;
      selectBtn.classList.remove("active");
      selectIcon.textContent = "◎";
      selectLabel.textContent = "Select element";
      log("Selection cancelled", "dim");
    }
  } catch (err) {
    selectingActive = false;
    selectBtn.classList.remove("active");
    selectIcon.textContent = "◎";
    selectLabel.textContent = "Select element";
    log(`Selection failed: ${err.message}`, "err");
  }
});

// Reset select button if content script confirms selection or cancellation
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === "ui-dom-inspector:selection-complete") {
    selectingActive = false;
    selectBtn.classList.remove("active");
    selectIcon.textContent = "◎";
    selectLabel.textContent = "Select element";
    log(`Element captured → bridge updated`, "ok");
  }
  if (message.type === "ui-dom-inspector:selection-cancelled") {
    selectingActive = false;
    selectBtn.classList.remove("active");
    selectIcon.textContent = "◎";
    selectLabel.textContent = "Select element";
    log("Selection cancelled", "dim");
  }
});

// ── Capture snapshot ──────────────────────────────────────────────────────────
document.getElementById("capture-snapshot").addEventListener("click", async () => {
  try {
    const tab = await getTargetTab();
    if (!tab) {
      log("No target tab.", "err");
      return;
    }
    log("Capturing…", "info");
    const result = await chrome.runtime.sendMessage({
      type: "ui-dom-inspector:capture-snapshot",
      tabId: tab.id,
      windowId: tab.windowId,
      pageUrl: tab.url
    });
    if (result?.ok) {
      log(`Snapshot saved: ${result.snapshot?.artifact?.filename || "ok"}`, "ok");
    } else {
      log(`Capture failed: ${result?.error || "unknown error"}`, "err");
    }
  } catch (err) {
    log(`Capture failed: ${err.message}`, "err");
  }
});

// ── Send page state ───────────────────────────────────────────────────────────
document.getElementById("send-page-state").addEventListener("click", async () => {
  try {
    const tab = await getTargetTab();
    if (!tab?.id) {
      log("No target tab.", "err");
      return;
    }
    const pageState = await chrome.tabs.sendMessage(tab.id, {
      type: "ui-dom-inspector:get-page-state"
    });
    const result = await chrome.runtime.sendMessage({
      type: "ui-dom-inspector:bridge-page-state",
      payload: pageState
    });
    if (result?.ok) {
      log("Page state sent to bridge", "ok");
    } else {
      log(`Bridge error: ${result?.error || "unknown"}`, "err");
    }
  } catch (err) {
    log(`Send failed: ${err.message}`, "err");
  }
});
