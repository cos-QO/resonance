"""
Planning Agent orchestration.

Full E2E flow:

PEP Reader Agent (label: pep)
  Reads PEP, produces ONE Core Plan issue containing all plans/blocks/tasks.
  Core Plan → Human Review (for operator sign-off). PEP → Done.
  Signal: pep_decomposed

Block Decomposer Agent (label: core-plan)
  Reads approved Core Plan, creates Block sub-issues (one per block) with full
  context, task checklists, and acceptance criteria. Sets blocking relations.
  Blocks → Plan Approved. Core Plan → In Progress.
  Signal: blocks_created

Block Execution Agent (label: block)
  Implements all tasks, self-verifies, checks acceptance criteria.
  Updates issue description task checkboxes as tasks complete.
  Signals block_complete when all tasks done and verified.
  Signals human_input_needed when blocked — includes takeover instructions.

Planning Agent (label: plan — legacy)
  Reads a plan document, decomposes into phase issues → Plan Approved.
  Signal: plan_decomposed
"""
import logging
from pathlib import Path
from typing import Optional

from .config import Config

logger = logging.getLogger(__name__)

PEP_LABEL = "pep"
PLAN_LABEL = "plan"


def is_pep_issue(issue: dict) -> bool:
    label_names = {lbl["name"].lower() for lbl in issue.get("labels", {}).get("nodes", [])}
    return "pep" in label_names


def is_plan_issue(issue: dict) -> bool:
    label_names = {lbl["name"].lower() for lbl in issue.get("labels", {}).get("nodes", [])}
    return PLAN_LABEL in label_names and "pep" not in label_names


# ─────────────────────────────────────────────────────────────────────────────
# PEP Reader Agent
# ─────────────────────────────────────────────────────────────────────────────

