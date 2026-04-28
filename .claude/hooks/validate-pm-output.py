#!/usr/bin/env python3
"""
PM Output Validator Hook
Runs on SubagentStop for PM agent.
Validates that PM created:
  1. A TODO file in .claude/memory/todos/
  2. An execution tracker in .claude/memory/active/execution-tracker.json

If either is missing, injects a warning so Main Claude knows to fix it.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta


def find_claude_dir():
    """Walk up from CWD to find .claude directory"""
    current = Path.cwd()
    while current != current.parent:
        claude_dir = current / '.claude'
        if claude_dir.is_dir():
            return claude_dir
        current = current.parent
    project_dir = os.environ.get('CLAUDE_PROJECT_DIR', '')
    if project_dir:
        claude_dir = Path(project_dir) / '.claude'
        if claude_dir.is_dir():
            return claude_dir
    return None


def check_recent_todo(claude_dir, max_age_seconds=120):
    """Check if a TODO file was created recently (within max_age_seconds)"""
    todos_dir = claude_dir / 'memory' / 'todos'
    if not todos_dir.exists():
        return False, "No todos/ directory found"

    now = datetime.now().timestamp()
    for todo_file in todos_dir.glob('TODO-*.md'):
        age = now - todo_file.stat().st_mtime
        if age < max_age_seconds:
            return True, str(todo_file.name)

    return False, "No recent TODO file (within last 2 minutes)"


def check_execution_tracker(claude_dir, max_age_seconds=120):
    """Check if execution tracker exists and is recent"""
    tracker_path = claude_dir / 'memory' / 'active' / 'execution-tracker.json'
    if not tracker_path.exists():
        return False, "No execution-tracker.json found"

    age = datetime.now().timestamp() - tracker_path.stat().st_mtime
    if age > max_age_seconds:
        return False, "execution-tracker.json is stale (not updated recently)"

    # Validate structure
    try:
        with open(tracker_path) as f:
            data = json.load(f)

        required_fields = ['plan_id', 'phases']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return False, f"execution-tracker.json missing fields: {', '.join(missing)}"

        if not data.get('phases'):
            return False, "execution-tracker.json has no phases defined"

        return True, f"{len(data['phases'])} phases defined"
    except (json.JSONDecodeError, IOError) as e:
        return False, f"execution-tracker.json invalid: {e}"


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, IOError):
        data = {}

    agent_name = data.get('agent_name', '') or data.get('subagent_type', '')

    # Only validate PM agent output
    if agent_name != 'pm':
        return 0

    claude_dir = find_claude_dir()
    if not claude_dir:
        return 0

    output_parts = []
    warnings = []

    # Check TODO
    todo_ok, todo_detail = check_recent_todo(claude_dir)
    if todo_ok:
        output_parts.append(f"✅ TODO created: {todo_detail}")
    else:
        warnings.append(f"⚠️  PM did not create a TODO file. {todo_detail}")
        warnings.append("   ACTION: Create a TODO in .claude/memory/todos/ before proceeding.")

    # Check execution tracker
    tracker_ok, tracker_detail = check_execution_tracker(claude_dir)
    if tracker_ok:
        output_parts.append(f"✅ Execution tracker: {tracker_detail}")
    else:
        warnings.append(f"⚠️  PM did not create execution tracker. {tracker_detail}")
        warnings.append("   ACTION: Create .claude/memory/active/execution-tracker.json with plan_id and phases.")

    # Print results
    if warnings:
        print("🚨 PM OUTPUT VALIDATION FAILED:")
        for w in warnings:
            print(w)
        print("")
        print("The execution chain cannot proceed without a TODO and tracker.")
        print("Either re-invoke PM or create these files manually before continuing.")

    if output_parts:
        for line in output_parts:
            print(line)

    if not warnings:
        print("✅ PM output validated — ready for agent chain execution.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
