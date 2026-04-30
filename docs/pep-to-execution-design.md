# PEP to Execution — Design Document

> **⚠ Superseded.** This document describes an earlier design. The current implementation is documented in:
> - `docs/how-it-works.md` — full technical reference
> - `docs/operator-runbook.md` — day-to-day operation
> - `docs/pipeline-status.md` — current component status and what was built per session
>
> Key terminology differences from this doc: what this doc calls "Plan issues" the current system calls "Block issues"; the intermediate "Core Plan" layer did not exist in this design.

How a Product Execution Prompt becomes running work in Resonance.

---

## Overview

The PEP (Product Execution Prompt) is the single source of truth for any piece of work. It lives in Linear as a project-scoped document and travels through four stages before any code is written:

```
[PEP] Project created in Linear
       ↓  human writes and reviews PEP
       ↓  human moves PEP issue to "Plan Approved"
Resonance reads PEP → creates Plan issues
       ↓  human reviews Plans → moves to "Plan Approved"
Resonance executes Plans → creates Block issues
       ↓  human reviews via comments / Human Review state
Resonance executes Blocks → tasks become checkboxes inside each Block
       ↓  human approves → Done
```

---

## Stage 1 — PEP Creation

### Project naming

Every PEP lives in a Linear project named:

```
[PEP] <title>
```

Examples: `[PEP] User Authentication`, `[PEP] Checkout Redesign`, `[PEP] Data Pipeline v2`

The `[PEP]` prefix signals to Resonance (and humans) that this project is a source-of-truth document, not an execution project.

### The PEP issue

Inside the project, there is **one PEP issue**. This issue is what Resonance watches. It:

- Has the label `pep`
- Contains the full PEP document as its description (see PEP template structure below)
- Starts in `Todo` status
- Moves to `Plan Approved` when the human is satisfied

### PEP template structure

```markdown
# PEP: <title>

id:      pep-<slug>
status:  draft | in-review | approved
owner:   <name>
created: YYYY-MM-DD

---

## Overview
[What this project is and why it matters — 2–4 sentences]

## Goal
[The single measurable outcome that defines success]

## Done When
- [ ] [Top-level acceptance criterion]
- [ ] [Top-level acceptance criterion]

## Not Doing
- [Explicit out of scope]

---

## Plans

> Each Plan becomes a separate Linear issue.
> Plans can be executed in sequence or in parallel (set dependency if sequential).

### Plan 1 — <name>
**Goal:** [What this plan delivers]
**Depends on:** none | Plan 2 | Plan 3
**Blocks:**
  - B1: [Block title] — [what it implements]
  - B2: [Block title] — [what it implements, depends on B1 if sequential]

### Plan 2 — <name>
**Goal:** [What this plan delivers]
**Depends on:** Plan 1
**Blocks:**
  - B1: [Block title]
  - B2: [Block title]

---

## Resources

| Resource | Link | Notes |
|---|---|---|
| Figma | [link] | |
| GitHub repo | [link] | |
| API docs | [link] | |
| Prior art | [link] | |

---

## Open Questions

| # | Question | Owner | Status |
|---|---|---|---|
| OQ-1 | | | Open |
```

### How the PEP is created

Two paths:

**Option A — Manual**: Human writes the PEP directly in the Linear issue description following the template.

**Option B — Skill-assisted**: Human creates the issue with a rough brief, then runs `/pd-pep <issue-id>` in a Claude Code session. The skill reads the brief, infers domain and scope, fills in the structured PEP, and posts it back to Linear. Human reviews and edits.

---

## Stage 2 — Resonance Reads the PEP

### Trigger

When the human moves the PEP issue to `Plan Approved`, Resonance picks it up on the next poll (within 15 seconds).

The `pep` label routes it to the **PEP Reader Agent** (a new task type, distinct from the existing `plan` task type).

### What the PEP Reader Agent does

