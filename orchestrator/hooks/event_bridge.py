"""
Hook: event_bridge
Fires on Stop and PostToolUse events during orchestrated runs.
Reads the Claude Code hook payload from stdin and writes a structured
event to runs/events.jsonl so the TUI can display real-time activity.

Claude Code invokes hooks by piping JSON to stdin.
Exit 0 = success, non-zero = hook failure (logged but not fatal).
"""
import json
import os
import sys
from pathlib import Path

# Add repo root to path so we can import orchestrator
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestrator.events import write as write_event


def main() -> int:
    payload_raw = sys.stdin.read().strip()
    if not payload_raw:
        return 0

    try:
        payload = json.loads(payload_raw)
    except json.JSONDecodeError:
        return 0

    hook_type = payload.get("hook_type", "unknown")
    issue_id = os.environ.get("ISSUE_ID", "unknown")

    if hook_type == "Stop":
        write_event(
            issue_id,
            "hook_stop",
            stop_reason=payload.get("stop_reason"),
            usage=payload.get("usage"),
        )

    elif hook_type == "PostToolUse":
        write_event(
            issue_id,
            "tool_completed",
            tool=payload.get("tool_name"),
            success=payload.get("result", {}).get("success"),
        )

    elif hook_type == "SubagentStop":
        write_event(
            issue_id,
            "subagent_stop",
            subagent=payload.get("subagent_type"),
            stop_reason=payload.get("stop_reason"),
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
