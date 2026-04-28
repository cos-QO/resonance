---
name: pd-github-pr
description: "Open a GitHub PR linked to the Linear issue. PR description generated from the execution plan and git diff. Assigns product designer or reviewer."
argument-hint: <linear-issue-id> [--reviewer <github-username>]
allowed-tools: Bash, Read, mcp__linear__*
---

# pd-github-pr — GitHub PR Creation

Opens a GitHub PR with a description generated from the implementation plan and git diff. Links to the Linear issue.

## PR description format

```markdown
## What
[What this PR does — from plan goal]

## Why
[Why — from PEP Why field]

## Changes
[Bullet list of files changed and what changed]

## Verification
- [ ] FR-1: [requirement] — [Verify by approach]
- [ ] FR-2: [requirement] — [Verify by approach]
- [ ] Manual: Test on mobile (375px) and desktop (1280px)

## Linear issue
[SPH-XX link]

## Preview
[Preview URL if available]
```

## Workflow

1. Read plan from `.claude/memory/pd/plans/<issue-id>.md`
2. Read PEP FRs for verification checklist
3. Get Linear issue URL via `mcp__linear__get_issue`
4. Run `gh pr create` with generated description
5. If `--reviewer` provided: assign reviewer via `gh pr edit --add-reviewer`
6. Post PR link as comment on Linear issue via `mcp__linear__create_comment`

## Requirements

- `gh` CLI must be authenticated (`gh auth status`)
- Must be on a non-main branch with commits
- Plan must be approved before calling this skill (enforced by `pd-guardrail`)
