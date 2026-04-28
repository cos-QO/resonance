#!/usr/bin/env python3
"""
Hook: compound-scope-enforcement.py
Trigger: PreToolUse (Write, Edit, MultiEdit tools)
Purpose: Enforce sub-plan scope isolation during compound mode execution

This hook validates file operations against sub-plan scope definitions to ensure:
1. Each sub-plan only accesses files in its allowed scope
2. Forbidden paths are blocked (other sub-plans, protected files)
3. Scope violations are logged and blocked
4. Coordination hub (watchdog) is notified of violations
"""

import json
import os
import re
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


# Configuration — folder name detected dynamically for migration compatibility
CLAUDE_FOLDER_NAMES = [".claude", "claude"]  # Preferred order: .claude first
COMPOUND_MEMORY_SUBPATH = "memory/compound"
VIOLATIONS_LOG = "violations.log"
ACTIVE_SUBPLAN_SUBPATH = "temp/active-subplan.txt"


def get_project_root() -> Path:
    """Get project root directory (where .claude/ or claude/ folder exists)."""
    current = Path.cwd()

    for folder_name in CLAUDE_FOLDER_NAMES:
        if (current / folder_name).exists():
            return current

    # Check parent directories (up to 3 levels)
    for parent in [current.parent, current.parent.parent, current.parent.parent.parent]:
        for folder_name in CLAUDE_FOLDER_NAMES:
            if (parent / folder_name).exists():
                return parent

    # Fallback to current directory
    return current


def get_claude_dir() -> Path:
    """Find the actual claude directory (.claude or claude)."""
    root = get_project_root()
    for folder_name in CLAUDE_FOLDER_NAMES:
        candidate = root / folder_name
        if candidate.exists():
            return candidate
    return root / CLAUDE_FOLDER_NAMES[0]  # Default to .claude


def get_active_subplan() -> Optional[str]:
    """Get the currently active sub-plan ID from temp file."""
    claude_dir = get_claude_dir()
    active_file = claude_dir / ACTIVE_SUBPLAN_SUBPATH

    if not active_file.exists():
        return None

    try:
        subplan_id = active_file.read_text().strip()
        return subplan_id if subplan_id else None
    except Exception:
        return None


def load_subplan_config(subplan_id: str) -> Optional[Dict[str, Any]]:
    """Load sub-plan configuration including scope definitions."""
    project_root = get_project_root()

    # Extract plan ID from subplan ID (e.g., PLAN-001 from SUBPLAN-001-A)
    match = re.search(r'(PLAN-[^-]+-[^-]+)', subplan_id)
    if not match:
        return None

    plan_id = match.group(1)

    # Load subplan config
    config_path = get_claude_dir() / COMPOUND_MEMORY_SUBPATH / plan_id / subplan_id / "config.yaml"

    if not config_path.exists():
        return None

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"⚠️  Warning: Could not load subplan config: {e}", file=sys.stderr)
        return None


def matches_glob(file_path: str, pattern: str) -> bool:
    """
    Check if file path matches glob pattern.

    Supports:
    - ** : matches any depth
    - * : matches within directory
    - Relative paths from project root
    """
    from fnmatch import fnmatch

    # Normalize paths
    file_path = file_path.replace("\\", "/").lstrip("/")
    pattern = pattern.replace("\\", "/").lstrip("/")

    # Handle ** patterns (any depth)
    if "**" in pattern:
        # Convert ** to regex pattern
        regex_pattern = pattern.replace("**", ".*")
        regex_pattern = regex_pattern.replace("*", "[^/]*")
        regex_pattern = f"^{regex_pattern}$"

        return bool(re.match(regex_pattern, file_path))

    # Handle * patterns (within directory)
    return fnmatch(file_path, pattern)


def validate_file_access(file_path: str, subplan_id: str, operation: str) -> tuple[bool, Optional[str]]:
    """
    Validate if subplan can access file.

    Returns:
        (allowed: bool, reason: Optional[str])
    """
    # Load subplan config
    config = load_subplan_config(subplan_id)

    if not config:
        # No config found - allow (not in compound mode or config error)
        return (True, None)

    scope = config.get("scope", {})
    allowed_patterns = scope.get("allowed", [])
    forbidden_patterns = scope.get("forbidden", [])

    # Normalize file path (relative to project root)
    project_root = get_project_root()
    try:
        file_path_abs = Path(file_path).resolve()
        file_path_rel = str(file_path_abs.relative_to(project_root))
    except Exception:
        # If path is already relative or can't be resolved, use as-is
        file_path_rel = file_path

    # Check forbidden paths first (highest priority)
    for forbidden_pattern in forbidden_patterns:
        if matches_glob(file_path_rel, forbidden_pattern):
            # Determine which subplan owns this path
            owner = determine_path_owner(file_path_rel, subplan_id)
            reason = (
                f"🚫 SCOPE VIOLATION: {subplan_id}\n"
                f"   Cannot access: {file_path_rel}\n"
                f"   Operation: {operation}\n"
                f"   Forbidden by: {forbidden_pattern}\n"
                f"   {owner}"
            )
            return (False, reason)

    # Check allowed paths
    for allowed_pattern in allowed_patterns:
        if matches_glob(file_path_rel, allowed_pattern):
            return (True, None)  # Access granted

    # Not in any allowed pattern
    reason = (
        f"⚠️ SCOPE WARNING: {subplan_id}\n"
        f"   File not in allowed scope: {file_path_rel}\n"
        f"   Operation: {operation}\n"
        f"   Allowed patterns: {allowed_patterns}\n"
        f"   This operation will be blocked."
    )

    return (False, reason)


