---
name: pd-issue
description: "Fetch complete context for a Resonance issue — local memory, Linear state, comments, artifacts, handoffs, and parent plan. Use before working on any issue or when debugging a stuck run."
argument-hint: <issue-id>
allowed-tools: Read, mcp__linear__*
---

# pd-issue — Issue Context Skill

Brings you fully up to speed on any Resonance issue. Works from the issue ID alone — no other context needed.

## When to Use

- Before starting or resuming work on an issue
- When a human asks "what's happening with QO-42?"
- When debugging a stuck or failed run
- At the start of every agent session for issues with prior iterations
- Before writing any code — always know the history

## What It Fetches

| Source | What |
|---|---|
| `runs/memory/{id}/plan.md` | The approved plan (if this is a phase issue, also fetches parent plan) |
| `runs/memory/{id}/context.json` | Current iteration, status, what's next |
| `runs/memory/{id}/handoffs/` | All iteration handoffs — what each run did and left off |
| `runs/memory/{id}/feedback/` | All human feedback entries in chronological order |
| `runs/memory/{id}/artifacts.json` | All produced artifacts: URLs, file paths, PR links |
| `runs/memory/{id}/decisions.md` | Key decisions and rationale |
| Linear (via MCP) | Live issue state, description, all comments, sub-issues |

## Execution Steps

**Step 1 — Load local memory**

Read these files if they exist (do not error if missing):
```
runs/memory/{issue_id}/plan.md
runs/memory/{issue_id}/context.json
runs/memory/{issue_id}/handoffs/iter-*.md   (all, sorted)
runs/memory/{issue_id}/feedback/*.md        (all, sorted)
runs/memory/{issue_id}/artifacts.json
runs/memory/{issue_id}/decisions.md
```

**Step 2 — Fetch from Linear**

Use `mcp__linear__linear_search_issues_by_identifier` to get the issue.
Also fetch:
- All comments on the issue
- Sub-issues (if any)
- Parent issue (if this is a phase issue linked to a plan)

**Step 3 — Present the brief**

Output a structured summary:

```
## Issue: {identifier} — {title}
**State**: {linear_state}   **Iteration**: {n}   **Status**: {local_status}

### What This Is
{goal from plan or issue description}

### What Was Done
{from handoffs — most recent first}

### Human Feedback
{from feedback/ files — most recent first}
{from Linear comments not yet in local memory}

### Outstanding
{what's left to do, from latest handoff or context.json}

### Artifacts
{from artifacts.json}

### Parent Plan
{if phase issue: summary of parent plan and where this phase fits}
```

## Rules

- Always read local memory BEFORE fetching from Linear — local memory may have context that hasn't been posted to Linear yet
- If `context.json` is missing, this is a first iteration — say so explicitly
- If `handoffs/` is empty, this is a first iteration — do not fabricate prior work
- If `feedback/` has entries, always surface them — they are the human's instructions
- Present the brief before taking any action — the brief IS the output of this skill
- Do not modify any files — this is a read-only skill
