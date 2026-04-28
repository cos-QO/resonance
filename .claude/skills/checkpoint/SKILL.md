---
name: checkpoint
description: Create or restore session checkpoints for context preservation across compaction. Use before /compact or after reconnecting to restore context.
argument-hint: [save|restore]
allowed-tools: Read, Write, Edit, Glob
disable-model-invocation: true
---
# /checkpoint — Session Context Preservation

Save or restore session context for continuity across compaction.

## Commands
- `/checkpoint save` or `/checkpoint` — Create checkpoint before compaction
- `/checkpoint restore` — Restore context after compaction

## What Gets Saved
- Project goals and objectives
- Active constraints and rules
- Current progress and stable decisions
- Key files and their roles (top 5-10)
- Current task and next steps
- Pending issues and blockers

## Storage
- Latest: `.claude/memory/session_checkpoints/latest.md`
- History: `.claude/memory/session_checkpoints/history/` (last 10)

## Arguments
- `$ARGUMENTS` — "save" (default) or "restore"
