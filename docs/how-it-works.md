# How Resonance Works

Technical reference for the implemented system. Target audience: a developer joining the project who wants to understand the full picture in one read.

---

## Overview

```mermaid
flowchart TD
    Human["Human (Linear)"]
    Linear["Linear\n(issue state + comments)"]
    Orchestrator["Orchestrator\n(poller.py loop)"]
    Runner["Runner\n(claude -p subprocess)"]
    State["runs/state.json\nruns/events.jsonl\nruns/commands.jsonl"]
    TUI["TUI Dashboard\n(tui/app.py)"]

    Human -->|"moves issue to Plan Approved"| Linear
    Orchestrator -->|"polls every 15s"| Linear
    Orchestrator -->|"starts"| Runner
    Runner -->|"emits AGENT_SIGNAL"| Orchestrator
    Orchestrator -->|"state transitions + comments"| Linear
    Orchestrator -->|"writes"| State
    TUI -->|"reads"| State
    TUI -->|"reads Linear pipeline"| Linear
    Human -->|"approve / feedback / abort via TUI or CLI"| State
    Orchestrator -->|"reads commands"| State
```

The orchestrator is a blocking loop started by `./onair.sh` and run in the background. The TUI is a Textual application in the foreground of the same shell. They share no in-process state — all coordination goes through files in `runs/`.

---

## The Four Layers

### 1. Linear — intent layer

Linear holds the canonical state of every issue. The orchestrator reads from and writes to Linear but never treats its own local state as more authoritative than what Linear says. Key operations:

- **Polling**: `get_eligible_issues()` queries issues in the configured `eligibility_state` (default: "Plan Approved").
- **Fail-closed re-check**: before starting any run, `get_issue()` re-fetches the issue to confirm the state hasn't changed since the poll.
- **State transitions**: `set_issue_state()` moves issues through In Progress → Agent Feedback Needed → Human Review → Done/Todo.
- **Comments**: `post_comment()` posts structured updates at key lifecycle moments (run start for plan issues, human_input_needed, ready_for_review, retry, failure).
- **Feedback extraction**: `get_issue_with_comments()` fetches all comments when resuming after Human Review; new comments since the last check are injected as feedback.

All API calls go to `https://api.linear.app/graphql`. The client uses `httpx` with a 30-second timeout. State names are resolved to UUIDs and cached per team.

### 2. Orchestrator — execution layer

The main loop is `Poller.run_forever()` in `orchestrator/poller.py`. Each tick (`_tick()`) runs four steps in order:

1. `_advance_runners()` — polls all active `Runner` objects. If a runner has finished, removes it from the active dict and calls `_handle_result()`.
2. `_process_commands()` — reads `runs/commands.jsonl` for pause/abort/feedback/approve commands written by the CLI or TUI.
3. `_check_human_feedback_resumes()` — scans runs in `waiting_human` or `needs_input` status. If the Linear state is "Agent Feedback Needed", extracts new comments and calls `_retry_run()`.
4. Fetch new eligible issues from Linear and start runs if concurrency slots are available.

Every `reconcile_interval_seconds` (default: 120s), `_reconcile()` cross-checks all active local runs against Linear. If an issue has moved to Done or Cancelled, the local run is stopped and archived, and the worktree is removed.

### 3. Claude CLI workers — agent layer

Each run is a `Runner` instance. `Runner.start()` builds the `claude` command and launches it with `subprocess.Popen`:

```
claude -p "<prompt>" \
  --output-format stream-json \
  --verbose \
  --permission-mode bypassPermissions \
  --name agent-<issue-id>-iter<N> \
  --plugin-dir ../../.claude/cc-pipeline \
  --plugin-dir ../../.claude/cc-qo-skills \
  --mcp-config ../../.mcp.json
```

The process runs in the worktree directory (`workspaces/<issue-id>/`). stdout is merged with stderr and consumed by a background thread (`_consume_stdout`). Every line is:
- Attempted as stream-json parse. Text events and tool events are forwarded to the event log.
- Scanned for `AGENT_SIGNAL:` via regex regardless of whether JSON parsing succeeded.

`Runner.poll()` returns a `RunResult` when the process exits (detected by the `_done` threading event being set by the stdout consumer). The result carries the last signal seen and any artifacts extracted from it.

Stall detection: `is_stalled(stall_seconds)` compares `time.monotonic()` against `_last_output_at`. The poller kills and retries stalled runners.

**Plan issues** receive a different prompt from `orchestrator/planner.py`. The Planning Agent uses the Linear MCP tools to create phase issues, moves them to Plan Approved, writes a `plan.md` to local memory, posts a summary comment on the parent, and emits `plan_decomposed`.

