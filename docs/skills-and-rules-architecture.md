# Skills & Rules Architecture

## The Deliverable: A Pipeline Module

The pipeline ships as an installable Claude Code module. In this repository it lives at
`.claude/cc-pipeline/` so Claude agents can use it without extra setup. When distributed
to other teams, they install it into their own `.claude/cc-pipeline/` directory.

```
.claude/cc-pipeline/           ← location in this repo
├── .claude-plugin/plugin.json
├── .mcp.json              ← Linear MCP pre-wired
├── README.md
├── COMMANDS.md            ← full command + skill reference
├── commands/              ← user-facing slash commands (/pd-*)
├── skills/                ← agent-facing reusable logic
└── rules/                 ← auto-loaded workflow rules
```

**Namespace:** `/pd-*` (pipeline delivery) — never collides with `/qo-*` from cc-qo-skills.
**Scoped memory:** writes under `.claude/memory/pd/` only.
**Activation:** guardrail rules enforce only inside a project with a Linear reference.

---

## Why This Layer Exists

A delivery pipeline documented in Linear is a process. A delivery pipeline enforced by skills and rules is an agentic system.

Without a skills/rules layer:
- Agents start coding without checking for an approved plan
- Context gathering is ad hoc — agents reason from the current issue alone
- Agents don't know which design system tokens, API patterns, or teams to consult
- Execution reports never get written because nothing requires them

With the module installed:
- `pd-guardrail.md` blocks execution until a plan is approved in Linear
- `/pd-scope` uses parallel Haiku agents to gather cross-team context in seconds
- Skills load the right team standards before any work starts
- `/pd-report` posts a structured execution report to Linear on completion

---

## Commands (user-facing, all `/pd-*`)

| Command | Purpose |
|---|---|
| `/pd-init` | Verify Linear MCP is working, cache team + project structure |
| `/pd-start <linear-issue>` | Full kickoff: classify → scope → plan → post to Linear → await approval |
| `/pd-scope <linear-issue>` | Run Haiku agent scoping only, produce context pack |
| `/pd-plan <linear-issue>` | Draft and post implementation plan to Linear |
| `/pd-report <linear-issue>` | Post execution report to Linear on completion |
| `/pd-status` | Show active plans and their Linear sync state |

---

## Skills (agent-facing reusable logic)

| Skill | What it does |
|---|---|
| `pd-linear-scope` | Orchestrates parallel Haiku agents for cross-team context gathering from Linear |
| `pd-context-pack` | Synthesizes Haiku agent results into a structured context pack + impact map |
| `pd-issue-validate` | Validates issue completeness against standards by issue type |
| `pd-plan-post` | Formats plan and posts to Linear as a comment; records plan ID |
| `pd-report-post` | Formats execution report and posts to Linear on task close |

---

## Rules (auto-loaded)

| Rule | Enforces |
|---|---|
| `pd-guardrail.md` | No code without an approved plan in Linear |
| `pd-issue-standard.md` | Required fields by issue type — agents block if missing |
| `pd-linear-sync.md` | Mandatory Linear updates at each phase transition |

---

## The Haiku Agent Scoping Pattern

When broad awareness is required, context gathering uses **parallel lightweight Haiku agents** rather than one Sonnet agent making sequential MCP calls. Haiku agents retrieve and summarize; they do not reason or decide. The main agent synthesizes.

```
Main agent classifies issue → broad awareness required
        ↓
Spawn 4–6 Haiku agents in parallel via Linear MCP:

  Haiku-1  parent project overview + linked docs
           → key decisions, constraints, owners

  Haiku-2  Engineering issues (last 30 days, same systems)
           → related work, risk signals

  Haiku-3  Design/Product issues linked to project
           → design refs, open questions

  Haiku-4  Issues this issue depends on
           → status, blockers, risk signals

  Haiku-5  Recently closed similar issues
           → patterns that emerged, what to reuse

        ↓ all return structured summaries in ~10–15 seconds
Main agent synthesizes → context pack + impact map
        ↓
/pd-plan writes plan + posts to Linear for human approval
```