def build_pep_reader_prompt(issue: dict, config: Config) -> str:
    """Prompt for the PEP Reader Agent.

    Reads the PEP, creates ONE Core Plan issue containing all plans/blocks/tasks.
    Core Plan goes to Human Review. PEP is marked Done.
    Signals pep_decomposed with the Core Plan UUID.
    """
    issue_id   = issue.get("identifier", issue["id"])
    issue_uuid = issue["id"]
    title      = issue.get("title", "")
    description = (issue.get("description", "") or "").strip()
    team_id    = config.linear_team_id
    project_id = config.linear_project_id or ""

    return f"""\
# PEP Reader Agent — {issue_id}: {title}

You are the Resonance PEP Reader Agent. Your job is to read this Product Execution
Prompt (PEP), understand the full scope of work, and produce ONE Core Plan issue
that captures every plan, block, and task in a structured, executable form.

You are the PM — not an executor. Do not write code. Think like a senior engineering
lead decomposing a project before handing it to a team.

---

## The PEP

{description if description else "_No description provided — read comments on this issue for context._"}

---

## Step 1 — Read all context

1. Read the PEP description above in full.
2. Fetch all comments on issue `{issue_id}` using `mcp__linear__linear_search_issues_by_identifier`.
   Comments contain human clarifications. Incorporate any context found there.
3. Note any external resources (Figma links, GitHub repos, API docs) — include them
   in the Core Plan under the relevant blocks.

---

## Step 2 — Design the Plans and Blocks

From the PEP, identify **Plans** (major deliverables, 1–5 per PEP) and within each
Plan the **Blocks** (atomic units of agent work):

**Plan rules:**
- 1–5 Plans per PEP
- Each Plan delivers something independently testable
- Plans that depend on other Plans must say so explicitly

**Block rules (CRITICAL):**
- One Block = one agent session = one PR
- 3–8 hours of focused work, single concern
- Each Block must have ≥2 measurable acceptance criteria
- Self-contained: every Block description must include all context an agent needs

**Good Block examples:**
  ✓ User model + migration (email, password_hash, created_at, soft delete)
  ✓ POST /auth/login — credential check, JWT response, refresh token
  ✗ Build the whole authentication system (too large)
  ✗ Fix button colour (too small)

---

## Step 3 — Create the Core Plan issue in Linear

Call `mcp__linear__linear_create_issue` ONCE with these fields:

| Field | Value |
|---|---|
| teamId | `{team_id}` |
| projectId | `{project_id}` |
| parentId | `{issue_uuid}` |
| title | `[{issue_id}] Execution Plan: {title}` |
| stateId | leave unset (defaults to Todo — orchestrator moves it to Human Review) |
| labelIds | the id of the `core-plan` label |
| description | use Core Plan Template below |

Record the returned `id` (UUID) and `identifier` — needed for the signal in Step 6.

### Core Plan Template

```markdown
## Overview
[One paragraph: what this delivery achieves and why it matters]

## Execution Map

### Plan 1 — <title>
**Goal:** [What this plan delivers]
**Depends on:** none / Plan 2

#### B1 — <block title>
**What:** [What this block implements]
**Domain:** frontend | backend | design | full-stack
**Tasks:**
- [ ] [Specific implementation task]
- [ ] [Specific implementation task]
**Acceptance Criteria:**
- [ ] [Verifiable, observable condition]
- [ ] [Verifiable, observable condition]
**Depends on:** none

#### B2 — <block title>
**What:** [What this block implements]
**Domain:** frontend | backend | design | full-stack
**Tasks:**
- [ ] [Specific implementation task]
**Acceptance Criteria:**
- [ ] [Verifiable, observable condition]
**Depends on:** B1

### Plan 2 — <title>
**Goal:** [What this plan delivers]
**Depends on:** Plan 1

#### B1 — <block title>
[...]

## Technical Context
[Codebase patterns, APIs, environment details, stack constraints relevant across all plans.
Include enough for an agent with only the codebase and this document.]

## Resources
[Figma links, API docs, GitHub refs, design tokens — all external resources from the PEP]

## Sequencing Rationale
[Why plans and blocks are ordered this way — what constrains the sequence]

## PEP Reference
Parent PEP: [{issue_id}] {title}
```

---

## Step 4 — Write plan summary to local memory

Create `runs/memory/{issue_id}/plan.md`:

```markdown
# Core Plan Summary — {issue_id}: {title}

## Core Plan Issue
[identifier]: [title]

## Plans and Blocks
Plan 1: [title]
  B1: [title] (independent)
  B2: [title] (depends on B1)
Plan 2: [title] (depends on Plan 1)
  B1: [title]

## Sequencing rationale
[One sentence explaining the execution order]
```

---

## Step 5 — Post summary comment on PEP issue

Call `mcp__linear__linear_create_comment` with `issueId: "{issue_uuid}"`.
Before posting, run `date -u +%H:%M` in Bash and compute the elapsed minutes
since your start to fill in `<elapsed>`.

```
📋 Core Plan created — [N] plan(s), [M] block(s) total  · <elapsed> elapsed

Core Plan: [identifier] → [title] (awaiting your review in Human Review)

Plans:
  Plan 1: [title] — [N] blocks
  Plan 2: [title] — [N] blocks (depends on Plan 1)

**Next step:** Review the Core Plan issue in Linear. When satisfied, move it
to **Plan Approved** to start block decomposition. Resonance picks it up automatically.
```

---

## Step 6 — Signal completion

After the Core Plan issue is created and the comment is posted, output EXACTLY:

`AGENT_SIGNAL: {{"type": "pep_decomposed", "pep_id": "{issue_id}", "core_issue_uuid": "<uuid>", "core_issue_identifier": "<identifier>"}}`

Replace `<uuid>` and `<identifier>` with the values returned by Linear when you created the issue.
Do not end this session without emitting this signal.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Block Decomposer Agent (Core Plan → Blocks)
# ─────────────────────────────────────────────────────────────────────────────

def build_core_plan_prompt(issue: dict, config: Config) -> str:
    """Prompt for the Block Decomposer Agent.

    Reads an approved Core Plan, creates Block sub-issues with full context,
    sets blocking relations, moves blocks to Plan Approved, signals blocks_created.
    """
    from datetime import datetime, timezone
    issue_id    = issue.get("identifier", issue["id"])
    issue_uuid  = issue["id"]
    title       = issue.get("title", "")
    description = (issue.get("description", "") or "").strip()
    team_id     = config.linear_team_id
    project_id  = config.linear_project_id or ""
    eligibility = config.eligibility_state
    started_at  = datetime.now(timezone.utc).strftime("%H:%M UTC")

    return f"""\
# Block Decomposer Agent — {issue_id}: {title}

You are the Resonance PM. This Core Plan was reviewed and approved by a human.
Your job is to create Block sub-issues — one per block — so execution agents can
implement each block independently.

---

## The Core Plan

{description if description else "_No description provided._"}

---