**Execution issues** receive the prompt from `runner.build_prompt()`. The prompt contains: issue title/description, task type, iteration number, required artifacts list, the handoff protocol (where to write `runs/memory/<issue-id>/handoffs/iter-N.md`), instructions to update the Linear issue description and post a structured review comment before signalling, and the AGENT_SIGNAL specification.

On retry (`_retry_run()`), the prompt also includes `prior_feedback` (all accumulated feedback texts) and a `memory_brief` string loaded from `runs/memory/<issue-id>/` by `orchestrator/memory.py`.

### 4. TUI dashboard — observation layer

`tui/app.py` is a Textual application (`ResonanceDashboard`). It reads `runs/state.json` and `runs/events.jsonl` on a 2-second refresh interval, and polls Linear independently on a 30-second background thread (`_LinearPoller`).

The layout is fixed:
- **Header bar** (1 line): orchestrator health (checks PID file), running/waiting/failed counts.
- **Attention section** (hidden when empty): items requiring human action — runs in `waiting_human` and Linear issues in Human Review state.
- **Active Runs table**: all runs with status `running`, `waiting_human`, `needs_input`, or `paused`. Shows issue ID, status with spinner for running, task type, attempt counter, detail text, elapsed time.
- **Linear Pipeline table**: issues fetched from Linear in any active pipeline state. Sorted by pipeline order (In Progress first, then Agent Feedback Needed, Human Review, Plan Approved).
- **Performance section**: success rate gauge, completed/failed/retried counts over 24h, 12-hour sparkline of run starts, average run duration.
- **Event Stream**: last 60 events from `runs/events.jsonl`, color-coded by event type. Toggle to raw log view with `v`.

All actions (approve, feedback, abort) write to `runs/commands.jsonl` via `orchestrator.state.post_command()`. The orchestrator picks them up on its next tick.

---

## Workflow States (Linear)

| State | Who transitions to it | Orchestrator behavior on seeing it |
|---|---|---|
| Todo | Human / orchestrator on failure | Not eligible — ignored |
| Ready for Planning | Human | Not eligible — ignored |
| Plan Proposed | Human / agent | Not eligible — ignored |
| Plan Approved | Human | **Eligible** — orchestrator picks up on next poll |
| In Progress | Orchestrator | Run is active — no new run started |
| Agent Feedback Needed | Orchestrator (on `human_input_needed`) or human (to resume after Human Review) | Checked by `_check_human_feedback_resumes`; if a local run is in `waiting_human`/`needs_input`, extracts new comments and resumes |
| Human Review | Orchestrator (on `ready_for_review`) | Local run in `waiting_human`; no automatic action — human must accept or send feedback |
| Done | Human | Reconciliation stops the local run and removes the worktree |
| Cancelled | Human | Reconciliation stops the local run and removes the worktree |

---

## Issue Labels

Labels are applied in Linear before moving an issue to Plan Approved. They determine task type, which controls the agent's skills, MCP servers, and required artifacts.

| Label(s) | Task type | Worker | Key skills | Required artifacts |
|---|---|---|---|---|
| `plan` | plan | claude-opus | Linear MCP | (signal: plan_decomposed) |
| `design` | design_to_code | claude-sonnet | connectui-dev, pd-pep, pd-plan-post | preview_url, figma_comparison |
| `frontend` (no `bug`) | frontend_feature | claude-sonnet | connectui-dev, pd-pep, pd-plan-post | preview_url |
| `frontend` + `bug` | frontend_bug | claude-sonnet | connectui-dev, pd-pep | preview_url, before_after_evidence |
| `backend` (no `bug`) | backend_feature | claude-sonnet | pd-pep, pd-plan-post | test_output |
| `backend` + `bug` | backend_bug | claude-sonnet | pd-pep | test_output |

The `RES` label is added automatically by the orchestrator when a run starts. It marks issues under orchestrator management.

Issues with no recognized label combination cause the orchestrator to post a comment explaining supported labels and return the issue to Todo.

---

## Run Lifecycle

### Plan issues

1. Issue with `plan` label appears in Plan Approved.
2. Orchestrator classifies as `plan`, builds the planning prompt (`build_planning_prompt()`), sets Linear → In Progress, adds `RES` label, posts a "Planning Agent started" comment.
3. Planning Agent runs in a worktree. It uses `mcp__linear__linear_create_issue` to create one issue per phase (child of the plan issue), writes `runs/memory/<issue-id>/plan.md`, posts a summary comment listing all phase identifiers, bulk-moves all phase issues to Plan Approved.
4. Agent emits: `AGENT_SIGNAL: {"type": "plan_decomposed", "plan_id": "...", "phases": [...]}`
5. Orchestrator: local run → `complete`, plan issue → Done in Linear, phases get picked up automatically on subsequent polls.

