#!/usr/bin/env python3
"""
Settings permission validator/fixer.

Claude Code rejects MCP permission rules that include path patterns in parens,
e.g. `mcp__filesystem__write_file(.claude/hooks/**)`. Those rules are skipped
at session start and produce a Settings Warning on every launch.

This script:
  1. Finds settings.json (project .claude/ and/or user ~/.claude/).
  2. Detects invalid `mcp__<server>__<tool>(<path>)` rules in allow/deny.
  3. Backs the file up (settings.json.bak-<timestamp>).
  4. For allow: drops the invalid rule (redundant with `mcp__<server>__*`).
  5. For deny:  replaces with the un-parenthesized hard-deny variant
                (e.g. `mcp__filesystem__write_file`), then dedups.
  6. Writes the cleaned file and prints a diff summary.

Modes:
  --check   Report only, no writes. Exit 1 if issues found.
  --fix     Apply fixes (default).
  --path P  Operate on a specific settings.json instead of auto-detect.
  --user    Also process ~/.claude/settings.json.

Usage from /setup:
    python3 .claude/scripts/fix-permissions.py --fix
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

INVALID_MCP_RE = re.compile(r"^(mcp__[A-Za-z0-9_]+__[A-Za-z0-9_]+)\(([^)]*)\)$")


def find_project_settings() -> Path | None:
    d = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()
    while d != d.parent:
        candidate = d / ".claude" / "settings.json"
        if candidate.is_file():
            return candidate
        d = d.parent
    return None


def clean_rules(rules: list[str], kind: str) -> tuple[list[str], list[tuple[str, str]]]:
    """
    Return (cleaned_rules, actions) where actions is a list of
    (original_rule, action_description).
    """
    seen: set[str] = set()
    out: list[str] = []
    actions: list[tuple[str, str]] = []

    for rule in rules:
        m = INVALID_MCP_RE.match(rule.strip())
        if not m:
            if rule not in seen:
                seen.add(rule)
                out.append(rule)
            continue

        base_tool = m.group(1)
        path_pat = m.group(2)

        if kind == "allow":
            # Drop — redundant with `mcp__<server>__*` wildcards users already have.
            actions.append((rule, f"removed (MCP rules cannot scope to path `{path_pat}`; covered by `{base_tool.rsplit('__',1)[0]}__*`)"))
            continue

        # deny: replace with un-parenthesized hard deny
        replacement = base_tool
        if replacement not in seen:
            seen.add(replacement)
            out.append(replacement)
            actions.append((rule, f"replaced with `{replacement}` (hard deny — MCP cannot do path-scoped deny)"))
        else:
            actions.append((rule, f"removed (duplicate of existing `{replacement}`)"))

    return out, actions


def process(settings_path: Path, apply: bool) -> dict:
    result = {
        "path": str(settings_path),
        "exists": settings_path.is_file(),
        "valid_json": False,
        "changed": False,
        "allow_actions": [],
        "deny_actions": [],
        "backup": None,
        "error": None,
    }
    if not result["exists"]:
        return result

    try:
        original_text = settings_path.read_text()
        data = json.loads(original_text)
        result["valid_json"] = True
    except json.JSONDecodeError as e:
        result["error"] = f"Invalid JSON: {e}"
        return result

    perms = data.get("permissions") or {}
    allow = list(perms.get("allow") or [])
    deny = list(perms.get("deny") or [])

    new_allow, allow_actions = clean_rules(allow, "allow")
    new_deny, deny_actions = clean_rules(deny, "deny")

    result["allow_actions"] = allow_actions
    result["deny_actions"] = deny_actions

    if not (allow_actions or deny_actions):
        return result  # nothing to do

    result["changed"] = True
    if not apply:
        return result

    # Backup
    ts = time.strftime("%Y%m%d-%H%M%S")
    backup = settings_path.with_suffix(f".json.bak-{ts}")
    backup.write_text(original_text)
    result["backup"] = str(backup)

    # Preserve other fields; only touch permissions.
    data.setdefault("permissions", {})
    data["permissions"]["allow"] = new_allow
    data["permissions"]["deny"] = new_deny

    settings_path.write_text(json.dumps(data, indent=2) + "\n")
    return result


def print_report(r: dict) -> None:
    print(f"\n=== {r['path']} ===")
    if not r["exists"]:
        print("  (not found, skipped)")
        return
    if r["error"]:
        print(f"  ERROR: {r['error']}")
        return
    if not r["changed"]:
        print("  OK — no invalid MCP permission rules.")
        return
    print(f"  Issues found: {len(r['allow_actions'])} allow, {len(r['deny_actions'])} deny")
    for rule, action in r["allow_actions"]:
        print(f"    allow: {rule}")
        print(f"      -> {action}")
    for rule, action in r["deny_actions"]:
        print(f"    deny:  {rule}")
        print(f"      -> {action}")
    if r["backup"]:
        print(f"  Backup written: {r['backup']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Report only, do not write")
    mode.add_argument("--fix", action="store_true", help="Apply fixes (default)")
    ap.add_argument("--path", help="Specific settings.json to process")
    ap.add_argument("--user", action="store_true", help="Also process ~/.claude/settings.json")
    args = ap.parse_args()

    apply = not args.check  # default is fix

    targets: list[Path] = []
    if args.path:
        targets.append(Path(args.path).expanduser().resolve())
    else:
        proj = find_project_settings()
        if proj:
            targets.append(proj)
    if args.user:
        user = Path("~/.claude/settings.json").expanduser()
        if user.is_file() and user not in targets:
            targets.append(user)

    if not targets:
        print("No settings.json found (looked for .claude/settings.json upward from CWD).")
        return 0

    any_changed = False
    for t in targets:
        r = process(t, apply=apply)
        print_report(r)
        if r["changed"]:
            any_changed = True

    if any_changed:
        if apply:
            print("\nDone. Restart Claude Code to clear the Settings Warning.")
            return 0
        print("\nIssues detected. Re-run without --check to fix.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
