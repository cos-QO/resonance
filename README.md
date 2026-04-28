# Resonance

A supervised agentic delivery orchestrator. Polls Linear for approved issues, runs Claude Code agents in isolated git worktrees, and keeps humans in control at every decision point.

```
Linear (Plan Approved) → Resonance polls → launches Claude agent in git worktree
                       → agent signals ready → Linear moves to Human Review
                       → human reviews PR → merges → Done
```

Human gates are mandatory: **plan approval** before work starts, **human review** before merge. Agents surface uncertainty and ask for input via structured signals; humans approve or redirect via the `resonance` CLI.

## Quick start

**Prerequisites:** Python 3.11+, Git, [Claude Code CLI](https://claude.ai/code)

```bash
# 1. Clone
git clone https://github.com/cos-QO/resonance && cd resonance

# 2. Install
pip install -e .

# 3. Configure
cp .env.example .env
# Edit .env — add your LINEAR_API_KEY and LINEAR_PROJECT_ID

# 4. One-time Linear setup (creates required workflow states and labels)
resonance setup

# 5. Health check
resonance doctor

# 6. Start the orchestrator
python -m orchestrator.main
```

## Commands

Both `resonance` and `reso` work — use whichever you prefer.

```bash
resonance setup                                # configure credentials, create Linear states/labels
resonance doctor                               # health check — verify everything is wired up

resonance status                               # show all active runs
resonance status QO-123                        # detail for one run
resonance logs QO-123                          # recent events for a run

resonance approve QO-123                       # resume a run waiting for human input
resonance feedback QO-123 "use primary button" # send feedback without taking over
resonance pause QO-123                         # pause a run cleanly
resonance abort QO-123                         # stop a run permanently

resonance attach QO-123                        # print worktree + log paths for manual inspection
resonance watch                                # TUI dashboard (coming in Milestone 2)
```

## Linear setup

`resonance setup` creates everything automatically. For reference, these are the workflow states and labels Resonance requires:

**Workflow states**

| State | Meaning |
|---|---|
| Plan Approved | Orchestrator picks up this issue and starts work |
| In Progress | Agent is actively working |
| Agent Feedback Needed | Agent paused, waiting for human input |
| Human Review | Work complete — awaiting PR review |

**Labels** (applied by humans before moving to Plan Approved)

| Label | Task type |
|---|---|
| `frontend` | frontend_feature — new UI feature |
| `bug` + `frontend` | frontend_bug — UI regression fix |
| `design` | design_to_code — Figma → component (requires FIGMA_API_KEY) |

## Configuration

**`.env`** — your credentials, never committed:

```
LINEAR_API_KEY=lin_api_...
LINEAR_PROJECT_ID=<your-project-uuid>
FIGMA_API_KEY=...      # optional — required for design_to_code tasks
GITHUB_TOKEN=...       # optional — required for PR creation (Milestone 3)
```

**`WORKFLOW.md`** — runtime policy, committed and shared with your team:
- Task types, iteration limits, retry config, concurrency limits
- Controls which issue labels trigger which agent behaviour
- No credentials — safe to commit and share

## How it works

1. You create a Linear issue and label it (`frontend`, `bug`, etc.)
2. You review the agent's implementation plan and move the issue to **Plan Approved**
3. Resonance picks it up, creates an isolated git worktree, and launches a Claude Code agent
4. The agent works, then emits a structured signal: `AGENT_SIGNAL: {"type": "ready_for_review", ...}`
5. Resonance moves the issue to **Human Review** and posts a summary comment
6. You review the PR and merge — or send feedback with `resonance feedback QO-123 "..."`

If the agent hits uncertainty at any point, it emits `human_input_needed` and waits. You respond with `resonance approve QO-123` or `resonance feedback`.

## Architecture

```
orchestrator/     Runtime — polls Linear, manages worktrees, runs Claude
cli/              resonance/reso command — approve, feedback, pause, abort, status
WORKFLOW.md       Policy contract — task types, retry config, concurrency
.claude/          Claude Code multi-agent dev infrastructure (agents, skills, hooks)
runs/             Runtime state — events.jsonl, state.json, per-run logs (gitignored)
workspaces/       Git worktrees — one per active issue (gitignored)
docs/             Architecture docs and design notes
```

## Sharing with your team

Fork this repo. Each person:
1. Copies `.env.example` → `.env` and adds their own API keys
2. Runs `pip install -e .` and `resonance setup` (creates Linear states/labels once per workspace)
3. `WORKFLOW.md` is shared policy — edit it to change orchestrator behaviour for everyone

## Milestone status

- **Milestone 1 — Orchestrator core** ✅ — polling, worker management, CLI, Linear integration
- **Milestone 2 — TUI dashboard** — real-time Textual dashboard (`resonance watch`)
- **Milestone 3 — cc-pipeline integration** — plan gate wiring, PR creation, execution reports

## Requirements

Python 3.11+. Key dependencies: `httpx`, `typer`, `rich`, `textual`, `pyyaml`, `python-dotenv`.

See `requirements.txt` for the full list.
