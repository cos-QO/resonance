# Orchestrator Technical Design

## Purpose

The orchestrator is the runtime layer that bridges Linear and Claude execution.
It continuously polls Linear for eligible issues, manages isolated workspaces,
launches Claude workers, and reconciles issue state with local run state.

It contains no workflow policy. Policy lives in `.claude/cc-pipeline/`.
It contains no business logic. That lives in the Claude worker adapter.
Its single responsibility is: run the right work in the right place at the right time.

---

## Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Orchestrator                         │
│                                                             │
│  ┌──────────┐    ┌───────────────┐    ┌─────────────────┐  │
│  │  Poller  │───▶│  Workspace    │───▶│     Runner      │  │
│  │          │    │  Manager      │    │                 │  │
│  │ polls    │    │ git worktrees │    │ claude -p       │  │
│  │ Linear   │    │ .claude setup │    │ stream capture  │  │
│  └──────────┘    └───────────────┘    └────────┬────────┘  │
│       │                                         │           │
│  ┌────▼──────┐                        ┌────────▼────────┐  │
│  │Reconciler │                        │  State Manager  │  │
│  │           │                        │                 │  │
│  │ drift     │◀───────────────────────│ runs/state.json │  │
│  │ detection │                        │ events.jsonl    │  │
│  └──────────-┘                        └─────────────────┘  │
│       │                                                     │
│  ┌────▼──────────┐                                          │
│  │ Linear Client │  thin API wrapper                        │
│  └───────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
         │                        ▲
         ▼                        │
    Linear API             hooks write events
                           TUI reads events
```

---

## Polling Loop

The core loop runs on a fixed cadence defined in `WORKFLOW.md` (`polling.interval_seconds`).

```python
async def polling_loop():
    while True:
        # 1. Fetch current eligible issues from Linear
        eligible = await linear_client.get_eligible_issues()
        #    eligible = issues with state == "Plan Approved"
        #              AND matching task type label
        #              AND valid plan approval verified

        # 2. Get current active runs
        active = state_manager.get_active_runs()

        # 3. Reconcile: stop runs where issue is no longer eligible
        for run in active:
            if run.issue_id not in [i.id for i in eligible]:
                await runner.stop(run, reason="issue_no_longer_eligible")
                await linear_client.post_comment(
                    run.issue_id,
                    "Run stopped: issue moved out of eligible state."
                )

        # 4. Start new runs up to concurrency cap
        running_ids = {r.issue_id for r in state_manager.get_active_runs()}
        slots = WORKFLOW.concurrency.max_parallel_runs - len(running_ids)

        for issue in eligible[:slots]:
            if issue.id not in running_ids:
                workspace = await workspace_manager.create(issue)
                await runner.start(issue, workspace)

        await asyncio.sleep(WORKFLOW.polling.interval_seconds)
```

The reconciler runs on a separate cadence (`polling.reconcile_interval_seconds`) and
performs deeper checks: orphan workspace detection, stalled process detection, and
state drift between `runs/state.json` and actual Linear issue state.

---

## Issue Eligibility Detection

An issue is eligible when ALL of the following are true:

1. **Linear state** = `Plan Approved` (exact match, case-sensitive)
2. **Task type label** present — at least one of: `design`, `frontend`, `bug+frontend`
3. **Plan approval verified** — queried via Linear API, not assumed from state name alone
4. **No active run** exists for this issue in `runs/state.json`
5. **Concurrency cap** not exceeded

Fail closed: if plan approval cannot be verified (API error, ambiguous state),
the issue is skipped and a warning is written to the event log.

### Task type detection

```python
def detect_task_type(issue: LinearIssue) -> str | None:
    labels = {l.name.lower() for l in issue.labels}

    if "design" in labels:
        return "design_to_code"
    if "frontend" in labels and "bug" not in labels:
        return "frontend_feature"
    if "bug" in labels and "frontend" in labels:
        return "frontend_bug"

    return None  # unsupported — orchestrator will post comment and skip
```

When task type is `None`, the orchestrator posts the unsupported comment defined in
`WORKFLOW.md` and moves the issue back to `Todo`.

---

## Workspace Lifecycle

### Creation

```bash
# 1. Create git worktree on a new branch
git worktree add workspaces/QO-123 -b agent/QO-123

# 2. Write minimal .claude/settings.json into the workspace
# Points plugin dirs at ../../.claude/cc-pipeline and ../../.claude/cc-qo-skills
# Activates orchestrator hooks (event_bridge, uncertainty_detector, etc.)
orchestrator.workspace.write_agent_config(worktree_path, issue, task_type)

