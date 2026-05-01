const BRIDGE = "http://127.0.0.1:47771";

const STATE = {
  selectionMode: false,
  hoverElement: null,
  selectedElement: null
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function safeText(value, max = 200) {
  return (value || "").replace(/\s+/g, " ").trim().slice(0, max);
}

function getSelector(element) {
  if (!(element instanceof Element)) return "";
  if (element.id) return `#${element.id}`;
  if (element.getAttribute("data-qo-id")) {
    return `[data-qo-id="${element.getAttribute("data-qo-id")}"]`;
  }
  const cls = Array.from(element.classList).slice(0, 3).join(".");
  return cls ? `${element.tagName.toLowerCase()}.${cls}` : element.tagName.toLowerCase();
}

function getBounds(element) {
  const rect = element.getBoundingClientRect();
  return {
    x: Math.round(rect.x),
    y: Math.round(rect.y),
    width: Math.round(rect.width),
    height: Math.round(rect.height)
  };
}

function getComputedStyleSnapshot(element) {
  const s = window.getComputedStyle(element);
  return {
    color: s.color,
    backgroundColor: s.backgroundColor,
    borderRadius: s.borderRadius,
    fontFamily: s.fontFamily,
    fontSize: s.fontSize,
    fontWeight: s.fontWeight,
    lineHeight: s.lineHeight,
    paddingTop: s.paddingTop,
    paddingRight: s.paddingRight,
    paddingBottom: s.paddingBottom,
    paddingLeft: s.paddingLeft,
    marginTop: s.marginTop,
    marginRight: s.marginRight,
    marginBottom: s.marginBottom,
    marginLeft: s.marginLeft,
    display: s.display,
    position: s.position,
    gap: s.gap,
    width: s.width,
    height: s.height
  };
}

function getAncestry(element) {
  const items = [];
  let current = element;
  while (current instanceof Element && items.length < 8) {
    items.unshift(getSelector(current));
    current = current.parentElement;
  }
  return items;
}

function getChildrenSummary(element) {
  return Array.from(element.children).slice(0, 12).map((child) => ({
    selector: getSelector(child),
    text: safeText(child.textContent, 80)
  }));
}

function guessComponentHints(element) {
  const hints = [];
  const role = element.getAttribute("role");
  const tag = element.tagName.toLowerCase();
  if (tag === "button" || role === "button") hints.push("Button");
  if (tag === "input" || tag === "textarea") hints.push("Input");
  if (role === "dialog") hints.push("Modal");
  if (role === "navigation" || tag === "nav") hints.push("Navigation");
  if (element.matches("[class*='card'], [data-card]")) hints.push("Card");
  if (element.matches("[class*='toggle'], [role='group']")) hints.push("ToggleGroup");
  if (element.matches("[class*='chip'], [class*='tag']")) hints.push("Chip");
  return hints;
}

function buildElementPayload(element) {
  return {
    selector: getSelector(element),
    tag: element.tagName.toLowerCase(),
    role: element.getAttribute("role") || "",
    text: safeText(element.textContent),
    classes: Array.from(element.classList),
    bounds: getBounds(element),
    computedStyles: getComputedStyleSnapshot(element),
    ancestry: getAncestry(element),
    children: getChildrenSummary(element),
    componentHints: guessComponentHints(element)
  };
}

// ── Overlay management ────────────────────────────────────────────────────────

function setSelectedElement(element) {
  if (STATE.selectedElement) {
    STATE.selectedElement.removeAttribute("data-ui-dom-inspector-selected");
  }
  STATE.selectedElement = element;
  if (STATE.selectedElement) {
    STATE.selectedElement.setAttribute("data-ui-dom-inspector-selected", "true");
  }
}

function setHoverElement(element) {
  if (STATE.hoverElement && STATE.hoverElement !== STATE.selectedElement) {
    STATE.hoverElement.classList.remove("ui-dom-inspector-hover");
  }
  STATE.hoverElement = element;
  if (STATE.hoverElement && STATE.hoverElement !== STATE.selectedElement) {
    STATE.hoverElement.classList.add("ui-dom-inspector-hover");
  }
}

function enterSelectionMode() {
  STATE.selectionMode = true;
  document.body.classList.add("ui-dom-inspector-selecting");
}

function exitSelectionMode() {
  STATE.selectionMode = false;
  document.body.classList.remove("ui-dom-inspector-selecting");
  if (STATE.hoverElement && STATE.hoverElement !== STATE.selectedElement) {
    STATE.hoverElement.classList.remove("ui-dom-inspector-hover");
  }
  STATE.hoverElement = null;
}

// ── Auto-bridge: push state after selection ───────────────────────────────────

async function autoBridgeState() {
  const payload = {
    page: { url: window.location.href, title: document.title },
    selectedElement: STATE.selectedElement ? buildElementPayload(STATE.selectedElement) : null
  };
  try {
    await fetch(`${BRIDGE}/session/update`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  } catch {
    // Bridge not running — non-fatal
  }
}

// ── Event listeners ───────────────────────────────────────────────────────────

document.addEventListener("mousemove", (event) => {
  if (!STATE.selectionMode) return;
  if (event.target instanceof Element) setHoverElement(event.target);
}, true);

document.addEventListener("click", (event) => {
  if (!STATE.selectionMode) return;
  const target = event.target;
  if (!(target instanceof Element)) return;
  event.preventDefault();
  event.stopPropagation();

  setSelectedElement(target);
  exitSelectionMode();

  // Push to bridge immediately; popup may already be closed
  autoBridgeState().then(() => {
    // Notify popup if it's still open
    chrome.runtime.sendMessage({
      type: "ui-dom-inspector:selection-complete",
      selector: getSelector(target)
    }).catch(() => {});
  });
}, true);

// Escape cancels selection mode
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && STATE.selectionMode) {
    exitSelectionMode();
    chrome.runtime.sendMessage({
      type: "ui-dom-inspector:selection-cancelled"
    }).catch(() => {});
  }
}, true);

// ── Message handler ───────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "ui-dom-inspector:start-selection") {
    enterSelectionMode();
    sendResponse({ ok: true });
    return true;
  }

  if (message.type === "ui-dom-inspector:stop-selection") {
    exitSelectionMode();
    sendResponse({ ok: true });
    return true;
  }

  if (message.type === "ui-dom-inspector:get-selected-element") {
    sendResponse({
      ok: !!STATE.selectedElement,
      selectedElement: STATE.selectedElement ? buildElementPayload(STATE.selectedElement) : null
    });
    return true;
  }

  if (message.type === "ui-dom-inspector:get-page-state") {
    sendResponse({
      page: { url: window.location.href, title: document.title },
      selectedElement: STATE.selectedElement ? buildElementPayload(STATE.selectedElement) : null
    });
    return true;
  }

  return false;
});