## Step 1 — Read and parse the plan

Read the Core Plan description above. Identify every Block across all Plans.
Note their titles, tasks, acceptance criteria, domain, and dependencies.

---

## Step 2 — Analyze parallelism

For each pair of blocks, determine if they can run concurrently:
- Blocks that touch the SAME files, modules, or database tables → SEQUENTIAL (add blocking relation)
- Blocks that work on INDEPENDENT areas (different components, different endpoints, different tables) → PARALLEL (no blocking relation, both go to Plan Approved)

Document your analysis in a brief table before creating issues.

Only add a blocking relation when there is a genuine data or code dependency.
Parallelize aggressively — the orchestrator runs multiple agents simultaneously.

---

## Step 3 — Create a sub-issue for each Block

For each Block, call `mcp__linear__linear_create_issue` with:

| Field | Value |
|---|---|
| teamId | `{team_id}` |
| projectId | `{project_id}` |
| parentId | `{issue_uuid}` |
| title | `[{issue_id}-B<N>] <Block title>` (global sequence, e.g. B1, B2, B3) |
| stateId | leave unset (defaults to Todo) |
| labelIds | `block` label id — optionally also a domain label (frontend/backend/design/bug) |
| description | use Block Issue Template below |

Record the returned `id` (UUID) and `identifier` for each block.

### Block Issue Template

```markdown
## Goal
[What this block implements — one clear paragraph]

## Tasks
- [ ] [Specific implementation task]
- [ ] [Specific implementation task]
- [ ] [Specific implementation task]

## Acceptance Criteria
- [ ] [Verifiable, observable condition]
- [ ] [Verifiable, observable condition]

## Technical Context
[Files to touch, patterns to follow, APIs, commands, environment variables.
Include everything an agent needs — it only has the codebase and this description.]

## Resources
[Relevant external links: Figma, API docs, GitHub refs]

## Dependencies
[Block identifiers that must be Done before this starts, or "None"]

## Parent Plan
[{issue_id}] {title}
```

---

## Step 4 — Set blocking relations

For each block that depends on another block, call `mcp__linear__linear_create_issue_relation`:
- For "B2 depends on B1": relation where B1 blocks B2
  - The issueId is the BLOCKER (B1), relatedIssueId is the BLOCKED (B2), type "blocks"

---

## Step 5 — Move all blocks to Plan Approved

Call `mcp__linear__linear_bulk_update_issues` with:
- `ids`: list of all block UUIDs
- `stateId`: state ID for `{eligibility}`

To get the state ID, call `mcp__linear__linear_search_issues_by_identifier` on
`{issue_id}` and read the `team.states` — find the state named `{eligibility}`.

---

## Step 6 — Post summary comment on Core Plan

Call `mcp__linear__linear_create_comment` with `issueId: "{issue_uuid}"`.
Before posting, run `date -u +%H:%M` in Bash and compute elapsed minutes since {started_at}.

```
📦 [{issue_id}] decomposed — [N] blocks created and queued  · <elapsed> elapsed

Parallel blocks (start simultaneously):
  [B1-identifier]: [title]
  [B2-identifier]: [title]

Sequential blocks (wait for dependency):
  [B3-identifier]: [title] — blocked by B1 (starts when B1 is Done)

Each block will be implemented and self-verified by an agent, then moved to Human Review.
```

---

## Step 7 — Signal completion

Output EXACTLY:

`AGENT_SIGNAL: {{"type": "blocks_created", "core_plan_id": "{issue_id}", "blocks": [{{"id": "<uuid>", "identifier": "<identifier>", "title": "<title>", "blocked_by_ids": []}}]}}`

- `id`: Linear UUID returned when you created the block issue
- `identifier`: e.g. "RND-42"
- `blocked_by_ids`: list of block UUIDs that block this one (empty list if none)

Do not end this session without emitting this signal.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Block Execution Agent
# ─────────────────────────────────────────────────────────────────────────────

