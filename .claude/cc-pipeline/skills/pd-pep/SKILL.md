---
name: pd-pep
description: "Create or validate a PEP (Product Execution Prompt) from a Linear issue. Detects domain, builds the correct tiers, appends only the matching domain variant, and posts to Linear."
argument-hint: <linear-issue-id> [--validate] [--create-tickets]
allowed-tools: Read, Write, mcp__linear__*
---

# pd-pep — Product Execution Prompt Skill

Creates a PEP from a Linear issue or validates an existing one. The PEP is the agent's primary input document — it replaces the raw issue body as the source of truth for planning and execution.

## PEP Structure

| Layer | Always? | Contents |
|---|---|---|
| Metadata | Always | id, status, owner, dates |
| Agent Handoff | Always | Sub-agent table, execution gate, output format |
| Tier 1 — Foundation | Always | What, Why, Done When, Not Doing |
| Tier 2 — Standard | Medium + large | Outcome, Scope, FRs with Verify by, Phasing |
| Tier 3 — Extended | Complex / cross-team | Interaction Model, Linear Export Mapping, Open Questions, Appendix |
| Domain variant | One only | Frontend OR Backend OR Data/Analytics OR Research/Spike |

## Domain Detection

Detect domain from issue labels and title keywords. Append **one variant only**.

| Signal | Domain | Variant |
|---|---|---|
| Label: `frontend`, `ui`, `design`, `connectui` | Frontend | `+ Frontend` block |
| Label: `backend`, `api`, `server`, `infra` | Backend | `+ Backend` block |
| Label: `data`, `analytics`, `schema`, `events` | Data / Analytics | `+ Data / Analytics` block |
| Label: `spike`, `research`, `investigation` | Research / Spike | `+ Research / Spike` block |
| Conflicting signals | Ambiguous | Surface as OQ — do not guess |
| No signal | None | No variant appended |

## Tier Selection

Infer from scope signals in the issue:
- **Quick win**: single file, clearly bounded, no cross-team impact → Tier 1 only
- **Medium**: multi-file, single team, defined scope → Tier 1 + Tier 2
- **Large / complex**: cross-team, product feature, architecture change → All tiers + domain variant

## Workflow — Create mode (no PEP exists)

1. Read the Linear issue: title, description, labels, comments, parent project
2. Detect domain from signals above
3. Classify tier level from scope signals
4. Generate PEP:
   - Fill Tier 1 from issue body (What from title, Why from description, Done When from acceptance criteria or inferred, Not Doing from explicit out-of-scope or inferred)
   - Add Tier 2 if medium/large
   - Add Tier 3 if large/complex
   - Append one domain variant if detected
5. Fill Agent Handoff block: populate sub-agent table based on domain, set gate and output format
6. Flag any fields that cannot be inferred as open questions in the OQ table — do not hallucinate values
7. Post PEP as a Linear document linked to the issue
8. Report: "PEP created — [N] fields need human input" with the OQ list

## Workflow — Validate mode (--validate or PEP exists)

1. Read the existing PEP document from Linear
2. Check Tier 1 completeness: What, Why, Done When (≥1 criterion), Not Doing (≥1 item)
3. Check FRs all have Verify by lines (Tier 2)
4. Check domain variant matches current issue labels
5. Check Agent Handoff block is present and sub-agent table is filled
6. Report: valid / list of missing or invalid fields

## Workflow — Create tickets (--create-tickets)

1. Read Section (Linear Export Mapping) from the filled PEP
2. For each ticket in the mapping:
   - Create the Linear issue with title, description, and acceptance criteria
   - Link to the parent epic
   - Assign to M0 milestone if active
3. Report: list of created ticket identifiers and URLs

## Output

- PEP document at Linear (linked to issue)
- Local copy at `.claude/memory/pd/peps/<issue-id>.md`
- Summary in Claude session

## Memory

Write PEP to `.claude/memory/pd/peps/<issue-id>.md` immediately after creation.
