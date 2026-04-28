#!/usr/bin/env python3
"""
Hook: protected-files-check.py
Trigger: PreToolUse (Write, Edit, MultiEdit tools)
Purpose: Protect system files from accidental agent modification

This hook enforces the protected files registry to maintain system integrity:
1. Block modifications to configuration, agents, hooks, knowledge, standards
2. Allow documenter agent full access (system maintainer)
3. Log violations for audit trail
4. Provide clear error messages
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from fnmatch import fnmatch


# Configuration — folder name detected dynamically for migration compatibility
CLAUDE_FOLDER_NAMES = [".claude", "claude"]  # Preferred order: .claude first
PROTECTED_FILES_SUBPATH = "memory/standards/protected-files.md"
VIOLATIONS_LOG_SUBPATH = "memory/violations.log"
DOCUMENTER_AGENT = "documenter"


def _claude_folder() -> str:
    """Detect active claude folder name (.claude or claude)."""
    current = Path.cwd()
    for folder_name in CLAUDE_FOLDER_NAMES:
        if (current / folder_name).exists():
            return folder_name
    for parent in [current.parent, current.parent.parent, current.parent.parent.parent]:
        for folder_name in CLAUDE_FOLDER_NAMES:
            if (parent / folder_name).exists():
                return folder_name
    return CLAUDE_FOLDER_NAMES[0]  # Default to .claude


def _protected_patterns() -> list:
    """Generate protected patterns using detected folder name."""
    cf = _claude_folder()
    return [
        f"{cf}/settings.json",
        f"{cf}/.claude-project.json",
        ".gitignore",
        ".git/config",
        f"{cf}/agents/**/*.md",
        f"{cf}/hooks/*.py",
        f"{cf}/hooks/*.sh",
        f"{cf}/knowledge/system/**/*.md",
        f"{cf}/memory/standards/*.md",
        f"{cf}/commands/**/*.md",
    ]


# Default protected patterns (computed on import)
DEFAULT_PROTECTED_PATTERNS = _protected_patterns()

PROTECTED_FILES_REGISTRY = f"{_claude_folder()}/{PROTECTED_FILES_SUBPATH}"
VIOLATIONS_LOG = f"{_claude_folder()}/{VIOLATIONS_LOG_SUBPATH}"


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


def load_protected_patterns() -> List[str]:
    """Load protected file patterns from registry."""
    project_root = get_project_root()
    registry_file = project_root / PROTECTED_FILES_REGISTRY

    if not registry_file.exists():
        # Use default patterns if registry not found
        return DEFAULT_PROTECTED_PATTERNS

    try:
        content = registry_file.read_text()

        # Extract patterns from registry (look for glob patterns in code blocks or lists)
        patterns = []

        # Match patterns in YAML-style lists
        pattern_matches = re.findall(r'^\s*-\s*["\'](.+?)["\']', content, re.MULTILINE)
        patterns.extend(pattern_matches)

        # Also match unquoted patterns
        unquoted_matches = re.findall(r'^\s*-\s+([^\s"\']+)$', content, re.MULTILINE)
        patterns.extend(unquoted_matches)

        # Remove duplicates and clean up
        patterns = list(set(p.strip() for p in patterns if p.strip()))

        return patterns if patterns else DEFAULT_PROTECTED_PATTERNS

    except Exception as e:
        print(f"⚠️  Warning: Could not load protected patterns: {e}", file=sys.stderr)
        return DEFAULT_PROTECTED_PATTERNS


def matches_glob(file_path: str, pattern: str) -> bool:
    """
    Check if file path matches glob pattern.

    Supports:
    - ** : matches any depth
    - * : matches within directory
    - Relative paths from project root
    """
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


def get_current_agent() -> Optional[str]:
    """Get the currently active agent from context."""
    # Try to get agent from environment variable (if set by system)
    agent = os.environ.get("CLAUDE_ACTIVE_AGENT")

    if agent:
        return agent.lower()

    # Try to infer from call stack or context
    # This is a placeholder - actual implementation would need
    # integration with Claude Code's agent tracking system

    # For now, return None (unknown agent)
    return None


def determine_protection_category(file_path: str) -> str:
    """Determine which protection category a file belongs to."""
    file_path_lower = file_path.lower()

    if "settings.json" in file_path_lower or ".claude-project.json" in file_path_lower:
        return "System Configuration"
    elif "/agents/" in file_path_lower:
        return "Agent Definitions"
    elif "/hooks/" in file_path_lower:
        return "System Hooks"
    elif "/knowledge/system/" in file_path_lower:
        return "Core Knowledge System"
    elif "/standards/" in file_path_lower:
        return "Memory Standards"
    elif "/commands/" in file_path_lower:
        return "Slash Commands"
    elif "/skills/" in file_path_lower:
        return "Skills"
    else:
        return "Protected File"


def get_protection_reason(category: str) -> str:
    """Get the reason why this category is protected."""
    reasons = {
        "System Configuration": "Configuration changes could break hooks, permissions, or integrations",
        "Agent Definitions": "Agent modifications could cause unpredictable behavior or role confusion",
        "System Hooks": "Hook modifications could disable enforcement or create security vulnerabilities",
        "Core Knowledge System": "System knowledge defines protocols that must remain consistent",
        "Memory Standards": "Standards define conventions that should not change frequently",
        "Slash Commands": "Command behavior must be predictable and documented",
        "Skills": "Skill definitions must remain stable for consistent agent behavior",
    }

    return reasons.get(category, "This file is critical to system integrity")


def is_protected(file_path: str, agent: Optional[str]) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Check if file is protected from this agent.

    Returns:
        (is_protected: bool, category: Optional[str], reason: Optional[str])
    """
    # Documenter has full access (system maintainer)
    if agent == DOCUMENTER_AGENT:
        return (False, None, None)

    # Normalize file path
    project_root = get_project_root()
    try:
        file_path_abs = Path(file_path).resolve()
        file_path_rel = str(file_path_abs.relative_to(project_root))
    except Exception:
        # If path can't be resolved, use as-is
        file_path_rel = file_path

    # Load protected patterns
    protected_patterns = load_protected_patterns()

    # Check if file matches any protected pattern
    for pattern in protected_patterns:
        if matches_glob(file_path_rel, pattern):
            category = determine_protection_category(file_path_rel)
            reason = get_protection_reason(category)
            return (True, category, reason)

    # Not protected
    return (False, None, None)