def build_block_execution_prompt(issue: dict, task_cfg: dict) -> str:
    from datetime import datetime, timezone
    issue_id    = issue.get("identifier", issue["id"])
    issue_uuid  = issue["id"]
    title       = issue.get("title", "")
    description = (issue.get("description", "") or "").strip()
    started_at  = datetime.now(timezone.utc).strftime("%H:%M UTC")

    return f"""\
# Block Execution Agent — {issue_id}: {title}

You are a Resonance execution agent. Implement this block completely, verify your
own work, then signal done. One block = one PR.

## Block Specification

{description if description else "_No description provided._"}

---

## Execution Protocol

### Step 1 — Read the spec
Read every task and acceptance criterion before writing any code.

### Step 2 — Implement task by task

For each task in the **Tasks** section:

1. Implement the task (code, tests, config).
2. Commit with a focused message.
3. Update the issue description to check off the task:
   - Fetch current description via `mcp__linear__linear_search_issues_by_identifier` with identifier `{issue_id}`
   - Replace `- [ ] <task text>` with `- [x] <task text>` in the description
   - Update via `mcp__linear__linear_bulk_update_issues` with `ids: ["{issue_uuid}"]` and the updated description
4. Post a brief comment via `mcp__linear__linear_create_comment` with `issueId: "{issue_uuid}"`:
   ```
   ✅ Task done: <task name>  · <elapsed, e.g. "4 min in">
   <What you did — 1-2 sentences. Key decisions or findings only.>
   ```
   Compute elapsed time from your start time ({started_at}) using `date -u +%H:%M` in Bash.

### Step 3 — Self-verify

After all tasks are implemented:
- Run the test suite or relevant checks (build, lint, type-check)
- Verify every acceptance criterion by observable output
- If a criterion fails, fix it before signalling complete

### Step 4 — Signal complete

When ALL tasks are checked off and ALL acceptance criteria are met:

`AGENT_SIGNAL: {{"type": "block_complete", "summary": "<one sentence: what was built and verified>"}}`

---

## Blocker Protocol

If you hit a blocker you cannot resolve (missing credentials, architectural decision
needed, conflicting requirements, external dependency unavailable):

1. Post a comment via `mcp__linear__linear_create_comment` with `issueId: "{issue_uuid}"`:
   ```
   ⚠️ Blocked: <{issue_id}>

   **Blocker:** <what is blocking you — be specific>

   **Recommendations:**
   - Option A: <approach + tradeoff>
   - Option B: <approach + tradeoff>

   **To take control via Claude Code:**
   ```
   resonance attach {issue_id}
   resonance feedback {issue_id} "your instructions here"
   ```
   Worktree has all current changes committed. Branch: agent/{issue_id}
   ```

2. Signal:
   `AGENT_SIGNAL: {{"type": "human_input_needed", "question": "<specific question that needs answering>", "context": "<blocker details>"}}`

---

## Diagrams

When a diagram would clarify architecture, flows, or relationships — in a Linear comment
or in a documentation file — write a Mermaid code block directly:

````markdown
```mermaid
graph TD
  A[Start] --> B[Step]
```
````

Linear renders Mermaid natively. For docs, Mermaid is standard markdown.
If you need a rendered image URL (e.g. to embed in a README or Slack), fetch one from
kroki.io: `POST https://kroki.io/mermaid/svg` with the diagram as plain text body.

## Figma references

If the block description contains a Figma URL, use the figma MCP to inspect the design:
extract colours, spacing, component names, and layout — then implement to match.
You cannot write to Figma; it is read-only reference material.

## Rules
- Never signal block_complete unless every task checkbox is checked and every criterion verified
- Keep commits atomic — one logical change per commit
- Your very first action: post a comment with `issueId: "{issue_uuid}"` and body:
  `▶️ Starting block {issue_id}  · started {started_at}`
- Include elapsed time (from {started_at}) in every subsequent comment you post
"""


# ─────────────────────────────────────────────────────────────────────────────
# Legacy Planning Agent (plan label)
# ─────────────────────────────────────────────────────────────────────────────

def build_planning_prompt(issue: dict, config: Config) -> str:
    issue_id  = issue.get("identifier", issue["id"])
    title     = issue.get("title", "")
    description = (issue.get("description", "") or "").strip()

    eligibility = config.eligibility_state
    team_id     = config.linear_team_id
    project_id  = config.linear_project_id or ""

    task_types = config.workflow.get("task_types", {})
    label_rows: list[str] = []
    for tt_name, tt_cfg in task_types.items():
        if tt_name in ("plan", "pep", "core_plan", "block"):
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

After each call, record the returned `id` (UUID) and `identifier` (e.g. RND-25).

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
on the parent issue `{issue_id}` and read the `team.states` from the result.

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

Replace the placeholders with the actual values returned by Linear.
Do not end this session without emitting this signal.
"""
