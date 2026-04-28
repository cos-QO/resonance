# Risks, Weaknesses, and Open Questions

## Main Weaknesses

### Inconsistent issue templates

If teams structure issues differently, retrieval quality will fall quickly.

### Weak project documentation

If project docs are sparse or stale, broad awareness becomes guesswork.

### State drift across tools

If Linear, local memory, and GitHub all contain conflicting summaries, trust breaks down.

### Late human review

If humans skip plan approval and only review at PR time, major mistakes are detected too late.

### Noisy retrieval

If broad awareness pulls too much unrelated context, planning quality drops.

### Unclear ownership

If nobody owns template quality, catalog refresh, and sync policy, the system will degrade over time.

## Risks To Watch

- agents producing too much comment noise in Linear
- duplicated plan/report content across local and remote locations
- hidden dependencies not encoded in templates or docs
- over-automation of decisions that should remain human
- inconsistent closeout reporting making historical analysis weak

## Open Questions

- what exact threshold should trigger full context-pack generation
- which approvals are mandatory for all teams
- what should be written back to Linear versus kept only locally
- who owns the thin context catalog
- how should adjacent teams be chosen during broad awareness
- where should final success metrics live

## Recommended First Decisions

1. define a mandatory issue template schema
2. define what qualifies as a simple task versus a broad-awareness task
3. define the minimum Linear update set for every completed task
4. define whether the thin context catalog exists in repo memory, Linear, or both
