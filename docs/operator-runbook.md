# Operator Runbook

Day-to-day operation reference for Resonance. Assumes setup is already complete. If you have not run `./wizard.sh` yet, start there.

---

## Prerequisites

| Requirement | Minimum | How to check |
|---|---|---|
| Python | 3.11+ | `python3 --version` |
| Git | 2.5+ (worktree support) | `git --version` |
| Claude Code CLI | latest | `claude --version` |

Claude Code must be authenticated:
```bash
claude auth login
claude --version   # confirms auth
```

---

## Installation

```bash
git clone https://github.com/cos-QO/resonance && cd resonance
./wizard.sh
```

`./wizard.sh` does the following in order:

1. Checks whether `resonance` is installed; if not, runs `pip install -e .` automatically.
2. Prompts for your Linear API key and validates it against the Linear API.
3. Fetches your Linear teams, lets you pick by number or paste a team URL, resolves it to a team UUID, and writes `LINEAR_TEAM_ID` to `.env`.
4. Creates the four required workflow states in your Linear team (Plan Approved, In Progress, Agent Feedback Needed, Human Review) — skips any that already exist.
5. Creates the required labels (`frontend`, `bug`, `design`) — skips any that already exist.
6. Prompts for optional credentials: `FIGMA_API_KEY` (design tasks) and `GITHUB_TOKEN` (PR creation, Milestone 3). Both can be skipped with Enter.
7. Writes `.env`.

After setup: `resonance doctor` confirms everything is wired up correctly, then `./onair.sh` starts the orchestrator.

**Setup modes:**

```bash
./wizard.sh              # first-time setup (default)
./wizard.sh overwrite    # redo everything — delete .env and re-enter all credentials
./wizard.sh update       # update one or more API keys interactively
./wizard.sh wipe         # remove .env and clear runs/state.json, events.jsonl, logs/
                        # (git worktrees in workspaces/ are preserved)
```

---

## Linear board configuration

`resonance setup` creates the required workflow states, but **Linear places new custom states in "Hidden columns" on the board by default.** This is the most common reason new operators can't see the pipeline in action.

**How to unhide:**
1. Open your team board in Linear (the kanban/board view, not the list view).
2. On the right side of the board, click **"Hidden columns"**.
3. Toggle on: **Plan Approved**, **Agent Feedback Needed**, **Human Review**.

Your board should then show (left to right):

```
Todo  |  Plan Approved  |  In Progress  |  Agent Feedback Needed  |  Human Review  |  Done
```

**Verify with `resonance doctor`:** after toggling visibility, run `resonance doctor` to confirm the states are accessible via the API. If any state shows as missing, run `resonance setup` again to recreate it.

---

## How the orchestrator detects issues

The orchestrator runs a poll loop on a 15-second interval (configurable in `WORKFLOW.md` under `polling.interval_seconds`).

Each tick:
1. Queries the Linear team for issues whose workflow state is exactly "Plan Approved".
2. Skips issues that already have an active local run (running, paused, or waiting_human).
3. For each new eligible issue, checks concurrency limits (default: 2 parallel runs max).
4. **Fail-closed re-verification**: before starting any work, re-fetches the issue from Linear and confirms the state is still "Plan Approved". If it has changed since the poll (e.g., someone moved it back), the issue is skipped. This prevents acting on stale state.
5. Classifies the issue by label (see below), creates the worktree, updates Linear to "In Progress", and launches the Claude process.

Every 120 seconds (configurable under `polling.reconcile_interval_seconds`), the orchestrator also reconciles active local runs against Linear state. If an issue has been moved to Done, Cancelled, or Todo in Linear, the local run is stopped and archived.

---

## How agents know what to do

**Label-to-task-type mapping** (from `WORKFLOW.md`). Classification priority: `pep` → `core-plan` → `block` → all other types.

| Label(s) on the issue | Task type | Agent | Notes |
|---|---|---|---|
| `pep` | pep | PEP Reader Agent (claude-opus) | Reads PEP, creates Core Plan issue |
| `core-plan` | core_plan | Block Decomposer Agent (claude-opus) | Creates Block sub-issues with dependencies |
| `block` | block | Block Execution Agent (claude-sonnet) | Implements work in shared worktree |
| `frontend` (no `bug`) | frontend_feature | Frontend Engineer | New UI feature |
| `frontend` + `bug` | frontend_bug | Frontend Engineer | UI regression fix |
| `design` | design_to_code | Frontend Engineer | Figma → component; requires FIGMA_API_KEY |
| `backend` (no `bug`) | backend_feature | Backend Engineer | New API/service |
| `backend` + `bug` | backend_bug | Backend Engineer | Backend regression fix |

