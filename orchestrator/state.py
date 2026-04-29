"""
Local run state persisted in runs/state.json.
Single source of truth for which issues are active and at what status.
All writes are full-file (no partial updates) to avoid corruption.
"""
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

STATE_PATH = Path("runs/state.json")
COMMANDS_PATH = Path("runs/commands.jsonl")

_lock = threading.Lock()

ACTIVE_STATUSES = {"running", "paused", "waiting_human", "needs_input"}
TERMINAL_STATUSES = {"failed", "complete", "archived"}


def _load() -> dict:
    if not STATE_PATH.exists():
        return {}
    with open(STATE_PATH) as f:
        return json.load(f)


def _save(data: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    tmp.replace(STATE_PATH)


def create_run(
    issue_id: str,
    task_type: str,
    worker: str,
    worktree: str,
    branch: str,
    log_file: str,
    linear_uuid: str = "",
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _lock:
        data = _load()
        data[issue_id] = {
            "status": "running",
            "task_type": task_type,
            "worker": worker,
            "worktree": worktree,
            "branch": branch,
            "linear_uuid": linear_uuid,   # Linear UUID for API calls; issue_id is the display identifier
            "pid": None,
            "iteration": 1,
            "attempt": 1,
            "started_at": now,
            "last_event_at": now,
            "artifacts": {},
            "pending_question": None,
            "feedback_history": [],
            "log_file": log_file,
        }
        _save(data)


def update_run(issue_id: str, **fields) -> None:
    with _lock:
        data = _load()
        if issue_id not in data:
            raise KeyError(f"No run record for {issue_id}")
        data[issue_id].update(fields)
        data[issue_id]["last_event_at"] = datetime.now(timezone.utc).isoformat()
        _save(data)


def get_run(issue_id: str) -> Optional[dict]:
    with _lock:
        return _load().get(issue_id)


def get_active_runs() -> dict[str, dict]:
    with _lock:
        data = _load()
    return {k: v for k, v in data.items() if v["status"] in ACTIVE_STATUSES}


def get_all_runs() -> dict[str, dict]:
    with _lock:
        return _load()


def clear_session(clear_events: bool = True) -> dict:
    """Clear completed/failed runs and optionally wipe the event log.
    Returns {"runs_removed": N, "events_cleared": bool}."""
    with _lock:
        data = _load()
        before = len(data)
        data = {k: v for k, v in data.items() if v["status"] not in TERMINAL_STATUSES}
        _save(data)
        removed = before - len(data)

    events_cleared = False
    if clear_events:
        events_path = STATE_PATH.parent / "events.jsonl"
        if events_path.exists():
            events_path.write_text("")
            events_cleared = True

    return {"runs_removed": removed, "events_cleared": events_cleared}


# ── Command queue (CLI → orchestrator communication) ──────────────────────────

def post_command(issue_id: str, action: str, **kwargs) -> None:
    """Write a command from the CLI for the orchestrator to pick up."""
    COMMANDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    cmd = {
        "issue_id": issue_id,
        "action": action,
        "ts": datetime.now(timezone.utc).isoformat(),
        **kwargs,
    }
    with _lock:
        with open(COMMANDS_PATH, "a") as f:
            f.write(json.dumps(cmd) + "\n")


def read_commands(issue_id: str, after_position: int = 0) -> tuple[list[dict], int]:
    """Read pending commands for an issue. Returns (commands, new_position)."""
    if not COMMANDS_PATH.exists():
        return [], 0
    commands = []
    with open(COMMANDS_PATH) as f:
        f.seek(after_position)
        for line in f:
            line = line.strip()
            if line:
                try:
                    cmd = json.loads(line)
                    if cmd.get("issue_id") == issue_id:
                        commands.append(cmd)
                except json.JSONDecodeError:
                    pass
        position = f.tell()
    return commands, position
