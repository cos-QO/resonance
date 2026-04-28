# cc-pipeline

Agentic delivery pipeline module for Claude Code. Installs as a plugin alongside `cc-qo-skills`.

## What it does

Wraps every stage of delivery in a skill or rule:

- **PEP** — structured LLM-native input replacing the raw PRD (`/pd-pep`)
- **Context collection** — parallel sub-agents pull from Linear, codebase, and Figma before planning
- **Plan gate** — `pd-guardrail` rule blocks any code without an approved plan in Linear
- **Execution** — hands off to `cc-qo-skills` for implementation standards
- **Report** — posts a structured execution report to Linear on close (`/pd-report`)

## Installation

```bash
claude --plugin-dir /path/to/cc-pipeline
```

## Required environment variables

```bash
export LINEAR_API_KEY=lin_api_...
export FIGMA_API_KEY=...   # optional — only needed for frontend tasks
```

## Commands

| Command | Purpose |
|---|---|
| `/pd-start <issue>` | Full kickoff: PEP → context → plan → await approval |
| `/pd-pep <issue>` | Create or validate a PEP for a Linear issue |
| `/pd-scope <issue>` | Run context collection only (sub-agents) |
| `/pd-plan <issue>` | Draft and post implementation plan to Linear |
| `/pd-report <issue>` | Post execution report to Linear on completion |
| `/pd-status` | Show active plans and their Linear approval state |

## Works with

- **cc-qo-skills** — execution standards (connectui-dev, verify, qo-pr). Install both.
- **Linear MCP** — pre-wired in `.mcp.json`
- **Figma MCP** — pre-wired, requires `FIGMA_API_KEY`

## Rules loaded automatically

- `pd-guardrail.md` — blocks execution without an approved plan
- `pd-linear-sync.md` — enforces Linear updates at each phase transition
- `pd-issue-standard.md` — validates required fields before planning starts