### Execution issues

1. Issue with a recognized non-`plan` label appears in Plan Approved.
2. Orchestrator classifies task type, creates worktree (`workspaces/<issue-id>/`), writes `.claude/settings.json`, sets Linear → In Progress, adds `RES` label.
3. Agent runs. Before signalling, it is instructed to: update the Linear issue description (check off completed acceptance criteria, append a Work Summary), post a structured review comment to Linear.
4. Two outcomes:
   - **Needs input**: agent emits `human_input_needed`. Local run → `needs_input`. Linear → Agent Feedback Needed. Comment posted with question.
   - **Ready**: agent emits `ready_for_review`. Local run → `waiting_human`. Linear → Human Review. Comment posted with summary and preview URL.
5. If `needs_input`: human adds a comment in Linear and moves the issue to Agent Feedback Needed. On next tick, `_check_human_feedback_resumes` detects the state, extracts new comments as feedback, posts an acknowledgement comment, calls `_retry_run()` to start a new iteration.
6. If `waiting_human` (Human Review): human reviews the branch. To accept, move to Done. To request changes, add a comment in Linear and move to Agent Feedback Needed — the orchestrator detects this the same as step 5.
7. On Done: reconciliation kills any active runner (if applicable), archives the local run, removes the worktree.

### Needs Input blocker flow (mid-task)

The `human_input_needed` signal can fire at any point during agent execution, not only at the end. The agent emits it, the runner records it as `_last_signal`, and when the process exits (because the agent stops after asking), `_handle_result` routes to the needs_input path. The run remains in `needs_input` status until the human moves the Linear issue to Agent Feedback Needed.

---

## AGENT_SIGNAL Protocol

The runner scans all output with:
```python
SIGNAL_PATTERN = re.compile(r"AGENT_SIGNAL:\s*(\{.*\})")
```

This runs on every line regardless of whether the line is valid stream-json. The last signal seen before process exit is what `_handle_result` acts on.

| Signal | Fields | Orchestrator action |
|---|---|---|
| `human_input_needed` | `question` (str), `context` (str) | `run_state.update_run(status="needs_input", pending_question=...)` → on exit: Linear → Agent Feedback Needed, comment posted |
| `ready_for_review` | `summary` (str), `artifacts` (dict with `preview_url` etc.) | `run_state.update_run(status="waiting_human", artifacts=...)` → on exit: Linear → Human Review, comment posted |
| `plan_decomposed` | `plan_id` (str), `phases` (list of `{id, identifier, title}`) | Local run → `complete`, issue → Done in Linear, phases written to memory |

The signal is handled in two places: `Runner._handle_signal()` updates local run state immediately when the signal is detected mid-stream; `Poller._handle_result()` drives the Linear state transition after the process exits.

---

## Run Status State Machine

All statuses are stored per-issue in `runs/state.json`. The file is written atomically (written to `.tmp` then renamed).

| Status | Meaning |
|---|---|
| `running` | Claude subprocess is active |
| `paused` | Subprocess was killed by `pause` command; Linear still shows In Progress |
| `waiting_human` | Agent emitted `ready_for_review`; Linear shows Human Review |
| `needs_input` | Agent emitted `human_input_needed`; Linear shows Agent Feedback Needed |
| `failed` | Max attempts reached, or aborted by operator |
| `complete` | Plan decomposition succeeded cleanly |
| `archived` | Run reconciled-stopped because Linear moved to Done/Cancelled |

`ACTIVE_STATUSES = {"running", "paused", "waiting_human", "needs_input"}` — runs in these states are shown in the TUI and processed by the orchestrator.

`TERMINAL_STATUSES = {"failed", "complete", "archived"}` — these are cleared by the `c` (cleanup) action in the TUI.

Valid transitions:

```
(created) → running
running → waiting_human   (ready_for_review signal)
running → needs_input     (human_input_needed signal)
running → paused          (pause command)
running → failed          (max attempts, abort, linear state error)
running → complete        (plan_decomposed signal)
waiting_human → running   (approve command or Human Review → Agent Feedback Needed detected)
needs_input → running     (Agent Feedback Needed detected in Linear)
paused → running          (approve command)
running/waiting_human/paused → archived   (reconciliation: Linear moved to Done/Cancelled)
```

---

## Worker Session Setup

