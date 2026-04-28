---
name: pd-linear-scope
description: "Spawn parallel sub-agents to collect context from codebase, Linear, and Figma before planning. Each sub-agent targets one source. Results written to local memory."
argument-hint: <linear-issue-id>
allowed-tools: Read, Write, Agent, mcp__linear__*, mcp__figma__*
---

# pd-linear-scope — Parallel Context Collection

Spawns sub-agents in parallel to collect cross-source context before planning. Mirrors the mini-troubleshooter pattern: cheap parallel collection, expensive synthesis once.

## Sub-agents

Spawn all relevant sub-agents simultaneously in a single message.

### Codebase agent
**Model:** haiku
**Mission:** Locate the files relevant to this issue. Map current implementation — components, tokens, imports, test coverage. Identify what will need to change.
**Returns:** File list, current usage summary, gaps vs target state.
**Skip if:** Issue has no codebase changes (pure research/spike).

### Linear agent
**Model:** haiku
**Mission:** Pull related Linear context — parent project, adjacent issues (last 30 days, same systems), linked documents, open blockers, comments with decisions.
**Returns:** Relevant issue summaries, known decisions, blockers, open questions already on record.
**Always run.**

### Figma agent
**Model:** haiku
**Mission:** Locate the relevant design system component specs and token set in Figma.
**Returns:** Component spec summary, token map, Figma file reference, any designer annotations.
**Skip if:** Issue has no frontend/design component.

## Workflow

1. Read the PEP for this issue (`.claude/memory/pd/peps/<issue-id>.md`)
2. Determine which sub-agents to spawn based on domain variant in PEP
3. Spawn applicable sub-agents in parallel (single message, multiple Agent calls)
4. Wait for all to complete
5. Write each result to `.claude/memory/pd/context/<issue-id>-<source>.md`
6. Call `pd-context-pack` to synthesize results

## Failure handling

If a sub-agent fails or returns empty:
- Note the failure in the context pack as an explicit gap
- Do not block — proceed with available context
- Surface the gap as an OQ in the plan

## Output

Raw sub-agent results written to:
- `.claude/memory/pd/context/<issue-id>-codebase.md`
- `.claude/memory/pd/context/<issue-id>-linear.md`
- `.claude/memory/pd/context/<issue-id>-figma.md`