Issues with no recognized label combination are rejected without starting: Resonance posts a comment explaining supported labels and returns the issue to Todo.

**The prompt** sent to the agent contains:
- Issue identifier and title
- Task type and iteration number
- Full issue description (this is where your spec lives — write it clearly)
- Prior feedback history (on retries or after `resonance feedback`)
- Required artifacts the agent must produce before signalling ready
- The AGENT_SIGNAL protocol

**The AGENT_SIGNAL protocol:** Resonance monitors the agent's stdout for lines matching:
```
AGENT_SIGNAL: {"type": "...", ...}
```

Two signal types are recognized:

```json
AGENT_SIGNAL: {"type": "human_input_needed", "question": "Should I use the design system button or a custom one?", "context": "The spec mentions both"}
```
Effect: run pauses, Linear moves to "Agent Feedback Needed", comment posted with the question.

```json
AGENT_SIGNAL: {"type": "ready_for_review", "summary": "Built the header component with responsive breakpoints", "artifacts": {"preview_url": "http://localhost:3001"}}
```
Effect: run completes, Linear moves to "Human Review", comment posted with summary and preview URL.

If the agent exits without emitting a signal, the orchestrator treats it as a failure and retries (up to `retry.max_attempts`, default 3).

---

## The full flow

Resonance follows a three-tier flow: PEP → Core Plan → Blocks. Every project starts with a PEP; direct block-level execution (for ad-hoc tasks) is also supported.

### Starting a project with a PEP (recommended)

**Step 1 — Write a PEP** (Human Gate 1)

Create an issue in your Linear project:
- Title: `[PEP] Your feature name`
- Label: `pep`
- Description: product brief — Goal, Acceptance Criteria, and a rough block breakdown (see `docs/pep-template.md` or run `/create-pep` in Claude Code)

Move it to **Plan Approved** when ready.

**Step 2 — PEP Reader runs (3–7 min)**

Resonance picks up the PEP within 15 seconds, launches the PEP Reader Agent. Watch the TUI event stream for `agent_action` events as it works.

Result: one **Core Plan** issue appears in **Human Review** with a full block breakdown and acceptance criteria. The PEP moves to Done.

**Step 3 — Review the Core Plan** (Human Gate 2)

Open the Core Plan issue in Linear. Read the planned blocks — edit titles, descriptions, or criteria if needed. When satisfied, move to **Plan Approved**.

**Step 4 — Block Decomposer runs (5–12 min)**

Resonance creates one Block sub-issue per block with Linear blocking relations (B2 blocked by B1, etc.).

**Step 5 — Blocks execute automatically (10–30 min each)**

Blocks run in dependency order. Each block agent:
- Works in the **shared worktree** `workspaces/{project-slug}/main/` — all blocks build on the same codebase
- Updates Linear checklist items live as tasks complete
- Posts "✅ Block complete" comment with branch link when done
- Pushes the branch to GitHub (if `GITHUB_TOKEN` is set)

You watch progress in the TUI.

**Step 6 — Review the output** (Human Gate 3)

When all blocks are Done, the Core Plan moves to **Human Review**:

```bash
resonance attach RND-51     # get worktree path and log file
# open workspaces/{project-slug}/main/ — or review on GitHub
```

Move the Core Plan to **Done** when satisfied. Resonance cleans up the workspace on its next reconcile.

---

### Running a standalone block (ad-hoc)

For single tasks that don't need a PEP/Core Plan:

1. Create a Linear issue with a task label (`frontend`, `backend`, `design`, or with `bug`).
2. Move to **Plan Approved**.
3. Resonance picks it up and runs a Block Execution Agent directly.

---

## Monitoring

### Quick status

```bash
resonance status              # all runs: status, task type, attempt, last event time
resonance status RND-123      # single run: all fields including log file path
resonance logs RND-123        # recent events from events.jsonl filtered to this issue
```

