"""
Planning Agent orchestration.

Two agent types live here:

PEP Reader Agent — triggered by the 'pep' label:
  Reads a PEP document (Product Execution Prompt) and decomposes it into
  Plan issues in Linear. Each Plan contains Blocks and tasks. The agent
  creates the Plan issues in Todo state (human reviews before approving),
  posts a summary comment on the PEP issue, then signals pep_decomposed
  with the plan list including blocking relationships.

Planning Agent — triggered by the 'plan' label:
  Reads a plan document and decomposes it into execution-ready phase issues,
  moves them to Plan Approved, then signals plan_decomposed.
"""
import logging
from pathlib import Path
from typing import Optional

from .config import Config

logger = logging.getLogger(__name__)

PEP_LABEL = "plan"   # kept for backward compat — classifier routes by task type, not this constant
PLAN_LABEL = "plan"


def is_pep_issue(issue: dict) -> bool:
    label_names = {lbl["name"].lower() for lbl in issue.get("labels", {}).get("nodes", [])}
    return "pep" in label_names


def is_plan_issue(issue: dict) -> bool:
    label_names = {lbl["name"].lower() for lbl in issue.get("labels", {}).get("nodes", [])}
    return PLAN_LABEL in label_names and "pep" not in label_names


def build_planning_prompt(issue: dict, config: Config) -> str:
    issue_id  = issue.get("identifier", issue["id"])
    title     = issue.get("title", "")
    description = (issue.get("description", "") or "").strip()

    eligibility = config.eligibility_state
    team_id     = config.linear_team_id
    project_id  = config.linear_project_id or ""

    # Build label reference table from WORKFLOW.md
    task_types = config.workflow.get("task_types", {})
    label_rows: list[str] = []
    for tt_name, tt_cfg in task_types.items():
        if tt_name == "plan":
            continue
        detection = tt_cfg.get("detection", {})
        requires  = detection.get("labels", [])
        excludes  = detection.get("excludes", [])
        skills    = tt_cfg.get("skills", [])
        row = f"  {tt_name:<20} labels={requires}"
        if excludes:
            row += f"  excludes={excludes}"
        row += f"  skills={skills[:3]}"
        label_rows.append(row)

    # QO skills always injected
    qo_skills_note = (
        "Always include these QO skills in every phase issue's skills section:\n"
        "  connectui-dev (design system), verify (quality gates), qo-pr (PR creation)"
    )

    return f"""\
# Planning Agent — {issue_id}: {title}

You are the Resonance Planning Agent. Your job is to decompose this approved plan
into Linear phase issues so the orchestrator can execute them one by one.

## The Plan

{description if description else "_No description provided._"}

## Your Task

**Step 1 — Analyse the plan.**
Read every phase and step. Identify the natural phases — each one should be a
cohesive unit of work (3–8 hours) that produces a verifiable output.

**Step 2 — For each phase, determine:**
- A clear title:  `Phase N: [descriptive name]`
- The correct task-type label (from Available Labels below)
- Acceptance criteria (bullet list of testable, observable conditions)
- Which phases it depends on (must complete before this one starts)

**Step 3 — Create a Linear issue for each phase** using `mcp__linear__linear_create_issue`.
Call it once per phase with exactly these fields:

| Field | Value |
|---|---|
| teamId | `{team_id}` |
| projectId | `{project_id}` |
| parentId | `{issue['id']}` |
| title | `Phase N: [name]` |
| stateId | leave unset (defaults to Todo) |
| labelIds | one label id from Available Labels |
| description | see PEP Template below |

After each call, record the returned `id` (UUID) and `identifier` (e.g. RND-25) — you need them for Steps 5 and 6.

**Step 4 — Write plan.md to local memory.**
Create the file `runs/memory/{issue_id}/plan.md` with a structured summary:
  - Overall goal
  - Phase list with titles, identifiers (after creation), and dependencies

**Step 5 — Post a "Plan ready" comment** on the parent issue.
Call `mcp__linear__linear_create_comment` with `issueId: "{issue['id']}"` and this body:

```
📋 Plan ready — [N] phases created

Phase 1: [title] → [identifier]
Phase 2: [title] → [identifier]
...

Each phase will be picked up automatically by the orchestrator.
Review the phase issues in Linear before they execute.
```

**Step 6 — Move each phase issue to Plan Approved.**
For each phase issue UUID from Step 3, call `mcp__linear__linear_bulk_update_issues` with:
- `ids`: list of all phase issue UUIDs
- `stateId`: the state ID for `{eligibility}`

To get the state ID for `{eligibility}`, first call `mcp__linear__linear_search_issues_by_identifier`
on the parent issue `{issue_id}` and read the `team.states` from the result, or look up via any issue
in the same team. The state named `{eligibility}` is what you need.
This kicks off orchestration automatically.

## Available Labels

{chr(10).join(label_rows)}

## QO Skills (always required)

{qo_skills_note}

## PEP Issue Description Template

Use this template for every phase issue description:

```markdown
## Goal
[What this phase achieves — one clear paragraph]

## Steps
1. [Step]
2. [Step]

## Acceptance Criteria
- [ ] [Testable, observable condition]
- [ ] [Testable, observable condition]

## Skills
[List: connectui-dev, verify, qo-pr + task-specific skills]

## Dependencies
[Phase identifiers that must be Done before this starts, or "None"]

## Parent Plan
[{issue_id}] {title}
```

## Signal Protocol

After all phase issues are created and moved to Plan Approved, output EXACTLY:

`AGENT_SIGNAL: {{"type": "plan_decomposed", "plan_id": "{issue_id}", "phases": [{{"id": "<linear-uuid>", "identifier": "<identifier>", "title": "<title>"}}]}}`

Replace the placeholders with the actual values returned by Linear when you created each issue.
Do not end this session without emitting this signal.
"""


