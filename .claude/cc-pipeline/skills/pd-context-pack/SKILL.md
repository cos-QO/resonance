---
name: pd-context-pack
description: "Synthesise sub-agent outputs into a structured context pack and impact map. Written to local memory. Referenced by pd-plan-post when drafting the plan."
argument-hint: <linear-issue-id>
allowed-tools: Read, Write
---

# pd-context-pack — Context Pack Synthesis

Reads sub-agent outputs from `.claude/memory/pd/context/` and synthesises them into a single structured context pack for the planning agent.

## Context Pack Structure

```markdown
# Context Pack — <issue-id>

## Summary
[2–3 sentences: what the issue is, what's affected, key constraint]

## Codebase findings
- Files to touch: [list]
- Current state: [token/component usage summary]
- Gaps identified: [what's missing or non-compliant]

## Linear context
- Related work in flight: [issues]
- Known decisions: [decisions already made that affect this]
- Blockers: [anything blocking]

## Figma / design context
- Component spec: [name + Figma link]
- Token map: [relevant tokens]
- Designer notes: [any annotations]

## Impact map
- What changes: [files, components, tokens]
- What must NOT change: [data layer, API contracts, other pages]
- Downstream risk: [what breaks if this is done wrong]

## Resolved open questions
- OQ-1: [question] → [answer from sub-agent]
- OQ-2: [question] → [answer from sub-agent]

## Remaining open questions (surface in plan)
- OQ-3: [question] — [which human / sub-agent resolves]
```

## Workflow

1. Read all context files for this issue from `.claude/memory/pd/context/`
2. Synthesise into the structure above — do not just concatenate, reason across sources
3. Identify conflicts between sources (e.g. Linear says X, codebase shows Y) and flag them
4. Write context pack to `.claude/memory/pd/context/<issue-id>-pack.md`
5. Return the pack path to the calling skill

## Output

`.claude/memory/pd/context/<issue-id>-pack.md`
