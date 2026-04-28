---
name: pd-plan
description: "Draft an implementation plan for a Linear issue and post it as a comment. Requires a valid PEP. Does not execute."
argument-hint: <linear-issue-id>
allowed-tools: Read, Write, mcp__linear__*
---

# /pd-plan — Draft and Post Plan

Drafts an implementation plan from a PEP and context pack, posts it to Linear, and awaits approval.

## Requires

- PEP must exist and be valid (run `/pd-pep` first if missing)
- Context pack recommended for medium+ tasks (run `/pd-scope` first)

## Workflow

Delegates to `pd-plan-post` skill. Plan is posted as a comment on the Linear issue and stored locally.

See `/pd-start` for the full kickoff flow that combines PEP + scope + plan in one command.