def log_violation(file_path: str, agent: Optional[str], operation: str, category: str, reason: str) -> None:
    """Log protection violation."""
    project_root = get_project_root()
    log_path = project_root / VIOLATIONS_LOG

    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Log entry
    timestamp = datetime.now().isoformat()
    agent_name = agent or "unknown"
    entry = (
        f"[{timestamp}] PROTECTED FILE VIOLATION\n"
        f"Agent: {agent_name}\n"
        f"File: {file_path}\n"
        f"Operation: {operation}\n"
        f"Category: {category}\n"
        f"Action: BLOCKED\n"
        f"Reason: {reason}\n\n"
    )

    # Append to log
    with open(log_path, "a") as f:
        f.write(entry)


def hook(tool_name: str, tool_input: Dict[str, Any]) -> None:
    """
    Pre-tool hook for protected files check.

    Args:
        tool_name: Name of the tool about to be executed
        tool_input: Input parameters that will be passed to the tool
    """
    # Only process file modification tools
    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        return

    # Extract file path from tool input
    file_path = tool_input.get("file_path")

    if not file_path:
        # No file path - allow (shouldn't happen)
        return

    # Get current agent
    agent = get_current_agent()

    # Check if file is protected
    protected, category, reason = is_protected(file_path, agent)

    if protected:
        # Log violation
        log_violation(file_path, agent, tool_name, category, reason)

        # Block operation with clear error message
        agent_name = agent or "this agent"
        print(f"\n🚫 PROTECTED FILE: {file_path}\n", file=sys.stderr, flush=True)
        print(f"   This file is protected from modification by {agent_name}.\n", file=sys.stderr, flush=True)
        print(f"   Protected Category: {category}", file=sys.stderr, flush=True)
        print(f"   Reason: {reason}\n", file=sys.stderr, flush=True)
        print("   If you need to modify this file:", file=sys.stderr, flush=True)
        print("     1. Contact user for approval", file=sys.stderr, flush=True)
        print("     2. Use @documenter agent for documentation updates", file=sys.stderr, flush=True)
        print("     3. Submit request via proper channels\n", file=sys.stderr, flush=True)
        print("   Operation BLOCKED.\n", file=sys.stderr, flush=True)

        # Exit with error to block the tool execution
        sys.exit(1)

    # File not protected - allow operation


# CLI interface for manual testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Protected files check hook - test and debug"
    )
    parser.add_argument(
        "action",
        choices=["test", "patterns", "violations"],
        help="Action to perform"
    )
    parser.add_argument(
        "--file-path",
        help="File path to test"
    )
    parser.add_argument(
        "--agent",
        help="Agent name to test as"
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
        if not args.file_path:
            print("❌ --file-path required for test")
            sys.exit(1)

        agent = args.agent or "developer"

        print(f"Testing protected files check:")
        print(f"  File: {args.file_path}")
        print(f"  Agent: {agent}")
        print(f"  Operation: {args.operation}")
        print()

        protected, category, reason = is_protected(args.file_path, agent)

        if protected:
            print("❌ BLOCKED (protected)")
            print(f"   Category: {category}")
            print(f"   Reason: {reason}")
        else:
            print("✅ ALLOWED (not protected)")

    elif args.action == "patterns":
        print("Protected File Patterns:")
        print()

        patterns = load_protected_patterns()

        for i, pattern in enumerate(patterns, 1):
            print(f"  {i}. {pattern}")

        print()
        print(f"Total: {len(patterns)} patterns")

    elif args.action == "violations":
        log_path = project_root / VIOLATIONS_LOG

        if log_path.exists():
            print("Violations Log:")
            print()
            print(log_path.read_text())
        else:
            print("No violations logged")
