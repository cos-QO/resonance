# Resonance

Resonance is a supervised agentic delivery pipeline. It polls Linear for approved work, launches Claude Code agents in isolated git worktrees, and keeps humans in control at two mandatory gates: plan approval and branch review. The full work unit is a **PEP** — a structured brief that Resonance decomposes through a Core Plan into atomic Blocks, each executed by a Claude agent.

---

## How it works

Work moves through three issue types in Linear, each requiring explicit human approval before Resonance acts.

### 1. Write a PEP

Create a Linear issue with label `pep` inside a `[PEP] <title>` project. Describe what you want built — goals, constraints, acceptance criteria. Move it to **Plan Approved** when you are ready.

### 2. PEP Reader Agent (claude-opus, 3–7 min)

Resonance picks up the PEP within 15 seconds and launches a PEP Reader Agent. It reads the PEP and creates one **Core Plan** issue (label: `core-plan`, parent: PEP issue) describing the full implementation approach. The PEP moves to Done; the Core Plan moves to **Human Review**.

### 3. Review the Core Plan

Read the Core Plan. Edit it if needed. Move it to **Plan Approved** to authorize execution.

### 4. Block Decomposer Agent (claude-opus, 5–12 min)

Resonance launches a Block Decomposer Agent that reads the Core Plan and creates **Block** sub-issues (label: `block`) with explicit Linear blocking relations — B2 is blocked by B1, and so on. Blocks are the atomic units of git work.

### 5. Block Execution Agents (claude-sonnet)

Resonance picks up blocks in dependency order and runs a Block Execution Agent per block. All blocks for a project share one git worktree:

```
workspaces/{project-slug}/main/          # shared branch: agent/{project-slug}
workspaces/{project-slug}/issues/{id}/   # per-block scratch data
```

Each agent receives `ISSUE_ID`, `ISSUE_PATH`, and `MAIN_PATH` as environment variables. It updates Linear checklist items as tasks complete and emits `AGENT_SIGNAL: {"type": "block_complete", ...}` when the block is done. The block moves to **Done** and, if `GITHUB_TOKEN` is set, the branch is pushed to origin.

If an agent needs a human decision mid-block, it emits `human_input_needed` — the block moves to **Agent Feedback Needed**. Add a comment in Linear with your answer and move it back; Resonance resumes with the new context.

### 6. Review and merge

When all blocks are done, the Core Plan moves to **Human Review**. Review the branch on GitHub. When satisfied, move the Core Plan to **Done** — Resonance cleans up the workspace on its next reconcile cycle.

---

## Quick start

