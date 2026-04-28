#!/usr/bin/env python3
"""
Hook: auto-commit.py
Trigger: PostToolUse (TodoWrite tool when all TODOs complete)
Purpose: Automatically commit changes with structured message when plan completes

This hook monitors TODO completion and automatically creates git commits with:
1. Structured commit messages (plan ID, agents, changes)
2. Automatic staging of all changes
3. Commit logging to git-commits.md
4. Integration with /git-commit command
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configuration
GIT_COMMITS_LOG = "claude/memory/git-commits.md"
COMMIT_MSG_TEMPLATE = "/tmp/claude-commit-msg-{timestamp}.txt"
COAUTHOR = "Co-Authored-By: Claude <noreply@anthropic.com>"


def get_project_root() -> Path:
    """Get project root directory (where claude/ folder exists)."""
    current = Path.cwd()

    # Check if claude/ exists in current directory
    if (current / "claude").exists():
        return current

    # Check parent directories (up to 3 levels)
    for parent in [current.parent, current.parent.parent, current.parent.parent.parent]:
        if (parent / "claude").exists():
            return parent

    # Fallback to current directory
    return current


def check_all_todos_complete(todos: List[Dict[str, Any]]) -> bool:
    """Check if all TODOs in the list are completed."""
    if not todos:
        return False

    return all(todo.get("status") == "completed" for todo in todos)


def find_active_plan() -> Optional[str]:
    """Find the active plan ID from memory/todos."""
    project_root = get_project_root()
    todos_dir = project_root / "claude/memory/todos"

    if not todos_dir.exists():
        return None

    # Look for active TODO files
    for todo_file in todos_dir.glob("*-todolist.md"):
        # Extract plan ID from filename
        match = re.search(r'(PLAN-[A-Z0-9]+-[A-Z0-9]+)', todo_file.name)
        if match:
            return match.group(1)

    # Fallback: look in active directory
    active_dir = project_root / "claude/memory/active"
    if active_dir.exists():
        plan_files = list(active_dir.glob("PLAN-*.md"))
        if plan_files:
            # Get most recent
            latest = max(plan_files, key=lambda p: p.stat().st_mtime)
            match = re.search(r'(PLAN-[A-Z0-9]+-[A-Z0-9]+)', latest.name)
            if match:
                return match.group(1)

    return None


def extract_plan_metadata(plan_id: str) -> Dict[str, Any]:
    """Extract metadata from plan file and git status."""
    project_root = get_project_root()

    metadata = {
        "plan_id": plan_id,
        "mode": "single",
        "agents": [],
        "files_changed": [],
        "summary": f"Plan {plan_id} completed",
        "changes": []
    }

    # Try to read plan file
    plan_file = project_root / f"claude/memory/active/{plan_id}.md"
    if plan_file.exists():
        try:
            content = plan_file.read_text()

            # Extract mode
            if "Mode: compound" in content or "compound" in content.lower():
                metadata["mode"] = "compound"

            # Extract agents (@mentions)
            agents = set(re.findall(r'@(\w+)', content))
            metadata["agents"] = sorted(agents)

            # Extract summary (first ## heading or title)
            match = re.search(r'^#+ (.+)$', content, re.MULTILINE)
            if match:
                summary = match.group(1)
                # Remove plan ID prefix if present
                summary = re.sub(r'^PLAN-[A-Z0-9]+-[A-Z0-9]+:?\s*', '', summary)
                metadata["summary"] = summary

            # Extract key changes (look for Changes: or Deliverables: section)
            changes_match = re.search(
                r'(?:Changes|Deliverables|Completed):(.+?)(?=\n##|\Z)',
                content,
                re.DOTALL | re.IGNORECASE
            )
            if changes_match:
                changes_text = changes_match.group(1)
                # Extract bullet points
                changes = re.findall(r'[-*]\s+(.+)', changes_text)
                metadata["changes"] = changes[:5]  # First 5 changes

        except Exception as e:
            print(f"⚠️  Warning: Could not parse plan file: {e}", file=sys.stderr)

    # Get changed files from git
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            cwd=project_root,
            check=False
        )

        if result.returncode == 0 and result.stdout.strip():
            files = [f for f in result.stdout.strip().split("\n") if f]
            metadata["files_changed"] = files

        # Also check staged files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            cwd=project_root,
            check=False
        )

        if result.returncode == 0 and result.stdout.strip():
            staged_files = [f for f in result.stdout.strip().split("\n") if f]
            # Add staged files not already in list
            for f in staged_files:
                if f and f not in metadata["files_changed"]:
                    metadata["files_changed"].append(f)

    except Exception as e:
        print(f"⚠️  Warning: Could not get git status: {e}", file=sys.stderr)

    return metadata


def generate_commit_message(metadata: Dict[str, Any]) -> str:
    """Generate structured commit message from plan metadata."""
    plan_id = metadata["plan_id"]
    summary = metadata["summary"]
    mode = metadata["mode"]
    agents = metadata["agents"]
    files_count = len(metadata["files_changed"])
    changes = metadata["changes"]

    # Build commit message
    lines = []

    # Subject line
    subject = f"[{plan_id}] {summary}"
    if len(subject) > 72:
        # Truncate subject to 72 characters
        subject = subject[:69] + "..."
    lines.append(subject)

    # Blank line
    lines.append("")

    # Metadata
    lines.append(f"Mode: {mode}")

    if agents:
        agents_str = ", ".join(f"@{a}" for a in agents)
        lines.append(f"Agents: {agents_str}")

    lines.append(f"Files: {files_count} changed")

    # Changes section
    if changes:
        lines.append("")
        lines.append("Changes:")
        for change in changes:
            # Clean up change text
            change = change.strip()
            if not change.startswith("-"):
                change = f"- {change}"
            lines.append(change)

    # Co-author
    lines.append("")
    lines.append(COAUTHOR)

    return "\n".join(lines)


def stage_all_changes(project_root: Path) -> bool:
    """Stage all changes for commit."""
    try:
        subprocess.run(
            ["git", "add", "-A"],
            cwd=project_root,
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Failed to stage changes: {e}", file=sys.stderr)
        return False


def create_commit(commit_message: str, project_root: Path) -> Optional[str]:
    """Create git commit and return commit hash."""
    # Write commit message to temp file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    msg_file = Path(COMMIT_MSG_TEMPLATE.format(timestamp=timestamp))

    try:
        msg_file.write_text(commit_message)

        # Create commit
        result = subprocess.run(
            ["git", "commit", "-F", str(msg_file)],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )

        # Get commit hash
        hash_result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )

        commit_hash = hash_result.stdout.strip()

        # Clean up temp file
        msg_file.unlink()

        return commit_hash

    except subprocess.CalledProcessError as e:
        print(f"⚠️  Commit failed: {e}", file=sys.stderr)
        if e.stderr:
            print(f"   Error: {e.stderr}", file=sys.stderr)

        # Clean up temp file
        if msg_file.exists():
            msg_file.unlink()

        return None


def log_commit(metadata: Dict[str, Any], commit_hash: str, project_root: Path) -> None:
    """Log commit to git-commits.md."""
    log_path = project_root / GIT_COMMITS_LOG

    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create log file with header if it doesn't exist
    if not log_path.exists():
        log_path.write_text(
            "# Git Commit Log\n\n"
            "This file tracks all auto-commits made by Claude Code.\n\n"
            "## Format\n"
            "- [PLAN-ID] {commit-hash} - {files} files - {timestamp}\n\n"
            "## Commits\n"
        )

    # Prepare log entry
    plan_id = metadata["plan_id"]
    mode = metadata["mode"]
    agents = metadata["agents"]
    files_count = len(metadata["files_changed"])
    summary = metadata["summary"]
    timestamp = datetime.now().isoformat()

    entry = f"- [{plan_id}] {commit_hash} - {files_count} files - {timestamp}\n"
    entry += f"  - Mode: {mode}\n"

    if agents:
        agents_str = ", ".join(f"@{a}" for a in agents)
        entry += f"  - Agents: {agents_str}\n"

    entry += f"  - Summary: {summary}\n"

    # Append to log
    with open(log_path, "a") as f:
        f.write(entry)


def check_git_repository(project_root: Path) -> bool:
    """Check if we're in a git repository."""
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=project_root,
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def has_changes_to_commit(project_root: Path) -> bool:
    """Check if there are any changes to commit."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )

        return bool(result.stdout.strip())

    except subprocess.CalledProcessError:
        return False


def hook(tool_name: str, tool_input: Dict[str, Any], tool_output: Any) -> None:
    """
    Post-tool hook for TodoWrite completion.

    Args:
        tool_name: Name of the tool that was executed
        tool_input: Input parameters passed to the tool
        tool_output: Output/result from the tool execution
    """
    # Only process TodoWrite tool
    if tool_name != "TodoWrite":
        return

    # Extract TODOs from input
    todos = tool_input.get("todos", [])

    if not todos:
        return

    # Check if all TODOs are complete
    if not check_all_todos_complete(todos):
        return  # Not ready for commit yet

    # Get project root
    project_root = get_project_root()

    # Check if in git repository
    if not check_git_repository(project_root):
        print("📝 Not in git repository - skipping auto-commit", flush=True)
        return

    # Check for changes
    if not has_changes_to_commit(project_root):
        print("📝 No changes to commit - working tree clean", flush=True)
        return

    # Find active plan
    plan_id = find_active_plan()

    if not plan_id:
        print("⚠️  No active plan found - skipping auto-commit", file=sys.stderr)
        return

    print(f"\n🔁 Plan completed - triggering auto-commit for {plan_id}...", flush=True)

    # Extract plan metadata
    metadata = extract_plan_metadata(plan_id)

    # Generate commit message
    commit_message = generate_commit_message(metadata)

    # Stage all changes
    if not stage_all_changes(project_root):
        print("⚠️  Could not stage changes - auto-commit aborted", file=sys.stderr)
        return

    # Create commit
    commit_hash = create_commit(commit_message, project_root)

    if not commit_hash:
        print("⚠️  Commit failed - see error above", file=sys.stderr)
        return

    # Log commit
    log_commit(metadata, commit_hash, project_root)

    # Success output
    print(f"\n✅ AUTO-COMMIT: {plan_id}", flush=True)
    print(f"   Hash: {commit_hash}", flush=True)
    print(f"   Files: {len(metadata['files_changed'])}", flush=True)
    print(f"   Message: {metadata['summary']}", flush=True)
    print(f"\n   View commit: git show {commit_hash}", flush=True)
    print(f"   Push to remote: git push origin main", flush=True)


# CLI interface for manual testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Auto-commit hook - test and debug"
    )
    parser.add_argument(
        "action",
        choices=["test", "status", "log"],
        help="Action to perform"
    )
    parser.add_argument(
        "--plan-id",
        help="Specific plan ID to test"
    )

    args = parser.parse_args()

    project_root = get_project_root()

    if args.action == "test":
        plan_id = args.plan_id or find_active_plan()
        if not plan_id:
            print("❌ No plan ID found")
            sys.exit(1)

        print(f"Testing auto-commit for {plan_id}...")
        metadata = extract_plan_metadata(plan_id)
        print(json.dumps(metadata, indent=2))

        message = generate_commit_message(metadata)
        print("\nGenerated commit message:")
        print("-" * 60)
        print(message)
        print("-" * 60)

    elif args.action == "status":
        print(f"Project root: {project_root}")
        print(f"Git repository: {check_git_repository(project_root)}")
        print(f"Has changes: {has_changes_to_commit(project_root)}")
        print(f"Active plan: {find_active_plan()}")

    elif args.action == "log":
        log_path = project_root / GIT_COMMITS_LOG
        if log_path.exists():
            print(log_path.read_text())
        else:
            print("No commit log found")
