"""
Hook: uncertainty_detector
Fires on Stop events. Scans the final assistant message for uncertainty
markers and emits a warning event if found. The TUI shows ⚠ for these.

Uncertainty markers: phrases that suggest the agent is guessing or blocked
without emitting a proper AGENT_SIGNAL.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestrator.events import write as write_event

UNCERTAINTY_PHRASES = [
    "i'm not sure",
    "i'm unsure",
    "i don't know",
    "unclear",
    "not certain",
    "might be",
    "could be wrong",
    "assuming that",
    "i assumed",
    "i think you want",
    "let me know if",
    "please clarify",
    "need more information",
    "need clarification",
]


def main() -> int:
    payload_raw = sys.stdin.read().strip()
    if not payload_raw:
        return 0

    try:
        payload = json.loads(payload_raw)
    except json.JSONDecodeError:
        return 0

    if payload.get("hook_type") != "Stop":
        return 0

    issue_id = os.environ.get("ISSUE_ID", "unknown")

    # Extract last assistant message content
    messages = payload.get("messages", [])
    last_assistant = ""
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        last_assistant = block.get("text", "")
                        break
            elif isinstance(content, str):
                last_assistant = content
            break

    if not last_assistant:
        return 0

    lower = last_assistant.lower()
    found = [p for p in UNCERTAINTY_PHRASES if p in lower]

    if found:
        write_event(
            issue_id,
            "uncertainty_detected",
            phrases=found[:3],
            excerpt=last_assistant[:200],
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
