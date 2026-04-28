#!/usr/bin/env python3
"""PostToolUseFailure hook: Log tool failures for pattern analysis."""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

def find_project_root():
    d = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    while d != d.parent:
        if (d / ".claude").is_dir():
            return d / ".claude"
        d = d.parent
    return None

def main():
    root = find_project_root()
    if not root:
        json.dump({"decision": "approve"}, sys.stdout)
        return

    # Read the tool failure info from stdin
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        input_data = {}

    tool_name = input_data.get("tool_name", "unknown")
    error = input_data.get("error", "")

    # Log to error tracking file
    log_dir = root / "memory" / "reports" / "errors"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "tool-failures.jsonl"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "error": str(error)[:500],  # Truncate long errors
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # Check for repeated failures (same tool failing 3+ times)
    try:
        lines = log_file.read_text().strip().split("\n")
        recent = [json.loads(l) for l in lines[-20:]]  # Last 20 entries
        same_tool = [e for e in recent if e["tool"] == tool_name]
        if len(same_tool) >= 3:
            json.dump({
                "decision": "block",
                "reason": f"Tool '{tool_name}' has failed {len(same_tool)} times recently. Consider investigating the root cause or trying a different approach."
            }, sys.stdout)
            return
    except Exception:
        pass

    json.dump({"decision": "approve"}, sys.stdout)

if __name__ == "__main__":
    main()