This mirrors the `mini-troubleshooter` pattern: cheap parallel data gathering, expensive synthesis only once.

---

## Issue Standards (not templates)

A template is a rigid form that gets skipped under pressure. A standard defines required information with quality criteria, validated by the agent before submission.

### Core fields — all issue types

- **Outcome** — what changes for whom (concrete, not vague)
- **Scope** — what's in and explicitly what's out
- **Dependencies** — named systems and teams
- **Acceptance criteria** — how we know it's done
- **Classification** — simple / medium / large / complex

### Additional fields by type

| Type | Extra required fields |
|---|---|
| Feature / Epic | Success metrics, Figma reference, product sign-off, adjacent teams |
| Bug | Steps to reproduce, expected vs actual, severity + customer impact |
| Technical task | Risk if deferred, complexity estimate, rollback plan |
| Data / Analytics | Analytics events, data model changes, privacy flags |
| Research / Spike | Questions to answer, time-box, output format, decision owner |

---

## What Lives Where

| Information | Location | Why |
|---|---|---|
| Intent, ownership, approvals | Linear | Human-readable, shared, queryable by MCP |
| Plan (full detail) | Local `.claude/memory/pd/plans/` | Working copy the agent executes against |
| Plan summary + approval | Linear comment | Humans review and approve without repo access |
| Context pack + impact map | Local `.claude/memory/pd/context/` | Working state; summary posted to Linear |
| Phase transition updates | Linear comments | Stakeholder visibility without noise |
| Execution report | Linear comment | The permanent record |
| Research notes, Figma Q&A | Local `.claude/memory/pd/notes/` | Agent scratch; not stakeholder-facing |
| Execution report draft | Local first, then posted to Linear | Review before publishing |

---

## Relationship to cc-qo-skills

| Module | Handles |
|---|---|
| `cc-pipeline` (this) | Pipeline orchestration — issue → context → plan → approval → report |
| `cc-qo-skills` | Execution — how to code (connectui-dev, verify, qo-prototype, qo-pr) |

They are complementary. A team installs both: cc-qo-skills for execution standards, cc-pipeline for delivery structure.

The pipeline module calls into cc-qo-skills execution skills at the implementation phase. It never duplicates them.

---

## What Already Exists (from cc-qo-skills and cc-modules)

| Asset | What it does | How it's reused |
|---|---|---|
| `connectui-dev` skill | Load design system + code standards before frontend work | Pattern for standards-loading in all `pd-` execution paths |
| `qo-bug` skill | Structured Linear ticket creation | Foundation for `pd-issue-validate` |
| `verify` skill L1/L2/L3 | Quality pipeline: build, lint, tests, security | Called from `/pd-start` execution phase |
| `qo-pr` skill | PR description from git diff | Called from `/pd-start` at PR creation |
| `/qo-kickoff` command | 10-gate kickoff pipeline with Linear sync | Reference architecture for `/pd-start` design |
| `qo-workflow.md` rule | Linear hygiene, plan discipline | Reference for `pd-linear-sync.md` rule |
| `mini-troubleshooter` | Parallel Haiku data gathering | Direct model for `pd-linear-scope` skill |

---

## Design Decisions (resolved)

1. **Where does cc-pipeline live?** → `.claude/cc-pipeline/` in this repo. Claude agents load
   it automatically. When distributed to other teams, they install it into their own `.claude/`.

2. **Where does plan approval live in Linear?** → Custom Linear workflow state named
   `Plan Approved`. Queryable via API, unambiguous, visible on the board. Defined in `WORKFLOW.md`.

3. **How is the team-context routing map maintained?** → Open. Currently static rule file.
   MCP-derived routing from Linear team structure is the intended V2 direction.

4. **Does classification use labels or field inference?** → Labels (`design`, `frontend`, `bug`).
   Explicit human signal applied before the issue reaches `Plan Approved`. Defined in `WORKFLOW.md`.
