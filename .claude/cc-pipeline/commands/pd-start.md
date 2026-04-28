---
name: pd-start
description: "Full pipeline kickoff: reads the PEP from Linear, runs sub-agent context collection, drafts an implementation plan, posts it to Linear, and waits for human approval before execution."
argument-hint: <linear-issue-id>
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, mcp__linear__*, mcp__figma__*
---

# /pd-start — Pipeline Kickoff

Full delivery pipeline start. Takes a Linear issue, produces an approved plan ready for execution.

## Workflow

### Step 1 — Load and validate PEP

Run the `pd-pep` skill on the issue:
- If a PEP exists: validate it — all Tier 1 fields filled, FRs have Verify by lines
- If no PEP: generate one from the issue body using the PEP template, post to Linear
- Surface any missing required fields before continuing

If PEP is invalid or incomplete, stop and report what's missing. Do not proceed to context collection with a broken PEP.

### Step 2 — Detect classification

Read the PEP's classification (quick win / medium / large / complex):
- **Quick win**: skip sub-agents, proceed directly to Step 4
- **Medium / large / complex**: run Step 3 first

### Step 3 — Context collection (medium+ only)

Run the `pd-linear-scope` skill: spawn parallel sub-agents for codebase, Linear, and Figma.

Wait for all sub-agents to complete. If any sub-agent fails, note the failure as an assumption in the plan rather than blocking.

### Step 4 — Draft plan

Run the `pd-context-pack` skill to synthesize sub-agent outputs into a context pack.

Draft an implementation plan:
- Goal (1–2 sentences)
- What will change (bullet list — no jargon)
- What will NOT change (explicit out-of-scope)
- Phases (3–7 steps)
- Files / areas touched
- How each FR will be verified
- Open questions resolved (or noted as assumptions)

### Step 5 — Post plan to Linear

Run the `pd-plan-post` skill:
- Post plan as a comment on the Linear issue
- Store full plan locally at `.claude/memory/pd/plans/<issue-id>.md`

Display the plan in the Claude session with an approval prompt:

```
────────────────────────────────────────
  PLAN READY — AWAITING APPROVAL
────────────────────────────────────────
[plan contents]

Set the issue status to "Plan Approved" in Linear to proceed.
Or reply here with changes to revise.
────────────────────────────────────────
```

### Step 6 — Wait for approval

Poll Linear via MCP every 30 seconds (max 10 polls) for status = "Plan Approved".

If approved: output "Plan approved — ready to execute. Run /pd-report <issue> when done."
If not approved after polling: output "Waiting for approval. Resume this session after approving in Linear."

**Do not proceed to execution.** Execution is handled separately — the guardrail rule enforces this.