def build_pep_reader_prompt(issue: dict, config: Config) -> str:
    """Prompt for the PEP Reader Agent.

    The agent reads the PEP issue description + comments, creates Plan issues in
    Linear (Todo state, for human review), posts a summary comment, then signals
    pep_decomposed with plan IDs and blocking relationships so the orchestrator
    can set Linear relations.
    """
    issue_id    = issue.get("identifier", issue["id"])
    issue_uuid  = issue["id"]
    title       = issue.get("title", "")
    description = (issue.get("description", "") or "").strip()
    team_id     = config.linear_team_id
    project_id  = config.linear_project_id or ""

    # Build label reference from WORKFLOW.md so the agent assigns correct labels
    task_types = config.workflow.get("task_types", {})
    label_rows: list[str] = []
    for tt_name, tt_cfg in task_types.items():
        if tt_name in ("pep", "plan"):
            continue
        detection = tt_cfg.get("detection", {})
        requires  = detection.get("labels", [])
        excludes  = detection.get("excludes", [])
        row = f"  {tt_name:<22} requires={requires}"
        if excludes:
            row += f"  excludes={excludes}"
        label_rows.append(row)

    return f"""\
# PEP Reader Agent — {issue_id}: {title}

You are the Resonance PEP Reader Agent. Your job is to read this Product Execution
Prompt (PEP), understand the full scope of work, and create a structured set of
Plan issues in Linear that Resonance agents can execute one by one.

You are the PM — not an executor. Do not write code. Think like a senior engineering
lead decomposing a project before handing it to a team.

---

## The PEP

{description if description else "_No description provided — read comments on this issue for context._"}

---

## Step 1 — Read all context

1. Read the PEP description above in full.
2. Fetch all comments on issue `{issue_id}` using `mcp__linear__linear_search_issues_by_identifier`.
   Comments contain human clarifications added after the initial PEP was written.
   Incorporate any context found there into your planning.
3. If the PEP references external resources (Figma links, GitHub repos, API docs),
   note them — you will include them in relevant Plan issue descriptions.

---

## Step 2 — Understand the goal and identify Plans

Read the PEP's `## Plans` section. Each Plan entry describes a cohesive deliverable.

If the PEP has no `## Plans` section, infer Plans from the structure:
- Each major Tier or Phase in the PEP = one Plan
- If the work is small enough, one Plan with multiple Blocks is correct

**Plan rules:**
- 1–5 Plans per PEP (more = the PEP should be split into separate PEPs)
- Each Plan delivers something testable and reviewable on its own
- Plans that depend on other Plans must say so explicitly
- Plans with no dependencies can run in parallel

---

## Step 3 — Design the Blocks inside each Plan

For each Plan, identify its Blocks:

**Block rules (CRITICAL):**
- One Block = one agent session = one PR
- 3–8 hours of focused work
- Single concern: one endpoint, one component, one migration — not "build the API"
- Each Block must have ≥2 measurable acceptance criteria
- Blocks within a Plan can be sequential (B2 needs B1) or parallel (no dependency)
- Self-contained: every Block description must include all context an agent needs

**Good Block examples:**
  ✓ User model + migration (email, password_hash, created_at, soft delete)
  ✓ POST /auth/login — credential check, JWT response, refresh token
  ✗ Build the whole authentication system (too large)
  ✗ Fix button colour (too small)

---

## Step 4 — Create Plan issues in Linear

For each Plan, call `mcp__linear__linear_create_issue` once with these exact fields:

| Field | Value |
|---|---|
| teamId | `{team_id}` |
| projectId | `{project_id}` |
| parentId | `{issue_uuid}` |
| title | `[{issue_id}-P<N>] <Plan title>` (e.g. `[{issue_id}-P1] Auth Backend API`) |
| stateId | leave unset — defaults to Todo (humans review before approving) |
| labelIds | one label from Available Labels below |
| description | use the Plan Issue Template below |

Record the returned `id` (UUID) and `identifier` (e.g. RND-30) for each plan — needed for Steps 5 and 6.

### Naming convention

```
PEP issue:   {issue_id}         (this issue)
Plan 1:      [{issue_id}-P1] Title
Plan 2:      [{issue_id}-P2] Title
Block 1/P1:  [{issue_id}-P1-B1] Title  ← created later by the Execution Agent
Block 2/P1:  [{issue_id}-P1-B2] Title
```

Agents use these prefixes to understand hierarchy at a glance. Always include them.

### Plan Issue Template

```markdown
## Goal
[One clear paragraph: what this plan delivers and why it matters]

## Blocks

### B1 — <block title>
**What:** [What this block implements]
**Label:** [frontend | backend | design | bug]
**Tasks:**
- [ ] [Specific implementation task]
- [ ] [Specific implementation task]
**Acceptance criteria:**
- [ ] [Verifiable, observable condition]
- [ ] [Verifiable, observable condition]
**Depends on:** none

### B2 — <block title>
**What:** [What this block implements]
**Label:** [frontend | backend | design | bug]
**Tasks:**
- [ ] [Specific implementation task]
**Acceptance criteria:**
- [ ] [Verifiable, observable condition]
**Depends on:** B1

[Add more blocks as needed]

## Technical context
[Relevant patterns, files to touch, APIs, environment details — sourced from the PEP.
Include enough for an agent with only the codebase and this description.]

## Resources
[Filtered list of PEP resources relevant to this specific plan — Figma links, docs, GitHub refs]

## Dependencies
[Identifiers of Plan issues that must be Done before this plan starts, or "None".
Example: Blocked by: {issue_id}-P1 (needs API endpoints before frontend can connect)]

## PEP Reference
Parent PEP: [{issue_id}] {title}
```

---

## Step 5 — Write plan summary to local memory

Create the file `runs/memory/{issue_id}/plan.md` with:

```markdown
# Plan Summary — {issue_id}: {title}

## Plans created

| Identifier | Title | Depends on |
|---|---|---|
| [returned identifier] | [title] | none / [other identifier] |

## Sequencing rationale
[Why plans are ordered this way — what constrains the sequence]
```

---

## Step 6 — Post summary comment on PEP issue

Call `mcp__linear__linear_create_comment` with `issueId: "{issue_uuid}"` and this body:

```
📋 PEP decomposed — [N] plan(s) created

[identifier]: [Plan title]  →  Todo (awaiting your review)
[identifier]: [Plan title]  →  Todo (awaiting your review, blocked by [identifier])

**Sequencing:** [one sentence on execution order and why]

**Next step:** Review each Plan issue in Linear. When satisfied, move it to **Plan Approved** to start execution. Resonance picks up Plan Approved issues automatically.

Blocked plans will start automatically once their dependencies are Done — no manual action needed.
```

---

## Step 7 — Signal completion

After all Plan issues are created and the summary comment is posted, output EXACTLY:

`AGENT_SIGNAL: {{"type": "pep_decomposed", "pep_id": "{issue_id}", "plans": [{{"id": "<uuid>", "identifier": "<identifier>", "title": "<title>", "blocked_by_ids": ["<uuid-of-blocker>"]}}]}}`

- `id`: the Linear UUID returned when you created the Plan issue
- `identifier`: the Linear identifier (e.g. "RND-30")
- `title`: the full title including the [{issue_id}-P<N>] prefix
- `blocked_by_ids`: list of UUIDs of Plan issues that block this one (empty list if none)

The orchestrator uses this signal to set blocking relations between Plan issues in Linear.
Do not end this session without emitting this signal.

---

## Available Labels

{chr(10).join(label_rows)}

Use these to label each Plan issue. Use the primary domain of the Plan.
If a plan spans multiple domains, use the dominant one.

---

## [PM] Self-commentary

After creating each Plan issue, post a `[PM]` comment on it:

```
[PM] Created from PEP {issue_id}: {title}
Plan {issue_id}-P<N> of <total>.
Blocks: B1 → B2 → ... (sequential) or B1 ∥ B2 (parallel).
Rationale: [one sentence on why this plan is scoped this way]
```

This comment persists between agent sessions and helps future iterations understand intent.
"""
