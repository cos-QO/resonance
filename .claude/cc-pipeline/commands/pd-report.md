---
name: pd-report
description: "Post an execution report to Linear on task completion. Summarises what was done, links the PR, and lists any follow-up issues."
argument-hint: <linear-issue-id>
allowed-tools: Read, Write, Bash, mcp__linear__*
---

# /pd-report — Post Execution Report

Generates and posts a structured execution report to Linear. Run this after the GitHub PR is merged.

## Report format

```
## What was done
[Bullet list — concrete, no jargon]

## Verification
- Tests: [pass/fail + CI link]
- PR: [link]

## Follow-up issues
- [ENG-XXX] — [title]

## What stayed local
- [List of local memory files if human wants more detail]
```

## Workflow

Delegates to `pd-report-post` skill:
1. Read the approved plan from `.claude/memory/pd/plans/<issue-id>.md`
2. Read git log and PR details
3. Generate report comparing plan vs actual
4. Post as comment on the Linear issue
5. Update issue status to "Done" or "Complete"