Status values: `running`, `waiting_human`, `paused`, `complete`, `failed`, `archived`.

### Attach

```bash
resonance attach RND-123
```

Prints the worktree path and log file path for a run. Use this to navigate to the worktree or tail the log file manually:

```bash
cd workspaces/D2D-Demo-gorgon/main
tail -f runs/logs/RND-123-20260428T143200.log
```

### Event stream

The orchestrator appends all lifecycle events to `runs/events.jsonl`. This file is the source of truth for what happened and when.

```bash
tail -f runs/events.jsonl
```

Each line is a JSON object with at minimum `ts` (ISO timestamp), `issue` (issue ID or "system"), and `type` (event type). `resonance logs RND-123` reads this file and filters by issue ID.

### Debug tracing

For deep investigation, enable full e2e tracing from the TUI:

- Press `s` → toggle **Enable debug tracing** → Enter to save
- Press `t` to open the trace viewer (newest-first, Enter for full event detail)

Or query the trace file directly:
```bash
cat runs/traces/session-*.jsonl | jq 'select(.cat=="mcp")'    # MCP tool calls
cat runs/traces/session-*.jsonl | jq 'select(.cat=="linear")' # Linear API calls
cat runs/traces/session-*.jsonl | jq 'select(.cat=="pipeline")' # routing decisions
```

Trace categories: **mcp** (full tool inputs/outputs from agents), **linear** (API calls + response + timing), **agent** (full reasoning text), **pipeline** (task routing, dependency checks, state transitions).

Settings are persisted to `runs/debug-settings.json`. Trace files are written to `runs/traces/` and are **not** cleared by the TUI cleanup action.

### Run state file

```bash
cat runs/state.json
```

JSON object keyed by issue ID. Each entry holds the current run state: status, PID, worktree, log file, iteration, attempt, artifacts, feedback history, pending question. This file is the authoritative source for the orchestrator — `resonance status` reads from it.

---

## Human control reference

### Approve

```bash
resonance approve RND-123
```

Resumes a run in `waiting_human` or `paused` status. Use this when:
- The agent emitted `human_input_needed` and you want to let it proceed without adding feedback.
- You paused a run with `resonance pause` and want to restart it.

The orchestrator picks up the approve command on its next tick, starts a new iteration with any accumulated feedback, and moves the Linear issue back to In Progress.

### Send feedback

```bash
resonance feedback RND-123 "Use the primary button variant, not outlined"
```

Queues feedback text to be injected into the agent's next iteration prompt. The run does not need to be in `waiting_human` — you can send feedback at any time. Feedback accumulates and is included in the Prior Feedback section of the next prompt.

When the run is waiting and you send feedback, also run `resonance approve RND-123` to resume it. Feedback alone queues the text but does not restart the run.

### Pause

```bash
resonance pause RND-123
```

Sends a pause command to the orchestrator. The Claude subprocess is killed cleanly. The run moves to `paused` status in `runs/state.json`. The Linear issue remains In Progress (to prevent another run from being started by the next poll).

Resume with `resonance approve RND-123`.

### Abort

```bash
resonance abort RND-123        # prompts for confirmation
resonance abort RND-123 --yes  # skip confirmation
```

Permanently stops the run. The Claude subprocess is killed. The run is marked `failed` in `runs/state.json` with reason "aborted by operator". The git worktree is preserved in `workspaces/RND/RND-123/` for inspection.

Linear is not automatically updated on abort — move the issue state manually if needed.

Use abort when a run has gone wrong and you want to start fresh. To restart, move the issue back to Plan Approved in Linear and let the orchestrator pick it up as a new run.

### Checkpoint

```bash
resonance checkpoint RND-123          # write RESONANCE.md to worktree
resonance checkpoint RND-123 --push   # write RESONANCE.md and push branch to GitHub
```

Writes a `RESONANCE.md` file to the issue's worktree root with the current status, progress, and resume instructions. Resonance writes this automatically on pause and Human Review transitions — use `checkpoint` to trigger it manually, or before handing off to a different machine.

`--push` runs `git push -u origin agent/RND-123` from the worktree. Use when you need the checkpoint accessible from another machine via `git show agent/RND-123:RESONANCE.md`.

---

## Human takeover

When you want to continue where Resonance left off — either because it produced partial work or hit max attempts — use the cc-resonance Claude Code plugin commands.

