---
name: pd-status
description: "Show all active plans and their Linear approval state. Lists plans in .claude/memory/pd/plans/ and checks each issue's current status in Linear."
allowed-tools: Read, Glob, mcp__linear__*
---

# /pd-status — Active Plans

Lists all plans in `.claude/memory/pd/plans/` and checks their current Linear status.

## Output

```
Active plans:

  SPH-93  pep-lists-reskin
    Status:     In Progress
    Plan:       Approved ✓
    PR:         #47 (open)
    Last sync:  2026-04-24

No blocked plans.
```

Shows: issue identifier, plan file, Linear status, plan approval state, linked PR if any.