For each new run, `WorkspaceManager.create()` does the following:

1. Creates the worktree:
   ```bash
   git worktree add -b agent/<issue-id> workspaces/<issue-id> HEAD
   ```
   If the branch already exists (from a prior attempt), falls back to:
   ```bash
   git worktree add workspaces/<issue-id> agent/<issue-id>
   ```

2. Writes `workspaces/<issue-id>/.claude/settings.json`:
   ```json
   {
     "pluginDirs": [
       "../../.claude/cc-pipeline",
       "../../.claude/cc-qo-skills"
     ],
     "mcpConfig": "../../.mcp.json",
     "permissions": {
       "allow": ["mcp__*", "Bash(*)", "Read(*)", "Write(*)", "Edit(*)",
                 "MultiEdit(*)", "Glob(*)", "Grep(*)", "WebSearch(*)",
                 "WebFetch(*)", "TodoWrite(*)"]
     },
     "env": {
       "ISSUE_ID": "<issue-id>"
     }
   }
   ```

3. The `claude` command adds `--permission-mode bypassPermissions`, so the agent operates without interactive permission prompts.

The plugin dirs point at the shared `cc-pipeline` and `cc-qo-skills` directories relative to the worktree root. The MCP config (`../../.mcp.json`) connects the Linear, Context7, and Figma MCP servers to the agent session.

Worktrees are removed when the issue reaches Done or Cancelled (detected by `_reconcile()`). They are also removed explicitly on `resonance abort` if the `--cleanup` flag is passed (the abort command marks the run failed; the worktree itself is left for inspection by default).

---

## TUI Reference

The TUI is started by `./onair.sh` as `python -m tui.app`. It runs in the foreground; the orchestrator runs in the background with its PID written to `runs/orchestrator.pid`.

### Dashboard sections

**Header bar** (1 line, always visible)
Shows orchestrator health (`● orch` green/red based on PID file), count of running runs, count of waiting runs, count of failed runs.

**Attention section** (hidden when empty)
Appears when human action is needed. Entries: local runs in `waiting_human` (shows pending question), and Linear issues in Human Review state (shows title). Suggested keyboard actions shown inline.

**Active Runs table**
All runs with an active status. Columns: issue ID (with `>` prefix if selected), status (with spinner for running), task type, attempt/max (e.g. `1/3`), detail text (branch or wait reason), elapsed time since start. If a run has a `pending_question`, it appears on the row below in yellow.

**Linear Pipeline table**
Issues from Linear in any pipeline state (Plan Approved, In Progress, Agent Feedback Needed, Human Review). Sorted: In Progress first, then Agent Feedback Needed, Human Review, Plan Approved. Polled every 30 seconds in a background thread. Shows identifier, truncated title, state with color, assignee, last updated time. Scoped to `LINEAR_PROJECT_ID` if set; otherwise shows all team issues.

**Performance section**
24-hour window. Shows: success rate gauge (green/yellow/red), completed/failed/retried counts, average run duration. 12-hour sparkline of run starts per hour (oldest left, newest right). Only appears after the first completed run.

