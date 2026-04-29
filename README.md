# Resonance

Resonance is a supervised agentic delivery pipeline. It polls a Linear team for issues in "Plan Approved" state, launches Claude Code agents in isolated git worktrees, monitors their output for structured signals, and keeps humans in control at two mandatory gates: plan approval and PR review. The orchestrator manages state transitions in Linear, retries on failure, and surfaces everything in a Textual TUI dashboard.

---

## How it works

1. Create a Linear issue with a clear title and description. Apply a label that tells Resonance what kind of work it is (`frontend`, `bug`+`frontend`, `design`, `backend`, or `bug`+`backend`). For multi-phase work, create a `plan`-labelled issue and let the Planning Agent decompose it.

2. Move the issue to **Plan Approved** in Linear. This is your explicit authorization — the orchestrator will not touch issues in any other state.

3. Within 15 seconds, the orchestrator picks up the issue. It re-fetches it from Linear to confirm the state is still Plan Approved (fail-closed), creates a git worktree at `workspaces/<team-prefix>/<issue-id>/` on branch `agent/<issue-id>`, writes a `.claude/settings.json` pointing at shared plugin directories, and launches `claude -p "<prompt>" --output-format stream-json --permission-mode bypassPermissions`. Linear moves to **In Progress** and the `RES` label is added.

   Workers are QO-specialized: each prompt opens with a task-type persona ("QO Frontend Engineer", "QO Project Manager", etc.) and a numbered skills workflow listing which slash commands to use. All 40+ cc-qo-skills are available (`/connectui-dev`, `/verify`, `/qo-prototype`, `/qo-pr`, `/review`, etc.). Workers read the Queen One design system tokens (`connectui-design-system.md`) and stack reference (`connectui-stack.md`) via a shared memory symlink in every worktree.

4. The agent works inside the worktree. If it needs a human decision, it writes to stdout:
   ```
   AGENT_SIGNAL: {"type": "human_input_needed", "question": "...", "context": "..."}
   ```
   Resonance detects this, moves the Linear issue to **Agent Feedback Needed**, and pauses the run. Add a comment in Linear with your answer and move the issue back to Agent Feedback Needed — the orchestrator detects the state change, extracts new comments, and resumes with a new iteration.

5. When the agent finishes, it writes:
   ```
   AGENT_SIGNAL: {"type": "ready_for_review", "summary": "...", "artifacts": {"preview_url": "..."}}
   ```
   Resonance moves the issue to **Human Review** and posts a comment with the summary and preview URL.

6. Review the branch (`workspaces/<team-prefix>/<issue-id>/`, branch `agent/<issue-id>`). Merge when satisfied, or add feedback in Linear and move to Agent Feedback Needed to trigger another iteration. When done, move the issue to **Done** — the orchestrator detects this on its next reconciliation cycle and cleans up the worktree.

---

## Quick start