Prerequisites: Python 3.11+, Git 2.5+, [Claude Code CLI](https://claude.ai/code) (`claude auth login`)

```bash
git clone https://github.com/cos-QO/resonance && cd resonance
./wizard.sh          # guided: credentials + Linear states/labels
resonance doctor     # verify everything is wired correctly
./onair.sh           # start orchestrator + TUI dashboard
```

`./onair.sh` activates the virtual environment, runs `resonance doctor` (and `resonance fix` for fixable issues), starts the orchestrator in the background, and opens the Textual TUI. Closing the TUI stops the orchestrator.

**onair.sh options:**

```bash
./onair.sh --project                 # pick a Linear project interactively
./onair.sh --project <url-or-id>     # set a specific project then start
./onair.sh --clear-project           # remove project scope
```

To update a single credential: `./wizard.sh update`
To wipe credentials and runtime state: `./wizard.sh wipe`

---

## TUI keyboard shortcuts

| Key | Action |
|---|---|
| `q` | Quit (stops the orchestrator) |
| `r` | Refresh state from disk |
| `l` | Refresh Linear pipeline view |
| `p` | Set or change project scope |
| `Tab` | Cycle run selection |
| `Enter` | Open detail modal for selected run |
| `o` | Open waiting run in Claude Code — launches new terminal at worktree, clipboard-primes initial message |
| `f` | Send feedback to selected agent |
| `a` | Approve / resume selected run |
| `x` | Abort selected run |
| `v` | Toggle raw log viewer |
| `c` | Clear completed runs and event log |
| `d` | Demo — creates a PEP in Linear |
| `e` | Event browser (300-event history) |
| `s` | Debug tracing settings modal |
| `t` | Debug trace viewer |
| `?` | Help screen |

---

## Debug tracing

Press `s` in the TUI to open the Settings modal. Toggles available:

- Enable debug tracing
- Capture MCP calls
- Capture Linear API calls
- Capture agent thinking
- Capture pipeline decisions

When tracing is active, the header bar shows `● trace` in magenta and structured JSONL is written to `runs/traces/session-*.jsonl` — full tool inputs/outputs, API timings, and reasoning text. Press `t` to browse the latest trace file; press `Enter` on any entry for full detail.

---

## Architecture

Three planes work together:

| Plane | Component | Role |
|---|---|---|
| Intent | Linear | Source of truth for issues, states, comments, and human decisions |
| Execution | Resonance (local) | Python orchestrator — polls Linear every 15s, launches Claude CLI workers in git worktrees, drives the state machine |
| Enforcement | GitHub | Branch hosting, PR review, merge gate |

**Within Resonance:**

| Module | Path | Role |
|---|---|---|
| Orchestrator | `orchestrator/poller.py` | Main loop: polls Linear, classifies issues, manages runs |
| Runner | `orchestrator/runner.py` | Launches `claude -p`, parses stream-json, detects AGENT_SIGNALs |
| Planner | `orchestrator/planner.py` | Builds PEP Reader and Block Decomposer prompts |
| State | `orchestrator/state.py` | Run records in `runs/state.json`; command queue in `runs/commands.jsonl` |
| Workspace | `orchestrator/workspace.py` | Git worktree lifecycle |
| TUI | `tui/app.py` | Textual dashboard |

The orchestrator and TUI communicate through files. The orchestrator writes `runs/state.json` and `runs/events.jsonl`; the TUI reads them. CLI commands (`resonance approve`, `resonance feedback`, etc.) are appended to `runs/commands.jsonl` and picked up on the next tick.

### Signal protocol

Agents communicate state transitions via `AGENT_SIGNAL:` lines in stdout:

| Signal type | Emitted when | Orchestrator action |
|---|---|---|
| `pep_decomposed` | PEP Reader done | Core Plan created; PEP → Done; Core Plan → Human Review |
| `blocks_created` | Block Decomposer done | Blocks and Linear blocking relations created |
| `block_complete` | Block agent done | Block → Done; branch pushed if GITHUB_TOKEN set |
| `ready_for_review` | Execution issue done | Linear → Human Review; summary comment posted |
| `human_input_needed` | Agent needs a decision | Linear → Agent Feedback Needed; run paused |

Agents that exit without a signal are retried up to `retry.max_attempts` times with exponential backoff.

### Block routing labels

Blocks are routed to the correct worker persona by their labels:

`frontend` | `backend` | `design` | `bug`+`frontend` | `bug`+`backend`

### Human-in-the-loop plugin (cc-resonance)

Commands for working alongside Resonance in any Claude session:

| Command | Purpose |
|---|---|
| `/create-pep [title]` | Author a PEP interactively and push it to Linear |
| `/reso <ID>` | Load full issue context (hierarchy, comments, memory) into the session |
| `/reso-takeover <ID>` | Claim control of a running issue, pause Resonance, get worktree path |
| `/reso-handback [note]` | Commit work, post handback comment, update Linear state |

---

## Configuration

`WORKFLOW.md` is the runtime policy file — committed, no credentials, edit to tune behavior. Changes take effect on the next orchestrator restart. Adding a new task type requires only a new block in `task_types:` — no code changes.

| Setting | Default |
|---|---|
| Eligibility state | `Plan Approved` |
| Poll interval | 15s |
| Reconcile interval | 120s |
| Max parallel runs | 2 |
| Max retries | 3 |
| Backoff | 5s / 15s / 60s |
| Stall timeout | 30 min |

`.env` holds credentials. Written by `./wizard.sh`, never committed.

| Variable | Required | Purpose |
|---|---|---|
| `LINEAR_API_KEY` | Yes | Linear personal API key (`lin_api_...`) |
| `LINEAR_TEAM_ID` | Yes | UUID of the watched team |
| `LINEAR_PROJECT_ID` | No | Scope to a specific project |
| `GITHUB_TOKEN` | No | Auto-push branch after each block completes |
| `FIGMA_API_KEY` | No | Required for `design_to_code` tasks |

---

## For more

- `docs/how-it-works.md` — full technical reference
- `docs/operator-runbook.md` — day-to-day operation, troubleshooting, and recovery