1. Reads the PEP issue description
2. Reads all comments on the PEP issue (for human context, clarifications, additions posted after initial writing)
3. Reads the project's resource links (Figma, GitHub, docs)
4. For each Plan defined in the PEP `## Plans` section:
   - Creates one Linear issue with full detail (see Plan issue format below)
   - Sets it to `Todo` — **not Plan Approved** (human must review first)
   - Links it as a child of the PEP issue
   - Sets `blockedBy` relations if the plan depends on another
5. Posts a summary comment on the PEP issue listing all created plans
6. Marks the PEP issue `Done` (its job is complete — the plans are now the unit of work)
7. Emits `AGENT_SIGNAL: {"type": "pep_decomposed", "plans": [...]}`

### Plan issue format

Each Plan issue created by the PEP Reader Agent follows this structure:

```markdown
## Goal
[What this plan delivers — from the PEP Plans section]

## Blocks

### B1 — <block title>
**What:** [What this block implements]
**Tasks:**
- [ ] [Specific task]
- [ ] [Specific task]
**Acceptance criteria:**
- [ ] [Verifiable condition]
**Depends on:** none

### B2 — <block title>
**What:** [What this block implements]
**Tasks:**
- [ ] [Specific task]
**Acceptance criteria:**
- [ ] [Verifiable condition]
**Depends on:** B1

## Technical context
[Relevant codebase context, patterns to follow, files to touch — sourced from resources in PEP]

## Resources
[Filtered list of relevant PEP resources for this specific plan]

## Dependencies
[Other plan IDs that must be Done before this plan can start, or "None"]

## Open questions inherited from PEP
[Any unresolved OQs from the PEP that affect this plan]
```

---

## Stage 3 — Human Reviews Plans

Plans are created in `Todo`. The human:

1. Reviews each Plan issue in Linear
2. Edits titles, descriptions, block definitions as needed
3. Moves each approved plan to `Plan Approved`

Resonance ignores plans in `Todo`. Only `Plan Approved` issues are picked up.

---

## Stage 4 — Resonance Executes Plans

### Dependency enforcement

Before starting any plan, Resonance checks its `blockedBy` relations. If any blocker is not in `Done` or `Cancelled`, the plan is skipped for this tick. Resonance posts a comment:

```
⏸ Waiting for [ISSUE-ID] to complete before this plan can start.
Will pick up automatically when the dependency is resolved.
```

When the blocker is Done and the plan is polled again, Resonance starts it and posts:

```
▶️ [ISSUE-ID] is now complete. Starting this plan.
```

### Block execution

Each Plan issue is executed by the Execution Agent (same as today). The agent:

1. Reads the Plan issue description
2. Implements each Block in sequence (or in parallel if no dependency noted between them)
3. For each Block, creates a **Block issue** as a child of the Plan issue
4. Updates the Plan issue description as blocks complete (checks off tasks)
5. Signals `ready_for_review` when all blocks are done

Block issues are the atomic unit of git work — each gets its own branch and PR.

---

## Naming Convention

Linear auto-assigns numeric identifiers (e.g. `RND-22`). We can't control these. The naming convention is therefore **title-based** using a bracketed prefix:

| Level | Title format | Example |
|---|---|---|
| PEP issue | `[PEP] <title>` | `[PEP] User Authentication` |
| Plan issue | `[<PEP-ID>-P<N>] <title>` | `[RND-22-P1] Auth Backend` |
| Block issue | `[<PEP-ID>-P<N>-B<N>] <title>` | `[RND-22-P1-B1] User model + migration` |

Where `RND-22` is the Linear identifier of the **PEP issue** (not the project).

This convention means:
- Any agent reading an issue title immediately knows its place in the hierarchy
- Searching Linear for `RND-22-P1` returns all blocks of that plan
- Searching for `RND-22` returns the entire work tree for that PEP
- The PM agent can reconstruct dependency graphs from titles alone

### Example tree