Prerequisites: Python 3.11+, Git 2.5+, [Claude Code CLI](https://claude.ai/code) (`claude auth login`)

```bash
git clone https://github.com/cos-QO/resonance && cd resonance
./setup.sh          # guided wizard: credentials + Linear states/labels
resonance doctor    # verify everything is wired correctly
./onair.sh          # start orchestrator + TUI dashboard
```

`./onair.sh` runs pre-flight checks, activates the virtual environment, runs `resonance doctor` (and `resonance fix` if it finds fixable issues), prompts for a Linear project scope if none is set, starts the orchestrator in the background, and opens the Textual TUI. Closing the TUI also stops the orchestrator.

To update a single credential: `./setup.sh update`
To remove credentials and runtime state: `./setup.sh wipe`

---

## Key concepts

### Workflow states

| Linear state | Who sets it | What it means |
|---|---|---|
| Todo | You / orchestrator on failure | Not ready, or returned after max retries |
| Plan Approved | You | Authorized — orchestrator will pick this up |
| In Progress | Orchestrator | Agent is actively running |
| Agent Feedback Needed | Orchestrator or you | Agent paused waiting for input; or you moved it here to send feedback after Human Review |
| Human Review | Orchestrator | Agent finished — PR is open, your review required |
| Done | You | Accepted; workspace cleaned up on next reconcile |
| Cancelled | You | Abandoned; workspace cleaned up on next reconcile |

### Signal protocol

Agents communicate back to the orchestrator by writing `AGENT_SIGNAL:` lines to stdout. The orchestrator scans every line of the Claude stream-json output. Three signal types are defined:

| Signal type | Emitted when | Orchestrator response |
|---|---|---|
| `human_input_needed` | Agent hit a decision it cannot make alone | Linear → Agent Feedback Needed; run paused; comment posted with question |
| `ready_for_review` | Agent finished the task | Linear → Human Review; run set to `waiting_human`; comment posted with summary and artifacts |
| `plan_decomposed` | Planning Agent finished decomposing a plan issue | Linear phase issues created and moved to Plan Approved; plan issue → Done |

Agents that exit without emitting a signal are treated as failures and retried up to `retry.max_attempts` times (default: 3) with exponential backoff (5s / 15s / 60s).

---

## TUI keyboard shortcuts

| Key | Action |
|---|---|
| `q` | Quit (also stops the orchestrator) |
| `r` | Refresh state from disk |
| `l` | Refresh Linear pipeline view |
| `p` | Set or change project scope (archives current session first) |
| `Tab` | Cycle run selection (shows `>` prefix) |
| `Enter` | Open detail modal for selected run |
| `f` | Send feedback to selected agent |
| `a` | Approve / resume selected run |
| `x` | Abort selected run |
| `v` | Toggle raw log viewer for selected run |
| `c` | Clear completed/failed runs and event log |
| `d` | Launch end-to-end demo (creates a plan issue in Linear) |
| `e` | Open full event browser |
| `?` | Help screen |

---

## Architecture

Four pieces work together:

| Component | Path | Role |
|---|---|---|
| Orchestrator | `orchestrator/` | Main loop: polls Linear, manages runs, drives the state machine |
| Runner | `orchestrator/runner.py` | Launches `claude -p` subprocess, parses stream-json, detects AGENT_SIGNALs |
| TUI | `tui/app.py` | Textual dashboard reading `runs/state.json` and `runs/events.jsonl` |
| Linear | via API | Source of truth for issue state and human decisions |

The orchestrator and TUI run as separate processes started by `./onair.sh`. They communicate through files: the orchestrator writes `runs/state.json` and `runs/events.jsonl`; the TUI reads them. CLI commands (approve, feedback, abort) are appended to `runs/commands.jsonl` and picked up by the orchestrator on its next tick.

---

## Configuration

`WORKFLOW.md` is the runtime policy file — committed, no credentials, edit to tune behaviour. Changes take effect on the next orchestrator restart.

Key settings:

| Setting | WORKFLOW.md path | Default |
|---|---|---|
| Eligibility state (trigger) | `linear.eligibility_state` | `Plan Approved` |
| Poll interval | `polling.interval_seconds` | 15 |
| Reconcile interval | `polling.reconcile_interval_seconds` | 120 |
| Max parallel runs | `concurrency.max_parallel_runs` | 2 |
| Max retries | `retry.max_attempts` | 3 |
| Backoff (seconds) | `retry.backoff_seconds` | `[5, 15, 60]` |
| Stall timeout | `retry.on_stall_minutes` | 30 |

Task types are defined in `task_types:` — add a new block to support a new label combination without changing orchestrator code.

`.env` holds credentials (`LINEAR_API_KEY`, `LINEAR_TEAM_ID`, optionally `LINEAR_PROJECT_ID`, `FIGMA_API_KEY`, `GITHUB_TOKEN`). Written by `./setup.sh`, never committed.

For detailed operation, troubleshooting, and recovery procedures, see `docs/operator-runbook.md`.