### Starting a new project (PEP)

In any Claude Code session:
```
/create-pep "Project Title"
```
Walks through an interview, formats the PEP, and creates the `[PEP] Title` Linear project and issue. Move the issue to Plan Approved when satisfied.

### Loading context in a fresh session

```
/reso RND-123
```
Fetches the issue hierarchy (Block → Plan → PEP), all comments, local memory, and `RESONANCE.md`. Works from any terminal — no local Resonance run required.

### Taking over a running issue

```bash
resonance pause RND-123     # stop the orchestrator run
```

Then in Claude Code:
```
/reso-takeover RND-123
```

Posts `[HUMAN TAKEOVER]` to Linear, loads full context, and shows you the worktree path to work in. The paused status prevents the orchestrator from restarting on the next poll.

### Handing back

When you're done working:
```
/reso-handback "what you did"
```

Commits uncommitted work, updates `RESONANCE.md`, posts `[HUMAN HANDBACK]` to Linear, and asks where to move the issue state. To resume Resonance afterwards:

```bash
resonance approve RND-123
```

---

## Troubleshooting

### PEP not picked up

**Symptom:** PEP issue is in Plan Approved but Resonance ignores it.

**Checks:**
1. The issue must have the label `pep` (case-sensitive). Verify in Linear.
2. `LINEAR_TEAM_ID` matches the team. Run `resonance doctor`.
3. `LINEAR_PROJECT_ID` is set to the correct project. Run `./onair.sh --project <url>` to scope correctly.

### Blocks running in wrong order

**Symptom:** B2 or B3 ran before its predecessor was Done.

**Cause:** The Block Decomposer Agent did not emit `blocked_by_ids` in its `blocks_created` signal, so the orchestrator never created Linear blocking relations.

**Check:**
```bash
cat runs/traces/session-*.jsonl | jq 'select(.type=="agent_signal") | .signal'
```
Look for the `blocks_created` signal. If `blocked_by_ids` is empty for every block, the Block Decomposer prompt needs attention.

**Fix:** Re-run the Core Plan (move back to Plan Approved). Enable debug tracing first (`s` in TUI) to capture the full signal.

### Checkboxes not updating in Linear

**Symptom:** Block agent runs successfully but the Linear issue description checkboxes stay unchecked.

**Cause:** The `linear-mcp` schema is missing the `description` field in `linear_bulk_update_issues`. The wizard auto-patches this.

**Fix:**
```bash
./wizard.sh check   # re-applies the description field patch to tool.types.js
```

### Issue not picked up

**Symptom:** Issue is in Plan Approved but orchestrator ignores it.

**Checks:**
1. State name is case-sensitive. Confirm the issue is in the state named exactly "Plan Approved" — not a label, not a comment.
2. Issue has a recognized label (`pep`, `core-plan`, `block`, `frontend`, `frontend`+`bug`, `design`, `backend`, or `backend`+`bug`).
3. `LINEAR_TEAM_ID` matches the team the issue belongs to. Run `resonance doctor` to verify.
4. Orchestrator is running. Check `./onair.sh` output or `resonance status`.
5. Concurrency limit: if 2 runs are already active, new issues are queued until a slot opens.
6. Check `runs/events.jsonl` for recent `poll_cycle` events:
   ```bash
   grep '"type":"poll' runs/events.jsonl | tail -5
   ```

### YAML/module not found error on startup

**Symptom:** `./onair.sh` or `python -m orchestrator.main` fails with `ModuleNotFoundError` or YAML parse error.

**Fix for missing modules:**
```bash
pip install -e .
```

**Fix for YAML parse error:** `resonance doctor` will flag this. Open `WORKFLOW.md` and check for syntax errors — it must be valid YAML. Run `python3 -c "import yaml; yaml.safe_load(open('WORKFLOW.md'))"` to pinpoint the error.

### `claude` not found

**Symptom:** `onair.sh` fails with "claude CLI not found".

**Fix:** Install Claude Code from https://claude.ai/code, then authenticate:
```bash
claude auth login
```
Confirm with `claude --version`.

### States not visible on the Linear board

**Symptom:** Plan Approved / Agent Feedback Needed / Human Review columns don't appear on the board.

**Fix:** They exist but are hidden. On the team board in Linear, click "Hidden columns" on the right side and enable the three states. See the "Linear board configuration" section above.

