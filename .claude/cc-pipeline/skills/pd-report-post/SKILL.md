---
name: pd-report-post
description: "Generate and post an execution report to Linear on task completion. Compares approved plan vs actual work. Links PR."
argument-hint: <linear-issue-id>
allowed-tools: Read, Write, Bash, mcp__linear__*
---

# pd-report-post — Execution Report

Generates a structured execution report comparing what was planned vs what was done, and posts it to Linear.

## Report format

```markdown
## Execution Report — <issue-id>

**What was done**
- [Bullet — concrete actions, file names where relevant]

**Verification**
- Tests: [pass / fail] — [CI link if available]
- PR: [GitHub PR link]
- Preview: [preview link if available]

**Plan vs actual**
- [Any deviations from the approved plan and why]

**Follow-up issues**
- [Issue identifier] — [title]

**What stayed local** (available on request)
- `.claude/memory/pd/context/<issue-id>-pack.md`
- `.claude/memory/pd/plans/<issue-id>.md`
```

## Workflow

1. Read approved plan from `.claude/memory/pd/plans/<issue-id>.md`
2. Read git log since plan was approved (`git log --oneline`)
3. Fetch PR details (number, URL, merge status) from GitHub via `gh pr list`
4. Generate report comparing plan vs actual
5. Post as comment on Linear issue via `mcp__linear__create_comment`
6. Update issue status to Done / Complete via `mcp__linear__update_issue`

## Output

- Execution report comment on Linear issue
- Issue status updated to Done
