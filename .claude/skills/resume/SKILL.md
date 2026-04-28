---
name: resume
description: Session recovery after disconnect or context loss. Reconstructs work state from checkpoints, TODOs, and git history. Only for resuming interrupted Claude sessions — NOT for resume/CV documents.
argument-hint: [context-hint]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
disable-model-invocation: true
---
# /resume — Session Recovery

Recover state and continue work after disconnect or context loss.

## Recovery Sources (checked in order)
1. Session checkpoints: `.claude/memory/session_checkpoints/latest.md`
2. Active TODOs: `.claude/memory/todos/`
3. Active plans: `.claude/memory/active/plans/`
4. Git status and recent commits
5. Recently modified files

## Workflow
1. Scan all recovery sources
2. Reconstruct current state and progress
3. Present recovery summary to user
4. Offer continuation options:
   - Resume active task
   - Start next planned task
   - Review and reprioritize

## Arguments
- `$ARGUMENTS` — Optional hint about what was being worked on