# 3. Record workspace in state.json
state_manager.create_run(issue_id, worktree_path, task_type)
```

The `.claude/settings.json` written into each workspace:

```json
{
  "plugins": [
    "../../.claude/cc-pipeline",
    "../../.claude/cc-qo-skills"
  ],
  "mcpConfig": "../../.mcp.json",
  "hooks": {
    "Stop": [
      { "type": "command", "command": "python3 ../../orchestrator/hooks/uncertainty_detector.py" },
      { "type": "command", "command": "python3 ../../orchestrator/hooks/event_bridge.py stop" }
    ],
    "SubagentStop": [
      { "type": "command", "command": "python3 ../../orchestrator/hooks/phase_tracker.py" },
      { "type": "command", "command": "python3 ../../orchestrator/hooks/artifact_poster.py" }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          { "type": "command", "command": "python3 ../../orchestrator/hooks/event_bridge.py file_write" }
        ]
      }
    ]
  }
}
```

### Cleanup

Triggered when issue reaches a terminal state (`Done`, `Cancelled`) or when
the workspace is older than `workspace.max_age_hours` with no active run.

```bash
git worktree remove workspaces/QO-123 --force
```

State record moved from `active` to `archived` in `runs/state.json`.
Log file retained in `runs/logs/` for post-mortem inspection.

---

## Issue Claiming Model

For v1 (single machine), `runs/state.json` is the claim record.
No distributed locking is needed.

Before starting a run, the orchestrator checks:
- Is `issue_id` present in `state.json`?
- If yes: is its status `failed` or `complete`? Only then can it be re-claimed.
- If status is `running`, `paused`, or `waiting_human`: skip — already claimed.

A run is considered orphaned if:
- Status is `running` in `state.json`
- But the process PID is no longer alive
- Or the workspace directory no longer exists

Orphan detection runs in the reconciler and triggers recovery (see Retry Policy).

---

## Run State Model

`runs/state.json` — the authoritative local state for all runs.

```json
{
  "QO-123": {
    "status": "running",
    "task_type": "design_to_code",
    "worker": "claude-sonnet",
    "worktree": "workspaces/QO-123",
    "branch": "agent/QO-123",
    "pid": 48291,
    "iteration": 2,
    "attempt": 1,
    "started_at": "2026-04-28T14:32:00Z",
    "last_event_at": "2026-04-28T14:45:12Z",
    "artifacts": {
      "preview_url": "http://localhost:3001",
      "figma_comparison": null
    },
    "pending_question": null,
    "log_file": "runs/logs/QO-123-20260428-143200.log"
  }
}
```

### Status values

| Status | Meaning |
|---|---|
| `running` | Claude process is active |
| `paused` | Manually paused by operator (`resonance pause`) |
| `waiting_human` | Agent emitted `human_input_needed` or `ready_for_review` |
| `failed` | Max retries exceeded or unrecoverable error |
| `complete` | Issue moved to `Human Review`, PR opened |
| `archived` | Workspace cleaned up, record kept for history |

---

## Event Stream Schema

`runs/events.jsonl` — append-only, one JSON object per line.
TUI tails this file. Orchestrator reads it for state transitions.

```jsonl
{"ts":"2026-04-28T14:32:00Z","issue":"QO-123","type":"run_started","iteration":1,"task_type":"design_to_code"}
{"ts":"2026-04-28T14:32:05Z","issue":"QO-123","type":"skill_loaded","skill":"connectui-dev"}
{"ts":"2026-04-28T14:33:10Z","issue":"QO-123","type":"file_modified","path":"src/components/Hero.tsx"}
{"ts":"2026-04-28T14:33:45Z","issue":"QO-123","type":"subagent_started","agent":"developer"}
{"ts":"2026-04-28T14:38:00Z","issue":"QO-123","type":"subagent_completed","agent":"developer"}
{"ts":"2026-04-28T14:38:10Z","issue":"QO-123","type":"artifact_ready","artifact":"preview_url","value":"http://localhost:3001"}
{"ts":"2026-04-28T14:38:15Z","issue":"QO-123","type":"ready_for_review","summary":"Hero section implemented. Preview at http://localhost:3001. Matched Figma spacing and typography."}
{"ts":"2026-04-28T14:39:00Z","issue":"QO-123","type":"iteration_paused","iteration":1,"reason":"waiting_human_approval"}
{"ts":"2026-04-28T14:52:00Z","issue":"QO-123","type":"human_feedback_received","feedback":"Use shadow-sm not shadow-md on the card."}
{"ts":"2026-04-28T14:52:05Z","issue":"QO-123","type":"run_started","iteration":2}
{"ts":"2026-04-28T15:10:00Z","issue":"QO-123","type":"human_approved"}
{"ts":"2026-04-28T15:10:05Z","issue":"QO-123","type":"run_complete","handoff_state":"Human Review","pr_url":"https://github.com/..."}
```

### Event types

| Type | Emitted by | Meaning |
|---|---|---|
| `run_started` | orchestrator | New iteration begins |
| `skill_loaded` | event_bridge hook | Agent loaded a skill file |
| `file_modified` | event_bridge hook | Agent wrote or edited a file |
| `subagent_started` | event_bridge hook | A subagent was spawned |
| `subagent_completed` | event_bridge hook | A subagent finished |
| `human_input_needed` | uncertainty_detector hook | Agent flagged a decision |
| `artifact_ready` | artifact_poster hook | Agent produced a reviewable artifact |
| `ready_for_review` | uncertainty_detector hook | Agent signalled iteration complete |
| `iteration_paused` | orchestrator | Run paused, waiting for human |
| `human_feedback_received` | orchestrator (from CLI) | Human sent feedback |
| `human_approved` | orchestrator (from CLI) | Human approved via `resonance approve` |
| `run_complete` | orchestrator | Run finished, Linear updated |
| `run_failed` | orchestrator | Unrecoverable failure |
| `run_aborted` | orchestrator | Operator called `resonance abort` |

---

## Retry and Recovery Policy

Defined in `WORKFLOW.md` under `retry`.

```
Attempt 1 → crash → wait 5s  → Attempt 2
Attempt 2 → crash → wait 15s → Attempt 3
Attempt 3 → crash             → give up → post failure report → move to Todo
```

### Stall detection

If no event is written to the event log for `retry.on_stall_minutes` (default 30),
the orchestrator treats the run as stalled:
1. SIGTERM the Claude process
2. Write `run_stalled` event
3. Restart as a new attempt (counts against max_attempts)

### Ineligibility during a run

If the reconciler detects the issue has moved out of `Plan Approved` or `In Progress`
state during a run (e.g. human cancelled it in Linear):
1. SIGTERM the Claude process immediately
2. Write `run_stopped_ineligible` event
3. Do NOT retry
4. Leave workspace intact for inspection
5. Write a comment to Linear: "Run stopped: issue state changed during execution."

---

## Failure Modes

| Failure | Detection | Response |
|---|---|---|
| Process crash | PID not alive | Retry with backoff |
| Stall (no output) | Event log gap > 30min | SIGTERM + retry |
| Plan gate missing | No `Plan Approved` status | Skip issue, log warning |
| Unknown task type | No matching label | Post unsupported comment, return to Todo |
| Max retries exceeded | attempt > max_attempts | Post failure report, move to Todo |
| Issue becomes ineligible mid-run | Reconciler detects state change | Stop immediately, no retry |
| Workspace creation fails | `git worktree add` error | Log error, skip issue this cycle |
| Orphan workspace | PID dead, status=running | Clean up workspace, reset state |
| Linear API error | HTTP error on poll | Skip cycle, log, retry next poll |

---

## Observability

### TUI (primary)
The TUI reads `runs/events.jsonl` in real-time via file tailing.
Every significant event is visible within seconds of occurring.

### Logs (secondary)
Each run writes a structured log to `runs/logs/{issue_id}-{timestamp}.log`.
Format: `[timestamp] [level] [issue] message`
Retained indefinitely (operators are responsible for rotation).

### State inspection
```bash
cat runs/state.json        # current run state
tail -f runs/events.jsonl  # live event stream
resonance status                  # formatted summary
```

---

## Key Interfaces

### orchestrator → Linear Client
```python
linear_client.get_eligible_issues() -> List[Issue]
linear_client.set_issue_state(issue_id, state) -> None
linear_client.post_comment(issue_id, body) -> None
linear_client.verify_plan_approved(issue_id) -> bool
```

### orchestrator → Runner
```python
runner.start(issue, workspace) -> Run
runner.stop(run, reason) -> None
runner.is_alive(run) -> bool
```

### orchestrator → State Manager
```python
state_manager.create_run(issue_id, ...) -> None
state_manager.update_run(issue_id, **fields) -> None
state_manager.get_active_runs() -> List[Run]
state_manager.get_run(issue_id) -> Run | None
```

### CLI → orchestrator
The CLI communicates with the orchestrator via a local socket or shared state file.
Commands (approve, feedback, pause, abort) write to a `runs/commands.jsonl` file
that the orchestrator polls between iterations.

---

## Not In Scope (V1)

- Distributed multi-machine scheduling
- GitHub webhook integration (CI watching)
- Automatic PR creation (agent creates PR, human merges)
- Auto-merge or deployment
- Multi-repo support
