# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<!-- AGENTIC:START -->
# Multi-Agent System

This project uses a multi-agent orchestration system. Full architecture is in `.claude/CLAUDE.md` — **read it before any complex task**.

## Quick Reference

- **15 agents** — PM (opus) coordinates; developer, tester, security, reviewer, etc. execute
- **32 skills** — auto-triggered (`/debug`, `/research`, `/planning`) and manual (`/verify`, `/commit`, `/train`)
- **7 rules** — guardrails, memory-protocol, file-organization + path-specific (security, testing, api, frontend)
- **12 hook scripts** — enforce quality gates, track execution, sync TODOs automatically

## Routing

| Request type | What happens |
|---|---|
| Simple (edit, git, test) | Execute directly — no overhead |
| Complex (multi-file, feature) | PM agent plans → agent chain executes → hooks enforce quality |
| Auto-detected | Skills trigger automatically: errors→`/debug`, reviews→`/review`, research→`/research` |

## Key Files

| File | Purpose |
|---|---|
| `.claude/CLAUDE.md` | **Full architecture** — routing, orchestration, memory system, all details |
| `.claude/agents/*.md` | Agent definitions (15 agents) |
| `.claude/skills/*/SKILL.md` | Skill definitions (32 skills) |
| `.claude/rules/*.md` | Auto-loaded rules (7 rules) |
| `.claude/hooks/*.py` | Hook automation scripts |
| `.claude/memory/` | Shared project memory (standards, plans, reports) |
| `.claude/agent-memory/` | Per-agent persistent memory (PM, developer, tester) |
| `.claude/settings.json` | Permissions and hook configuration |

## Essential Rules

1. **Developer always paired with tester** — no exceptions
2. **Memory before assumptions** — check `.claude/memory/standards/` before decisions
3. **PM plans, agents execute** — PM never implements directly
4. **Hooks enforce quality** — don't bypass; they track execution and validate output
<!-- AGENTIC:END -->

---

# Project: Resonance Orchestrator

Resonance is a working Python application — a **supervised agentic delivery pipeline** that polls Linear for approved issues, launches Claude CLI workers in isolated git worktrees, and manages their full lifecycle through human review gates.

The entry point for new work is a **PEP** (Product Execution Prompt) — a structured document in a `[PEP] <title>` Linear project. Moving the PEP issue (label: `pep`) to Plan Approved triggers Resonance to decompose it into Plan issues. Humans approve each Plan, then Resonance executes them in dependency order using Block issues as the atomic unit of git work. See `docs/pep-to-execution-design.md` for the full flow.

The package installs as `resonance` / `reso` (see `pyproject.toml`). Requires Python 3.11+.

## Commands

```bash
# First-time setup (interactive, creates .env and Linear workflow states)
./wizard.sh
resonance setup

# Health check (verifies credentials, Linear states/labels)
resonance doctor

# Start orchestrator + TUI
./onair.sh                          # preferred — handles venv, doctor, and TUI
python -m orchestrator.main         # orchestrator only (no TUI)

# Operator commands
resonance status                    # all active runs
resonance status QO-123             # one run in detail
resonance logs QO-123               # tail recent events
resonance approve QO-123            # resume waiting run
resonance feedback QO-123 "text"    # send feedback to agent
resonance pause QO-123              # pause without aborting
resonance abort QO-123              # stop permanently
resonance attach QO-123             # print worktree + log paths
resonance checkpoint QO-123         # write RESONANCE.md to worktree (human handoff prep)
resonance checkpoint QO-123 --push  # write RESONANCE.md and push branch to GitHub
resonance watch                     # TUI dashboard (Textual)
resonance plan                      # interactive issue/milestone creator
resonance project list              # list Linear projects
resonance project set <url-or-id>   # scope to a project
resonance fix                       # auto-create missing Linear states/labels

# Development install
pip install -e .
```

### onair.sh options

```bash
./onair.sh --project               # pick project interactively
./onair.sh --project <url-or-id>   # set specific project then start
./onair.sh --clear-project         # remove project scope
```

## Architecture

### Three-plane model

