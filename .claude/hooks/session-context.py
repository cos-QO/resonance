#!/usr/bin/env python3
"""SessionStart hook: Check for active work and remind Claude of context."""
import json
import os
import sys
from pathlib import Path

def find_project_root():
    """Walk up to find .claude directory."""
    d = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    while d != d.parent:
        if (d / ".claude").is_dir():
            return d / ".claude"
        d = d.parent
    return None

def main():
    root = find_project_root()
    if not root:
        return

    messages = []

    # Check for active execution tracker
    tracker = root / "memory" / "active" / "execution-tracker.json"
    if tracker.exists():
        try:
            data = json.loads(tracker.read_text())
            status = data.get("status", "unknown")
            plan_id = data.get("plan_id", "unknown")
            pending = [p for p in data.get("phases", []) if p.get("status") == "pending"]
            completed = [p for p in data.get("phases", []) if p.get("status") == "completed"]
            if pending:
                messages.append(
                    f"Active plan: {plan_id} ({len(completed)} phases done, {len(pending)} pending). "
                    f"Consider running /resume or reading the tracker."
                )
        except (json.JSONDecodeError, KeyError):
            pass

    # Check for active TODOs
    todos_dir = root / "memory" / "todos"
    if todos_dir.exists():
        active_todos = [
            f.name for f in todos_dir.glob("TODO-*.md")
            if "active" in f.read_text()[:200].lower()
        ]
        if active_todos:
            messages.append(f"Active TODOs: {', '.join(active_todos[:3])}")

    # Check for skill drafts pending installation
    drafts_dir = root / "memory" / "active" / "skill-drafts"
    if drafts_dir.exists():
        drafts = list(drafts_dir.glob("*.md"))
        if drafts:
            messages.append(
                f"Pending skill drafts: {', '.join(d.stem for d in drafts[:3])}. "
                f"Review and install with: cp .claude/memory/active/skill-drafts/<name>.md .claude/skills/<name>/SKILL.md"
            )

    if messages:
        result = {
            "decision": "block",
            "reason": "Session context reminder:\n" + "\n".join(f"- {m}" for m in messages)
        }
    else:
        result = {"decision": "approve"}

    json.dump(result, sys.stdout)

if __name__ == "__main__":
    main()
