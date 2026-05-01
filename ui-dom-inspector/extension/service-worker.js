const BRIDGE_BASE_URL = "http://127.0.0.1:47771";

async function postJson(path, payload) {
  const response = await fetch(`${BRIDGE_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(`Bridge responded ${response.status} on ${path}`);
  }
  return response.json();
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {

  // ── Capture visible tab screenshot ────────────────────────────────────────
  if (message.type === "ui-dom-inspector:capture-snapshot") {
    // Use Promise API (MV3 preferred) to avoid async-callback race condition
    chrome.tabs.captureVisibleTab(message.windowId, { format: "jpeg", quality: 70 })
      .then((dataUrl) =>
        postJson("/snapshot", {
          pageUrl: message.pageUrl || "",
          screenshotDataUrl: dataUrl
        })
      )
      .then((result) => sendResponse(result))
      .catch((err) => sendResponse({ ok: false, error: err.message }));

    return true; // keep channel open for async response
  }

  // ── Push page state to bridge ─────────────────────────────────────────────
  if (message.type === "ui-dom-inspector:bridge-page-state") {
    postJson("/session/update", message.payload)
      .then((result) => sendResponse(result))
      .catch((err) => sendResponse({ ok: false, error: err.message }));

    return true;
  }

  return false;
});