If `resonance doctor` reports a state as missing (not just hidden), run `resonance setup` to recreate it.

### Worker exits immediately with no signal

**Symptom:** Run appears, moves to In Progress, then immediately fails. `resonance status RND-123` shows `failed`.

**Check the log:**
```bash
resonance attach RND-123   # get the log file path
tail -100 runs/logs/RND-123-*.log
```

**Common causes:**
- Claude CLI not authenticated: `claude auth login`
- Missing `--permission-mode acceptEdits` — this flag is set in the runner; if you see a permissions prompt error, check that the CLI version supports it
- Import error in orchestrator code: `pip install -e .` to reinstall

### Run stalls (no new events for a long time)

**Symptom:** Run is `running` but `resonance logs RND-123` shows no new events for many minutes.

The orchestrator has a stall detector: if the Claude process produces no output for 30 minutes (configurable under `retry.on_stall_minutes` in `WORKFLOW.md`), the process is killed and the run is retried automatically.

To intervene manually before the timeout:
```bash
resonance abort RND-123 --yes
# Then move the Linear issue back to Plan Approved to start a fresh run
```

### Max attempts reached

**Symptom:** `resonance status RND-123` shows `failed` after 3 attempts.

The orchestrator gave up. Review the last log to understand what went wrong. Options:
- If the output looks acceptable: move the Linear issue back through Plan Approved to trigger a fresh run, and use `resonance approve` after the agent signals.
- If the spec needs clarification: edit the issue description in Linear, then move back to Plan Approved.
- The retry counter resets on each new run (new entry in state.json after re-pickup).

---

## Configuration reference

All runtime behaviour is controlled by `WORKFLOW.md`. Changes take effect on the next orchestrator restart (`Ctrl+C` then `./onair.sh`).

Key settings:

| Setting | Location in WORKFLOW.md | Default |
|---|---|---|
| Poll interval | `polling.interval_seconds` | 60 |
| Reconcile interval | `polling.reconcile_interval_seconds` | 120 |
| Max parallel runs | `concurrency.max_parallel_runs` | 2 |
| Max retries per run | `retry.max_attempts` | 3 |
| Stall timeout | `retry.on_stall_minutes` | 30 |
| Max iterations (frontend_feature) | `task_types.frontend_feature.max_iterations` | 3 |
| Max iterations (design_to_code) | `task_types.design_to_code.max_iterations` | 5 |
| Workspace base dir | `workspace.base_dir` | workspaces/ |
| State file | `run_state.state_file` | runs/state.json |
| Event log | `run_state.event_log` | runs/events.jsonl |

---

## Recovery

### Restart the orchestrator

`Ctrl+C` in the terminal running `./onair.sh`, then:
```bash
./onair.sh
```

On startup, the orchestrator reads `runs/state.json`. Runs that were `running` when the orchestrator stopped are detected by reconciliation on the next cycle — if the Linear state is still In Progress, they will be retried as new attempts (subject to `retry.max_attempts`).

Workspaces in `workspaces/` are preserved across restarts.

### Stuck run (dead PID, status still "running")

If the orchestrator crashed hard without updating state, a run may appear stuck as `running` with a process that no longer exists.

**Fix:**
```bash
# Back up state
cp runs/state.json runs/state.json.bak

# Inspect
python3 -c "import json; d=json.load(open('runs/state.json')); [print(k, d[k]['status'], d[k].get('pid')) for k in d]"

# Edit state.json manually — change the stuck run's status from "running" to "failed"
# Use your preferred editor; the file is plain JSON
```

After editing, restart the orchestrator. It will not attempt to re-run the failed entry unless the issue is moved back to Plan Approved in Linear.

### Full reset

To clear all runtime state and start clean:

```bash
# Stop the orchestrator
# (Ctrl+C in the onair.sh terminal)

# Abort any orphaned worktrees
ls workspaces/
# For each: git worktree remove workspaces/RND/RND-123 --force

# Clear runtime state
rm -f runs/state.json runs/events.jsonl runs/commands.jsonl
rm -rf runs/logs/

# Restart
./onair.sh
```

Note: this does not touch Linear state. Issues remain wherever they were. Move them manually in Linear as needed — typically back to Todo or Plan Approved.
