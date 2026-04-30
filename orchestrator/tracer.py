"""
Debug tracer — captures full e2e event traces for debugging.

When enabled, writes structured trace events to:
  runs/traces/<session-id>.jsonl   (one file per orchestrator session)

Categories:
  mcp        — full MCP tool calls (input + output) from agent workers
  linear     — every Linear GraphQL API call (query + response summary)
  agent      — full agent thinking text (not truncated) + all signals
  pipeline   — orchestrator decisions: task routing, dependency checks, state changes

Settings persisted at runs/debug-settings.json.
Trace files are standalone JSONL — readable with `jq` or the TUI trace viewer.
"""
import json
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_SETTINGS_FILE = Path("runs/debug-settings.json")
_TRACES_DIR    = Path("runs/traces")

_DEFAULT_SETTINGS: dict = {
    "enabled": False,
    "categories": {
        "mcp":      True,
        "linear":   True,
        "agent":    True,
        "pipeline": True,
    },
}

_lock = threading.Lock()
_settings: dict = dict(_DEFAULT_SETTINGS)
_session_id: Optional[str] = None
_trace_path: Optional[Path] = None


# ── Settings ──────────────────────────────────────────────────────────────────

def load() -> None:
    """Load settings from disk. Called at orchestrator startup."""
    global _settings
    if _SETTINGS_FILE.exists():
        try:
            data = json.loads(_SETTINGS_FILE.read_text())
            merged = dict(_DEFAULT_SETTINGS)
            merged["enabled"] = bool(data.get("enabled", False))
            cats = merged["categories"].copy()
            cats.update({k: bool(v) for k, v in data.get("categories", {}).items() if k in cats})
            merged["categories"] = cats
            with _lock:
                _settings = merged
        except Exception:
            logger.warning("tracer: could not load debug-settings.json")


def save(enabled: bool, categories: Optional[dict[str, bool]] = None) -> None:
    """Persist settings. Called from TUI settings modal."""
    global _settings, _session_id, _trace_path
    new_cats = _settings["categories"].copy()
    if categories:
        new_cats.update({k: bool(v) for k, v in categories.items() if k in new_cats})
    new_settings = {"enabled": enabled, "categories": new_cats}

    with _lock:
        _settings = new_settings
        if enabled and _session_id is None:
            _start_session()
        elif not enabled:
            _session_id = None
            _trace_path = None

    _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        _SETTINGS_FILE.write_text(json.dumps(new_settings, indent=2))
    except Exception:
        logger.warning("tracer: could not save debug-settings.json")


def get_settings() -> dict:
    with _lock:
        return {
            "enabled": _settings["enabled"],
            "categories": dict(_settings["categories"]),
        }


def is_enabled(category: Optional[str] = None) -> bool:
    with _lock:
        if not _settings["enabled"]:
            return False
        if category is None:
            return True
        return _settings["categories"].get(category, False)


# ── Session management ────────────────────────────────────────────────────────

def _start_session() -> None:
    """Open a new trace file. Must be called under _lock."""
    global _session_id, _trace_path
    _TRACES_DIR.mkdir(parents=True, exist_ok=True)
    _session_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    _trace_path = _TRACES_DIR / f"session-{_session_id}.jsonl"
    logger.info("tracer: session started path=%s", _trace_path)


def start_session() -> None:
    """Start a trace session (called at orchestrator startup if already enabled)."""
    with _lock:
        if _settings["enabled"] and _session_id is None:
            _start_session()


# ── Event writing ─────────────────────────────────────────────────────────────

def record(
    category: str,
    event_type: str,
    issue_id: Optional[str] = None,
    **data,
) -> None:
    """
    Write one trace event. No-op if tracing is disabled or category is off.

    Args:
        category:   one of mcp | linear | agent | pipeline
        event_type: short descriptor e.g. "mcp_call", "linear_query", "agent_thinking_full"
        issue_id:   Linear issue identifier, if applicable
        **data:     arbitrary key=value fields merged into the event
    """
    if not is_enabled(category):
        return

    with _lock:
        path = _trace_path
        if path is None:
            if _settings["enabled"]:
                _start_session()
                path = _trace_path
            if path is None:
                return

    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "cat": category,
        "type": event_type,
        **({} if issue_id is None else {"issue": issue_id}),
        **data,
    }
    try:
        with open(path, "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception:
        logger.warning("tracer: write failed event_type=%s", event_type)


# ── Convenience helpers ───────────────────────────────────────────────────────

def mcp_call(
    issue_id: str,
    tool_name: str,
    tool_id: str,
    inputs: dict,
) -> None:
    """Record an MCP tool invocation (call side)."""
    record("mcp", "mcp_call",
           issue_id=issue_id,
           tool=tool_name,
           tool_id=tool_id,
           inputs=inputs)


def mcp_result(
    issue_id: str,
    tool_name: str,
    tool_id: str,
    outputs: object,
    is_error: bool = False,
) -> None:
    """Record an MCP tool result (response side)."""
    record("mcp", "mcp_result",
           issue_id=issue_id,
           tool=tool_name,
           tool_id=tool_id,
           outputs=outputs,
           error=is_error)


def linear_query(
    method: str,
    variables: Optional[dict],
    response_summary: object,
    elapsed_ms: float,
) -> None:
    """Record a Linear GraphQL API call from the orchestrator."""
    # Redact API key from variables just in case
    safe_vars = _redact(variables) if variables else None
    record("linear", "linear_query",
           method=method,
           variables=safe_vars,
           response=response_summary,
           elapsed_ms=round(elapsed_ms, 1))


def agent_thinking_full(issue_id: str, text: str) -> None:
    """Record the full (untruncated) agent thinking text."""
    record("agent", "agent_thinking_full", issue_id=issue_id, text=text)


def pipeline_decision(issue_id: str, decision: str, **context) -> None:
    """Record an orchestrator routing or state-machine decision."""
    record("pipeline", "pipeline_decision",
           issue_id=issue_id,
           decision=decision,
           **context)


# ── Utilities ─────────────────────────────────────────────────────────────────

def _redact(d: dict) -> dict:
    sensitive = {"apiKey", "api_key", "token", "secret", "password", "authorization"}
    return {
        k: "***" if k.lower() in sensitive else v
        for k, v in d.items()
    }


def get_trace_files() -> list[Path]:
    """Return trace files sorted newest-first."""
    if not _TRACES_DIR.exists():
        return []
    return sorted(_TRACES_DIR.glob("session-*.jsonl"), reverse=True)


def read_latest_trace(n: int = 500) -> list[dict]:
    """Read the last n events from the current session trace file."""
    files = get_trace_files()
    if not files:
        return []
    events: list[dict] = []
    try:
        for line in files[0].read_text().splitlines():
            try:
                events.append(json.loads(line))
            except Exception:
                pass
    except Exception:
        pass
    return events[-n:]
