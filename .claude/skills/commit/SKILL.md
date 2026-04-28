---
name: commit
description: "Use when committing code changes — after completing a task, finishing a plan phase, checkpointing progress, or when user says 'commit'. Plan-aware: auto-detects execution tracker and generates structured checkpoint commits with phase context and next-steps."
argument-hint: [commit-message]
allowed-tools: Bash, Read, Glob, Grep
disable-model-invocation: true
---
# /commit — Git Commit & Plan Checkpoint

Create well-formatted git commits. When running inside a plan, automatically generates structured checkpoint commits with phase context and next-steps instructions.

## Workflow

### Step 1: Analyze Changes
1. Run `git status` and `git diff --staged` to analyze changes
2. If no staged changes, stage modified files (ask user if ambiguous)
3. If no changes at all, report "nothing to commit" and stop

### Step 2: Detect Plan Context
Check if `/.claude/memory/active/execution-tracker.json` exists:
- **If YES** → Plan-aware mode (see below)
- **If NO** → Standard mode

### Step 3: Generate Commit Message

#### Standard Mode (no active plan)
```
type(scope): description

[body if needed]

Co-Authored-By: Claude <noreply@anthropic.com>
```
Types: feat, fix, refactor, docs, test, chore, style, perf

If `$ARGUMENTS` provided, use as commit message. Otherwise auto-generate from diff.

#### Plan-Aware Mode (active execution tracker)
Read the execution tracker and generate a structured checkpoint:

```
type(scope): description

[PLAN-ID] Phase N/M: [Phase Title]
Status: [completed phases] of [total phases] complete

## What was done
- [Summary of changes in this phase from tracker + diff]

## Agents involved
- @agent1: [task summary]
- @agent2: [task summary]

## Next steps
- Phase N+1: [title] → @agent (pending)
- [Any blockers or decisions needed]

## Resume instructions
To continue this plan:
1. Read /.claude/memory/active/execution-tracker.json
2. Next pending phase: Phase N+1 — [title]
3. Run: [next agent/skill invocation]

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Step 4: Commit
1. Stage relevant files (prefer specific files over `git add -A`)
2. Exclude: .env, credentials, secrets, node_modules, __pycache__
3. Create commit
4. Output commit hash and summary

## Plan Checkpoint Rules
- Read the execution tracker to determine current phase and progress
- Include completed phase summary from tracker tasks
- Always include "Next steps" with the specific next phase and assigned agent
- Always include "Resume instructions" so a fresh session can pick up where we left off
- Update the execution tracker: mark current phase as "completed" with timestamp
- If this is the FINAL phase, note "Plan complete" instead of next steps

## General Rules
- Never push to remote (user must explicitly request)
- Never commit .env, credentials, or secrets
- If `$ARGUMENTS` provided, use as commit message (skip auto-generation)
- If no arguments, auto-generate from diff analysis + plan context
- Commit message subject line max 72 characters

## Arguments
- `$ARGUMENTS` — Optional commit message or title