| Plane | Tool | Responsibility |
|---|---|---|
| Intent & approval | Linear | Issues, PRDs, ownership, approval state, final reports |
| Execution | Claude Code CLI (`claude -p`) | Planning, implementation in git worktrees |
| Enforcement | GitHub | PR review, CI, merge restrictions |

**Operating rule:** Linear defines the work → Resonance executes in a worktree → human reviews before merge.

### Core execution loop (`orchestrator/poller.py`)

1. Poll Linear every 15s for issues in `Plan Approved` state
2. Classify issue by label → task type (`design_to_code`, `frontend_feature`, `frontend_bug`, `backend_feature`, `backend_bug`, `plan`)
3. Create a git worktree at `workspaces/{team_prefix}/{issue_id}` on branch `agent/{issue_id}`
4. Build prompt and launch `claude -p --output-format stream-json --permission-mode bypassPermissions`
5. Parse `AGENT_SIGNAL: {"type": "..."}` events from stdout to detect state transitions
6. On `ready_for_review` → move Linear issue to `Human Review`, post summary comment
7. On `human_input_needed` → move to `Agent Feedback Needed`, wait for comment
8. On failure after retries → move back to `Todo`, post failure report
9. Reconcile loop (every 120s) stops local runs if Linear state changed externally

### Key modules

| Module | Purpose |
|---|---|
| `orchestrator/poller.py` | Main orchestration loop — `Poller.run_forever()` |
| `orchestrator/runner.py` | Subprocess wrapper for `claude -p`; parses `AGENT_SIGNAL` |
| `orchestrator/state.py` | Run state persisted in `runs/state.json`; command queue in `runs/commands.jsonl` |
| `orchestrator/workspace.py` | Git worktree lifecycle — create, write `.claude/settings.json`, remove |
| `orchestrator/classifier.py` | Maps Linear labels → task type from `WORKFLOW.md` |
| `orchestrator/linear_client.py` | Linear GraphQL API client |
| `orchestrator/config.py` | Loads `WORKFLOW.md` (YAML) + `.env` into typed `Config` object |
| `orchestrator/memory.py` | Per-issue local memory in `runs/memory/{issue_id}/` |
| `orchestrator/planner.py` | PEP Reader Agent prompt (`build_pep_reader_prompt`) + Planning Agent prompt (`build_planning_prompt`) |
| `orchestrator/hooks/` | Hooks wired from `WORKFLOW.md`: uncertainty detector, event bridge, phase tracker, artifact poster |
| `cli/main.py` | Typer CLI — all `resonance` commands |
| `tui/app.py` | Textual TUI dashboard |

### WORKFLOW.md

`WORKFLOW.md` is the **machine-readable runtime contract** — a YAML file loaded by the orchestrator at startup. It defines:
- Linear state model and eligibility state
- Task types: detection labels, skills, rules, workers, required artifacts, retry policy
- Workspace policy, concurrency limits, polling intervals, handoff states
- Hook wiring

Operators edit `WORKFLOW.md` to change runtime behavior. No orchestrator code changes needed to add a task type.

### Signal protocol

Agents communicate completion via `AGENT_SIGNAL` lines in stdout:

```
AGENT_SIGNAL: {"type": "ready_for_review", "summary": "...", "artifacts": {"preview_url": "..."}}
AGENT_SIGNAL: {"type": "human_input_needed", "question": "...", "context": "..."}
AGENT_SIGNAL: {"type": "plan_decomposed", "phases": [...]}
```

The `Runner` scans all output (stream-json and plain text) for this pattern.

### Run state machine

States tracked in `runs/state.json`:

```
running → waiting_human → (feedback) → running
        → needs_input   → (feedback) → running
        → failed        (after max retries)
        → complete
        → archived      (reconciled away)
paused  → running       (on approve)
```

### Per-issue memory (`runs/memory/{issue_id}/`)

- `context.json` — current iteration, status, Linear URL, timestamps
- `feedback/` — human feedback written between iterations
- `handoffs/iter-{N}.md` — agent-written handoff notes for next iteration
- `artifacts.json` — artifact URLs produced by the agent

### Environment variables (`.env`)

