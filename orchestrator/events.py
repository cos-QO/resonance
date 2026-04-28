"""
Append-only structured event log at runs/events.jsonl.
Every significant orchestrator action writes an event here.
The TUI tails this file for real-time display.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

EVENTS_PATH = Path("runs/events.jsonl")

logger = logging.getLogger(__name__)


def write(issue_id: str, event_type: str, **kwargs) -> None:
    EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "issue": issue_id,
        "type": event_type,
        **kwargs,
    }
    try:
        with open(EVENTS_PATH, "a") as f:
            f.write(json.dumps(event) + "\n")
    except OSError as e:
        logger.warning(f"Failed to write event: {e}")


def read_all() -> list[dict]:
    if not EVENTS_PATH.exists():
        return []
    events = []
    with open(EVENTS_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return events


def tail(n: int = 50) -> list[dict]:
    return read_all()[-n:]
