---
name: cleanup
description: "Use when project files need reorganization, user says 'cleanup', 'organize', 'tidy', or file structure has drifted from standards. NOT for code quality review (use /review) or refactoring code logic (use /task)."
argument-hint: [scope]
context: fork
agent: pm
disable-model-invocation: true
---
# /cleanup — File Organization

Organize project files according to established standards.

## Workflow
1. Read `.claude/memory/standards/folder-structure.md`
2. Scan project for misplaced files
3. Identify cleanup opportunities:
   - Files in wrong locations
   - Orphaned temp files
   - Stale artifacts
   - Root directory clutter
4. Propose changes to user (never delete without confirmation)
5. Execute approved moves/reorganization
6. Update references in code if files moved

## Rules
- SOFT cleanup only — propose, don't force
- Never delete files without user confirmation
- Update imports/references when moving files
- Follow established project conventions

## Arguments
- `$ARGUMENTS` — Optional scope (e.g., "root", "tests", "docs")