| Variable | Required | Purpose |
|---|---|---|
| `LINEAR_API_KEY` | Yes | Linear personal API key (`lin_api_...`) |
| `LINEAR_TEAM_ID` | Yes | UUID of the watched team |
| `LINEAR_PROJECT_ID` | No | Scope to a project within the team |
| `LINEAR_STATE_ELIGIBILITY` | No | Override default `Plan Approved` |
| `LINEAR_STATE_IN_PROGRESS` | No | Override default `In Progress` |
| `LINEAR_STATE_FEEDBACK` | No | Override default `Agent Feedback Needed` |
| `LINEAR_STATE_REVIEW` | No | Override default `Human Review` |
| `LINEAR_STATE_RETURN` | No | Override default `Todo` |
| `FIGMA_API_KEY` | No | Required for `design_to_code` tasks |
| `GITHUB_TOKEN` | No | Required for automated PR creation |

### Workspace isolation

Each issue gets a git worktree (`workspaces/{team_prefix}/{issue_id}`) with its own branch (`agent/{issue_id}`). The orchestrator writes a `.claude/settings.json` into the worktree with absolute paths to the shared plugin dirs (`.claude/cc-pipeline`, `.claude/cc-qo-skills`) and `.mcp.json`. The `ISSUE_ID` env var is injected into every worker session.

Worktrees are cleaned up when the Linear issue reaches `Done` or `Cancelled`.

## Runtime data directories

| Path | Contents |
|---|---|
| `runs/state.json` | Active/recent run records (source of truth for local state) |
| `runs/events.jsonl` | Append-only event log (TUI tails this) |
| `runs/commands.jsonl` | CLI → orchestrator command queue |
| `runs/logs/` | Per-run raw `claude` output logs |
| `runs/memory/` | Per-issue memory (`context.json`, handoffs, feedback) |
| `workspaces/` | Git worktrees (one per active issue) |

## MCP servers

Configured in `.mcp.json`:
- **linear** — `mcp__linear__*` tools for Linear issue/project access
- **context7** — live library/framework documentation
- **figma** — design file access (requires `FIGMA_API_KEY`)

## Human-in-the-loop plugin (cc-resonance)

`.claude/cc-resonance/` — operator interface for working alongside Resonance.

| Command | Purpose |
|---|---|
| `/reso <ID>` | Load full issue context (hierarchy, comments, memory, RESONANCE.md) into any session |
| `/create-pep [title]` | Author a PEP interactively and push it to Linear |
| `/reso-takeover <ID>` | Claim control of a running issue, pause Resonance, get worktree path |
| `/reso-handback [note]` | Commit work, post handback comment, update Linear state |

The `RESONANCE.md` file in each worktree root is the portable checkpoint — written by Resonance on pause/Human Review, updated by humans on handback. Readable on GitHub without cloning.

## Worker plugins (cc-qo-skills)

`.claude/cc-qo-skills` is a symlink to the shared QO skills module. Workers get this via `--plugin-dir ../../.claude/cc-qo-skills`. Provides 40+ skills including:

| Skill | Use case |
|-------|---------|
| `/connectui-dev <task>` | ConnectUI specialization — loads design system + code standards, queries Context7 + Figma |
| `/verify L1\|L2\|L3` | Automated quality pipeline (build, lint, tests, security) |
| `/qo-prototype <figma-url>` | Figma-to-code: maps design tokens to Orion components |
| `/qo-component <Name>` | Scaffold new Orion/MUI component with Storybook story |
| `/qo-pr` | Generate ConnectUI-standard PR description from git diff |
| `/qo-bug` | Structured bug investigation workflow |
| `/review` | Deep code review |

Workers are prompted with their available skills in the `## Skills Available` section of the generated prompt, with a recommended execution order.

## QO Design System Reference

`.claude/memory/standards/connectui-design-system.md` — authoritative token reference (colors, typography, spacing, shape, component list) derived from the connect-ui repo design tokens. Workers access this via an absolute symlink at `workspaces/{team_prefix}/{issue_id}/.claude/memory` → `<repo-root>/.claude/memory`.

`.claude/memory/standards/connectui-stack.md` — technology stack reference (React, MUI v7, TanStack, Zustand, Firebase, conventions).

To refresh from GitHub when connect-ui changes:
```bash
python3 scripts/sync-design-system.py
```