```
RND-22           [PEP] User Authentication
  RND-30         [RND-22-P1] Auth Backend API
    RND-31         [RND-22-P1-B1] User model + migration
    RND-32         [RND-22-P1-B2] JWT token service
    RND-33         [RND-22-P1-B3] Auth endpoints (login, register, refresh)
  RND-34         [RND-22-P2] Auth Frontend (depends on P1)
    RND-35         [RND-22-P2-B1] Auth context + token storage
    RND-36         [RND-22-P2-B2] Login + registration pages
    RND-37         [RND-22-P2-B3] Protected route wrapper
```

---

## Comment-Based Communication

### Why it matters

Comments are how humans and Resonance talk to each other without changing issue state. Three use cases:

1. **Human → Agent**: add context, answer questions, send feedback mid-execution
2. **Agent → Human**: status updates, decisions made, things waiting on human input
3. **Agent → itself**: self-notes posted as comments that survive between iterations (since comments persist in Linear while local memory can be rebuilt from them)

### Existing mechanism (issue-level)

The `Agent Feedback Needed` state already triggers comment reading. When an agent emits `human_input_needed`, Resonance:
- Posts the agent's question as a comment
- Moves issue to `Agent Feedback Needed`
- On next poll: reads new comments since last check, injects them as `prior_feedback` into the next iteration prompt

This works today. No changes needed for issue-level conversation.

### Extended: PEP-level and Plan-level comments

For PEP and Plan issues, the same comment mechanism applies with two additions:

**1. Kickoff detection on PEP issue**

When the PEP issue is in `Plan Approved`, the PEP Reader Agent already reads all existing comments before creating plans. This means any context a human posted as a comment ("focus on mobile first", "skip OAuth for now", "the Figma link in the description is outdated — use this one instead") is incorporated into the plan decomposition.

**2. Block-level question mid-execution**

If the Execution Agent working on a Block issue hits a question, it emits `human_input_needed`. The block issue goes to `Agent Feedback Needed`. The human answers in a comment. Resonance reads it and resumes. This is identical to today's mechanism, but now it applies at the Block level rather than the Plan level.

### PM self-commentary pattern

The PM agent (PEP Reader Agent and Planning Agent) is instructed to post structured comments at key moments for its own future reference. These are prefixed `[PM]` so they're distinguishable from agent status updates:

```
[PM] Plans created from PEP RND-22. Sequencing: P1 → P2 (P2 blocked on P1).
Rationale: P2 frontend depends on P1 API contracts being stable.
P3 (analytics) can run in parallel with P2 once P1 is done.
```

```
[PM] RND-30 (P1) is now Done. Unblocking RND-34 (P2) — starting now.
```

```
[PM] Holding RND-34 (P2). RND-30 (P1) still in Human Review.
Will resume when P1 reaches Done.
```

This gives any human (or future agent iteration) a readable audit trail of why things were sequenced the way they were.

---

## New Task Type: `pep`

Add to `WORKFLOW.md` task_types:

```yaml
pep:
  detection:
    labels: [pep]
  worker: claude-opus       # needs strongest reasoning for decomposition
  mcp:
    - linear                # creates issues, reads project, posts comments
  description: |
    Reads a PEP document from a Linear issue.
    Creates Plan issues with full block/task breakdowns.
    Sets dependencies between plans. Posts summary comment on PEP issue.
    Marks PEP issue Done when all plans are created.
```

---

## New Linear Labels Required

| Label | Color | Purpose |
|---|---|---|
| `pep` | `#7C3AED` (purple) | Marks the PEP issue — triggers PEP Reader Agent |
| `plan` | existing | Already exists — marks plan decomposition issues |

The `pep` label is applied only to the one PEP issue per project. All plan and block issues use existing labels (`frontend`, `backend`, `design`, `bug`).

---

## New Linear Workflow States Required

No new states. The existing state model covers all transitions:

```
Todo → Plan Approved → In Progress → Human Review → Done
                              ↕
                    Agent Feedback Needed
```

