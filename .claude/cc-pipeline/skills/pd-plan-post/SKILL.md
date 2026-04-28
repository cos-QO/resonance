---
name: pd-plan-post
description: "Draft an implementation plan from the PEP and context pack, post it as a comment on the Linear issue, and store it locally. Does not execute."
argument-hint: <linear-issue-id>
allowed-tools: Read, Write, mcp__linear__*
---

# pd-plan-post — Plan Draft and Post

Drafts a human-readable implementation plan and posts it to Linear for approval.

## Plan format

```markdown
## Implementation Plan — <issue-id>

**Goal:** [1–2 sentences]

**What will change**
- [Bullet — concrete, no jargon]
- [Bullet]

**What will NOT change**
- [Explicit out-of-scope items]

**Phases**
1. [Phase title] — [brief description]
2. [Phase title] — [brief description]
3. [Phase title] — [brief description]

**Files / areas touched**
- [file or component name]

**Verification approach**
- [How each FR will be confirmed — links to Verify by lines in PEP]

**Open questions / assumptions**
- [Resolved OQs stated as facts]
- [Unresolved OQs stated as assumptions with risk level]
```

## Workflow

1. Read PEP from `.claude/memory/pd/peps/<issue-id>.md`
2. Read context pack from `.claude/memory/pd/context/<issue-id>-pack.md` (if exists)
3. Draft plan in the format above
4. Post plan as a comment on the Linear issue via `mcp__linear__create_comment`
5. Store full plan locally at `.claude/memory/pd/plans/<issue-id>.md`
6. Record plan comment ID in `.claude/memory/pd/plans/<issue-id>-meta.json`

## Output

- Plan comment on Linear issue
- `.claude/memory/pd/plans/<issue-id>.md` (full plan)
- `.claude/memory/pd/plans/<issue-id>-meta.json` (comment ID, timestamp, status)