def determine_path_owner(file_path: str, current_subplan: str) -> str:
    """Determine which sub-plan owns this file path."""
    project_root = get_project_root()

    # Extract plan ID
    match = re.search(r'(PLAN-[^-]+-[^-]+)', current_subplan)
    if not match:
        return "This file belongs to another SUBPLAN or is protected"

    plan_id = match.group(1)

    # Check all other subplans in this plan
    plan_dir = get_claude_dir() / COMPOUND_MEMORY_SUBPATH / plan_id

    if not plan_dir.exists():
        return "This file belongs to another SUBPLAN or is protected"

    for subplan_dir in plan_dir.iterdir():
        if not subplan_dir.is_dir() or not subplan_dir.name.startswith("SUBPLAN-"):
            continue

        if subplan_dir.name == current_subplan:
            continue  # Skip current subplan

        # Load other subplan config
        config_path = subplan_dir / "config.yaml"
        if not config_path.exists():
            continue

        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            allowed = config.get("scope", {}).get("allowed", [])

            # Check if this file matches this subplan's scope
            for pattern in allowed:
                if matches_glob(file_path, pattern):
                    return f"This file belongs to {subplan_dir.name}"

        except Exception:
            continue

    return "This file is protected or belongs to another SUBPLAN"


def log_violation(subplan_id: str, file_path: str, operation: str, reason: str) -> None:
    """Log scope violation to violations.log."""
    project_root = get_project_root()

    # Extract plan ID
    match = re.search(r'(PLAN-[^-]+-[^-]+)', subplan_id)
    if not match:
        return

    plan_id = match.group(1)

    # Violations log path
    log_path = get_claude_dir() / COMPOUND_MEMORY_SUBPATH / plan_id / VIOLATIONS_LOG

    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Log entry
    timestamp = datetime.now().isoformat()
    entry = (
        f"[{timestamp}] SCOPE VIOLATION: {subplan_id}\n"
        f"  File: {file_path}\n"
        f"  Operation: {operation}\n"
        f"  Reason: {reason}\n"
        f"  Action: BLOCKED\n\n"
    )

    # Append to log
    with open(log_path, "a") as f:
        f.write(entry)


def hook(tool_name: str, tool_input: Dict[str, Any]) -> None:
    """
    Pre-tool hook for scope enforcement.

    Args:
        tool_name: Name of the tool about to be executed
        tool_input: Input parameters that will be passed to the tool
    """
    # Only process file modification tools
    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        return

    # Check if in compound mode (active subplan exists)
    subplan_id = get_active_subplan()

    if not subplan_id:
        # Not in compound mode - allow all operations
        return

    # Extract file path from tool input
    file_path = tool_input.get("file_path")

    if not file_path:
        # No file path - allow (shouldn't happen)
        return

    # Validate file access
    allowed, reason = validate_file_access(file_path, subplan_id, tool_name)

    if not allowed:
        # Log violation
        log_violation(subplan_id, file_path, tool_name, reason or "Unknown")

        # Block operation
        print(f"\n{reason}\n", file=sys.stderr, flush=True)
        print("   Operation BLOCKED.", file=sys.stderr, flush=True)
        print("   Contact coordinator to resolve.\n", file=sys.stderr, flush=True)

        # Exit with error to block the tool execution
        sys.exit(1)

    # Access allowed - continue


# CLI interface for manual testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Compound scope enforcement hook - test and debug"
    )
    parser.add_argument(
        "action",
        choices=["test", "status", "violations"],
        help="Action to perform"
    )
    parser.add_argument(
        "--subplan-id",
        help="Specific subplan ID to test"
    )
    parser.add_argument(
        "--file-path",
        help="File path to test access"
    )
    parser.add_argument(
        "--operation",
        choices=["Write", "Edit", "MultiEdit"],
        default="Write",
        help="Operation type"
    )

    args = parser.parse_args()

    project_root = get_project_root()

    if args.action == "test":
        if not args.subplan_id or not args.file_path:
            print("❌ --subplan-id and --file-path required for test")
            sys.exit(1)

        print(f"Testing scope enforcement:")
        print(f"  Subplan: {args.subplan_id}")
        print(f"  File: {args.file_path}")
        print(f"  Operation: {args.operation}")
        print()

        allowed, reason = validate_file_access(
            args.file_path,
            args.subplan_id,
            args.operation
        )

        if allowed:
            print("✅ ACCESS GRANTED")
        else:
            print("❌ ACCESS DENIED")
            print(reason)

    elif args.action == "status":
        active_subplan = get_active_subplan()

        if not active_subplan:
            print("No active subplan (not in compound mode)")
        else:
            print(f"Active Subplan: {active_subplan}")

            config = load_subplan_config(active_subplan)
            if config:
                print("\nScope Configuration:")
                print(yaml.dump(config.get("scope", {}), default_flow_style=False))
            else:
                print("⚠️  Could not load subplan config")

    elif args.action == "violations":
        if not args.subplan_id:
            print("❌ --subplan-id required for violations")
            sys.exit(1)

        # Extract plan ID
        match = re.search(r'(PLAN-[^-]+-[^-]+)', args.subplan_id)
        if not match:
            print("❌ Invalid subplan ID format")
            sys.exit(1)

        plan_id = match.group(1)
        log_path = get_claude_dir() / COMPOUND_MEMORY_SUBPATH / plan_id / VIOLATIONS_LOG

        if log_path.exists():
            print(log_path.read_text())
        else:
            print(f"No violations logged for {plan_id}")