---

## Full Flow Diagram

```
Human writes PEP in Linear project "[PEP] Title"
    ↓
Human moves PEP issue (label: pep) → Plan Approved
    ↓
Resonance polls → classifies as task_type: pep
    ↓
PEP Reader Agent (claude-opus) runs in worktree
  reads PEP description + all comments + resource links
  creates Plan issues:
    [RND-22-P1] → Todo, child of RND-22, blockedBy: none
    [RND-22-P2] → Todo, child of RND-22, blockedBy: [RND-30 (P1)]
  posts summary comment on RND-22
  marks RND-22 → Done
  emits AGENT_SIGNAL: pep_decomposed
    ↓
Human reviews Plan issues in Linear
Human moves Plan issues → Plan Approved (one by one, own pace)
    ↓
Resonance polls → picks up Plan Approved issues
  checks blockedBy: if any blocker not Done → skip, post [PM] comment
  if unblocked → start run
    ↓
Execution Agent runs (e.g. claude-sonnet for backend_feature)
  reads Plan issue description (blocks, tasks, context, resources)
  implements Block by block
  creates Block issues as child issues:
    [RND-22-P1-B1] → created, worked on, PR opened
    [RND-22-P1-B2] → created after B1 if sequential
  checks off tasks in Plan issue description as completed
  posts structured review comment
  emits AGENT_SIGNAL: ready_for_review
    ↓
Resonance: Plan issue → Human Review
Human reviews PR(s)
    ↓
Human approves → Plan issue → Done
Resonance detects P1 Done → posts [PM] unblock comment on P2 → P2 can now start
    ↓
(repeat for remaining Plans)
```

---

## Implementation Status

### Completed in code

| File | Change |
|---|---|
| `WORKFLOW.md` | `pep` task type added (claude-opus, linear MCP) |
| `orchestrator/linear_client.py` | `pep` label added to `REQUIRED_LABELS`; `inverseRelations` added to `get_issue()`; `create_issue_relation()` method added |
| `orchestrator/classifier.py` | `pep` checked before `plan` — routes `pep`-labeled issues to PEP Reader Agent |
| `orchestrator/planner.py` | `is_pep_issue()`, `build_pep_reader_prompt()` added; `is_plan_issue()` updated to exclude pep |
| `orchestrator/poller.py` | Dependency check in `_start_run()`; `_check_active_blockers()`; `_handle_blocked()` with `[PM]` comment; `_finish_pep_decomposed()` with Linear relation wiring; `pep_decomposed` signal handled |
| `orchestrator/memory.py` | `write_plans()` / `get_plans()` added for PEP issue plan metadata |
| `docs/pep-template.md` | `## Plans` section added; naming convention note added |

### Linear setup required (one-time, per team)

Run `resonance fix` or `resonance setup` — the `pep` label is now in `REQUIRED_LABELS` and will be created automatically.

- `pep` label (purple `#7C3AED`) — created by `resonance fix`
- Project naming convention `[PEP] <title>` — human convention, no automation needed

---

## Open Questions

| # | Question | Decision needed |
|---|---|---|
| OQ-1 | Should Block issues be created by the PEP Reader Agent or by the Execution Agent mid-run? | PEP Reader: creates Plan issues. Execution Agent: creates Block issues during run. |
| OQ-2 | Tasks within a Block: separate issues or checklists inside the Block issue? | Checklists for now (lower overhead). Promote to issues if a task needs its own PR. |
| OQ-3 | Can a PEP have only 1 Plan? | Yes. If the work is small enough, one Plan with N Blocks is valid. |
| OQ-4 | What happens if the human edits the PEP after plans are created? | Out of scope for V1. Human edits plan issues directly. A `/pd-pep --sync` command is a future option. |
| OQ-5 | Should the Execution Agent read the original PEP as additional context? | Yes — the Plan issue description should include a link to the PEP issue ID so the agent can fetch it via MCP if needed. |
