"""
Hook: phase_tracker
Fires on SubagentStop. Reads the execution tracker and marks the
completed phase, then writes an event so the TUI can show progress.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestrator.events import write as write_event

TRACKER_PATH = Path(".claude/memory/active/execution-tracker.json")


def main() -> int:
    payload_raw = sys.stdin.read().strip()
    if not payload_raw:
        return 0

    try:
        payload = json.loads(payload_raw)
    except json.JSONDecodeError:
        return 0

    if payload.get("hook_type") != "SubagentStop":
        return 0

    issue_id = os.environ.get("ISSUE_ID", "unknown")
    subagent_type = payload.get("subagent_type", "unknown")

    if not TRACKER_PATH.exists():
        return 0

    try:
        with open(TRACKER_PATH) as f:
            tracker = json.load(f)
    except (json.JSONDecodeError, OSError):
        return 0

    # Find and mark any in_progress phase assigned to this subagent type as completed
    phases = tracker.get("phases", [])
    for phase in phases:
        if phase.get("status") == "in_progress" and phase.get("agent") == subagent_type:
            phase["status"] = "completed"
            write_event(
                issue_id,
                "phase_completed",
                phase_id=phase.get("id"),
                phase_title=phase.get("title"),
                agent=subagent_type,
            )

    try:
        with open(TRACKER_PATH, "w") as f:
            json.dump(tracker, f, indent=2)
    except OSError:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
