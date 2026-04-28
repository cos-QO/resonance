---
name: pd-scope
description: "Run sub-agent context collection for a Linear issue. Spawns parallel agents for codebase, Linear, and Figma. Saves context pack locally."
argument-hint: <linear-issue-id>
allowed-tools: Read, Write, Agent, mcp__linear__*, mcp__figma__*
---

# /pd-scope — Context Collection

Runs the context collection phase only. Useful for large issues where you want to review the context pack before drafting a plan.

## Workflow

Delegates to `pd-linear-scope` then `pd-context-pack` skills.

Outputs:
- Context pack at `.claude/memory/pd/context/<issue-id>.md`
- Summary in Claude: key findings, open questions, and recommended plan approach