**Event Stream / Log viewer**
Last 60 events from `runs/events.jsonl`, excluding system startup/shutdown events. Color-coded: red for failures, green for completions, yellow for waiting/paused/feedback, cyan for starts. Press `v` to toggle to raw log view (last 60 lines of the selected run's log file).

### Keyboard bindings

| Key | Action | Notes |
|---|---|---|
| `q` | Quit | Also stops the orchestrator if this TUI started it |
| `r` | Refresh | Re-reads state.json and events.jsonl |
| `l` | Linear refresh | Triggers immediate background Linear poll |
| `p` | Set project | Opens modal; accepts Linear project URL or UUID |
| `Tab` | Select next run | Cycles through active runs |
| `Enter` | Run detail | Opens modal with full run info, artifacts, handoff, manual control commands |
| `f` | Send feedback | Opens modal; queues feedback to `runs/commands.jsonl` |
| `a` | Approve | Resumes selected run in `waiting_human` status |
| `x` | Abort | Stops selected run permanently |
| `v` | Toggle log | Switches event stream to raw log view for selected run |
| `c` | Cleanup | Clears failed/complete/archived runs and event log (with confirmation) |
| `d` | Demo | Creates a plan issue in Linear for end-to-end walkthrough |
| `e` | Event browser | Full scrollable event history (last 300 events) |
| `?` | Help | Full help screen with workflow explanation |

### Run detail modal

Opened with `Enter`. Shows: issue ID, status, task type, iteration, Linear URL, artifacts (with preview URL), latest handoff file contents (from `runs/memory/<issue-id>/handoffs/iter-N.md`), pending question or review instructions, branch/worktree/log paths, and the manual control commands:
```
cd workspaces/<issue-id> && claude
/pd-issue <issue-id>
```

---

## Configuration Reference

`WORKFLOW.md` is parsed as YAML by `orchestrator/config.py` at startup. No changes take effect without restarting the orchestrator. State names can be overridden via environment variables (e.g. `LINEAR_STATE_ELIGIBILITY`), which take precedence over `WORKFLOW.md` values.

### Key settings and their effects

| Setting | Path in WORKFLOW.md | Default | Effect |
|---|---|---|---|
| Eligibility state | `linear.eligibility_state` | `Plan Approved` | The Linear state name the orchestrator polls for |
| Poll interval | `polling.interval_seconds` | 15 | How often the main loop queries Linear for new issues |
| Reconcile interval | `polling.reconcile_interval_seconds` | 120 | How often active local runs are validated against Linear state |
| Max parallel runs | `concurrency.max_parallel_runs` | 2 | Maximum simultaneous Claude subprocesses |
| Max per issue | `concurrency.max_runs_per_issue` | 1 | Prevents duplicate workers for the same issue |
| Max attempts | `retry.max_attempts` | 3 | How many times the orchestrator will retry before giving up |
| Backoff | `retry.backoff_seconds` | `[5, 15, 60]` | Wait times between retry attempts |
| Stall timeout | `retry.on_stall_minutes` | 30 | Minutes of no output before the subprocess is killed and retried |
| Workspace dir | `workspace.base_dir` | `workspaces/` | Root directory for all git worktrees |
| Branch naming | `workspace.branch_naming` | `agent/{issue_id}` | Git branch pattern per worktree |
| Cleanup on | `workspace.cleanup_on` | `[Done, Cancelled]` | Linear states that trigger worktree removal |
| Plugin dirs | `workspace.agent_config.plugin_dirs` | `[cc-pipeline, cc-qo-skills]` | Relative paths from worktree to plugin directories |
| Worker runtime | `worker.runtime` | `claude_cli` | Currently the only supported runtime |
| Default model | `worker.default` | `claude-sonnet` | Overridable per task type |

### Task type configuration

Each task type block under `task_types:` controls:
- `detection.labels` / `detection.excludes`: which label combinations match
- `worker`: model override (e.g., `plan` uses `claude-opus`)
- `mcp`: which MCP servers to connect (always includes `linear`; `figma` optional)
- `skills`: list of cc-pipeline/cc-qo-skills skill names injected into the prompt context
- `artifacts_required`: artifacts the agent must produce; listed in the prompt
- `verify_level`: L1 (build+lint) or L2 (build+lint+tests) — referenced in the prompt
- `max_iterations`: maximum feedback/retry cycles

Adding a new task type requires only a new YAML block — no Python changes.

---

## Retry and Failure Handling

When a runner finishes without a `ready_for_review` signal, `_handle_failure()` checks the attempt counter:

- **Attempt < max_attempts**: posts a retry comment to Linear ("Attempt N failed — retrying in Xs"), sleeps for the backoff duration (`backoff_seconds[attempt-1]`), calls `_retry_run()`.
- **Attempt >= max_attempts**: local run → `failed`, posts a failure comment to Linear with the error, moves the issue back to Todo.

`_retry_run()` builds a new prompt with `prior_feedback` (all accumulated feedback texts) and a `memory_brief` (context from `runs/memory/<issue-id>/`) injected before the issue description. This gives subsequent iterations context about what was already tried.

Stall-triggered retries follow the same path — the poller detects `is_stalled()` on each tick, kills the subprocess, then `_handle_result()` sees a non-zero exit code and enters the retry logic.

Plan issues always receive the planning prompt on retry, not the execution prompt.

---

## Manual Control

To work on an issue directly outside the orchestrator:

```bash
cd workspaces/<issue-id>
claude
```

The `.claude/settings.json` is already in place with the correct plugin dirs and permissions, so the full skill set is available. Use `/pd-issue <issue-id>` inside that Claude session to load issue context from Linear.

When to take manual control:
- The agent has produced partial work and you want to review and adjust before the next iteration.
- The run has hit max attempts and you want to continue from where it left off.
- You need to run a specific skill or investigate a problem in the worktree.

After manual work, move the issue in Linear to the appropriate next state (Human Review if done, Agent Feedback Needed to trigger orchestrator resumption, or Done to close).

The `resonance attach <issue-id>` CLI command prints the worktree path and current log file path without starting anything.
