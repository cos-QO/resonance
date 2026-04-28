# cc-pipeline — Command Reference

## Commands

| Command | What it does |
|---|---|
| `/pd-start <issue>` | Full kickoff: PEP → context collection → plan → post to Linear → await approval |
| `/pd-pep <issue>` | Create or validate a PEP for a Linear issue |
| `/pd-pep <issue> --validate` | Validate an existing PEP — report missing fields |
| `/pd-pep <issue> --create-tickets` | Auto-create Linear child tickets from Section 14 of the PEP |
| `/pd-scope <issue>` | Run context collection only (sub-agents for codebase, Linear, Figma) |
| `/pd-plan <issue>` | Draft and post implementation plan to Linear |
| `/pd-report <issue>` | Post execution report to Linear on completion |
| `/pd-status` | Show active plans and their Linear approval state |

## Skills (agent-facing)

| Skill | What it does |
|---|---|
| `pd-pep` | Create / validate / domain-detect PEPs |
| `pd-linear-scope` | Spawn parallel Haiku sub-agents for context collection |
| `pd-context-pack` | Synthesise sub-agent outputs into a structured context pack |
| `pd-plan-post` | Draft plan and post to Linear |
| `pd-report-post` | Generate and post execution report to Linear |
| `pd-github-pr` | Open GitHub PR linked to Linear issue |

## Rules (auto-loaded)

| Rule | Enforces |
|---|---|
| `pd-guardrail` | No implementation code without an approved plan in Linear |
| `pd-linear-sync` | Linear comments at each pipeline phase transition |
| `pd-issue-standard` | Minimum issue quality before planning starts |

## Local memory written

```
.claude/memory/pd/
├── peps/          ← PEP documents per issue
├── context/       ← sub-agent outputs + context packs
├── plans/         ← approved plans + meta (approval status, comment ID)
└── reports/       ← draft execution reports before posting
```

## Typical flow

```
/pd-start SPH-93
  → PEP validated / created
  → Sub-agents collect codebase + Linear + Figma context
  → Plan drafted and posted to Linear
  → Waiting for Plan Approved status...

[Human sets status to Plan Approved in Linear]

[Agent executes — guardrail confirms approval]
[Agent opens PR via pd-github-pr]

/pd-report SPH-93
  → Execution report posted to Linear
  → Issue status set to Done
```
