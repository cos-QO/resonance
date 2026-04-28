# Operator Runbook

## Overview

This runbook covers setup, daily operation, human intervention, monitoring,
cleanup, and failure recovery for the Queen One agentic pipeline orchestrator.

The system has three components you interact with:
- **Orchestrator** — background daemon, manages Claude runs
- **TUI** — terminal dashboard, your primary view and control surface
- **CLI** — `resonance` command for quick operator actions

---

## Prerequisites

### Software

| Requirement | Minimum version | Check |
|---|---|---|
| Python | 3.11+ | `python3 --version` |
| Claude Code CLI | latest | `claude --version` |
| Git | 2.5+ (worktree support) | `git --version` |
| Node.js | 18+ (for dev servers) | `node --version` |

### Claude Code authentication

```bash
claude auth login
claude --version   # confirms authenticated
```

### Environment variables

```bash
export LINEAR_API_KEY="lin_api_..."        # required — Linear personal API key
export LINEAR_PROJECT_ID="..."             # required — your Linear project ID
export FIGMA_API_KEY="figd_..."            # required for design_to_code tasks
```

Add these to your shell profile (`~/.zshrc` or `~/.bash_profile`) for persistence.

---

## One-Time Linear Setup

Before the orchestrator can run, your Linear workspace must have the correct
workflow states and labels. This is a one-time manual setup.

### Workflow states

Create these custom workflow states in your Linear workspace settings.
They must match `WORKFLOW.md` exactly (case-sensitive).

| State | Type | When used |
|---|---|---|
| `Ready for Planning` | Started | Scoping can begin |
| `Plan Proposed` | Started | Agent posted draft plan |
| `Plan Approved` | Started | Human approved — orchestrator picks up here |
| `In Progress` | Started | Orchestrator has claimed and started |
| `Agent Feedback Needed` | Started | Agent paused, waiting for human |
| `Human Review` | Completed | Human approved output, PR open |

`Todo`, `Done`, and `Cancelled` typically exist by default.

### Labels

Create these labels in your Linear workspace:

| Label | Usage |
|---|---|
| `design` | Triggers `design_to_code` task type |
| `frontend` | Required for `frontend_feature` and `frontend_bug` |
| `bug` | Combined with `frontend` triggers `frontend_bug` |

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/queen-one/agentic-pipeline
cd agentic-pipeline

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install cc-qo-skills (execution skills — separate module)
git clone https://github.com/queen-one/cc-qo-skills .claude/cc-qo-skills

# 4. Verify Linear MCP is accessible
claude mcp list   # should show 'linear' in the list

# 5. Set your Linear project ID in WORKFLOW.md or via env var
# Either: export LINEAR_PROJECT_ID="your-project-id"
# Or: edit WORKFLOW.md and replace "${LINEAR_PROJECT_ID}" with your ID

# 6. Verify setup
resonance status   # should show "No active runs. Orchestrator not running."
```

---

## Starting the System

### Start the orchestrator (background daemon)

```bash
python -m orchestrator.main &
echo "Orchestrator PID: $!"
```

Or with logging to a file:

```bash
python -m orchestrator.main >> runs/logs/orchestrator.log 2>&1 &
```

### Start the TUI dashboard

In a separate terminal:

```bash
resonance watch
```

The TUI opens and shows the active runs panel, live output, and workspace activity.
The orchestrator and TUI run independently — you can close and reopen the TUI
at any time without affecting active runs.

### Verify the system is running

```bash
resonance status
# Expected output:
# Orchestrator: running (PID 12345)
# Active runs: 0
# Polling interval: 60s
# Next poll: in 45s
```

---

## Normal Operating Flow

### 1. Prepare an issue in Linear

- Fill in the issue with all required fields (see `pd-issue-standard.md` for requirements)
- Add the appropriate label: `design`, `frontend`, or `bug` + `frontend`
- Move the issue to `Ready for Planning`

### 2. Generate and approve a plan

```
/pd-start QO-123    (in an interactive Claude Code session)
```

This runs the full intake flow: PEP validation → context gathering → plan draft → post to Linear.

Review the plan posted to Linear. If approved, move the issue to `Plan Approved`.

### 3. Orchestrator picks it up

Within the next polling cycle (up to 60 seconds), the orchestrator detects the eligible issue,
creates a workspace, and starts a Claude run. The TUI shows the new run appear.

### 4. Monitor in the TUI

The live output panel streams Claude's work in real-time.
The workspace panel shows which files are being modified.

### 5. Respond to agent signals

When the agent flags a decision (⚠):
- Read the question in the notifications panel
- Press `F` to send feedback, or `Q` to open a query session

When the agent signals ready for review:
- Review the preview URL posted to Linear
- Press `A` to approve (moves issue to `Human Review` in Linear, PR is opened)
- Or press `F` to send feedback and trigger another iteration

### 6. Complete the PR review

Open the PR in GitHub. Review and merge as normal.
After merge, move the issue to `Done` in Linear.
The orchestrator detects the terminal state and cleans up the workspace.

---

## Human Intervention

### Approve a completed iteration

```bash
resonance approve QO-123
```

Effect: Linear issue moves to `Human Review`. PR is created (if not already open).
Run is marked complete. Workspace is preserved until PR is merged.

### Send feedback without taking over

```bash
resonance feedback QO-123 "Use the secondary button variant for the CTA"
```

Effect: Feedback is stored and injected at the start of the next iteration.
The run resumes automatically.

### Open an interactive query session

```bash
resonance attach QO-123
# or press Q in the TUI with QO-123 selected
```

Opens an embedded terminal panel in the TUI (or a new terminal window if running headless).
The session is a full Claude Code interactive session in the issue's worktree, with
the current plan, memory state, and iteration context pre-loaded.

Type your questions or instructions directly. Claude responds in full context.
Close the session with `/exit` or Ctrl+D. The orchestrator resumes the run.

### Pause a run

```bash
resonance pause QO-123
```

Effect: Claude process receives SIGTERM cleanly. Workspace is preserved.
Issue remains in `In Progress` in Linear (to prevent another run from starting).
Resume with:
```bash
resonance resume QO-123
```

### Abort a run

```bash
resonance abort QO-123
```

Effect: Claude process terminated. Workspace preserved for inspection.
Linear issue moved to `Todo` with a comment explaining the abort.
Use when the run has gone wrong and you want to start fresh.

To also clean up the workspace:
```bash
resonance abort QO-123 --cleanup
```

---

## Monitoring and Inspection

### TUI (recommended)

```bash
resonance watch
```

Keyboard shortcuts in the TUI:

| Key | Action |
|---|---|
| Tab | Switch between active issues |
| A | Approve selected issue |
| F | Send feedback to selected issue |
| Q | Open query session for selected issue |
| P | Pause selected issue |
| X | Abort selected issue |
| L | Toggle log panel |
| W | Toggle workspace activity panel |
| Esc | Close panels |
| Ctrl+C | Exit TUI (orchestrator continues) |

### Quick status

```bash
resonance status
# Shows: active runs, their status, iteration, last event
```

### Raw event stream

```bash
tail -f runs/events.jsonl | python -m json.tool
```

### Run state

```bash
cat runs/state.json | python -m json.tool
```

### Per-run log

```bash
tail -f runs/logs/QO-123-20260428-143200.log
```

---

## Workspace Management

### List all workspaces

```bash
ls workspaces/
```

### Check orphan workspaces (dry run)

```bash
resonance cleanup --dry-run
```

Orphans are workspaces with no corresponding active run in `runs/state.json`,
or workspaces older than `workspace.max_age_hours` from WORKFLOW.md.

### Clean up orphans

```bash
resonance cleanup
```

### Force-clean a specific workspace

```bash
resonance cleanup QO-123
```

This removes the git worktree and archives the state record.

---

## Common Failure Cases

### Issue not picked up

**Symptom:** Issue is in `Plan Approved` but orchestrator ignores it.

**Checks:**
1. Verify state name is exactly `Plan Approved` (case-sensitive) in Linear
2. Verify the issue has the correct label (`design`, `frontend`, or `bug`+`frontend`)
3. Check `LINEAR_PROJECT_ID` matches the project containing the issue
4. Check `resonance status` — is orchestrator running?
5. Check `runs/events.jsonl` — is there a recent `poll_cycle` event?

```bash
grep "poll_cycle" runs/events.jsonl | tail -5
```

### Plan gate blocked

**Symptom:** Run starts but immediately stops with "plan not approved" error.

**Fix:** The Linear status must be set to `Plan Approved` using the custom workflow state,
not a label or comment. Check Linear and confirm the state appears in the status column,
not the label list.

### Run stalls (no TUI activity)

**Symptom:** TUI shows the run as active but no new events for several minutes.

**Check:**
```bash
cat runs/state.json | python -m json.tool | grep "last_event_at"
# If more than 30 minutes ago, the reconciler should have detected this already
```

**Manual intervention:**
```bash
resonance abort QO-123   # stop cleanly
resonance resume QO-123  # restart (counts as a new attempt)
```

### Figma MCP not loading

**Symptom:** `design_to_code` run starts but agent reports it cannot access Figma.

**Checks:**
1. `echo $FIGMA_API_KEY` — must be set and non-empty
2. `claude mcp list` — should show `figma` in the list
3. Check the workspace MCP config: `cat workspaces/QO-123/.claude/mcp.json`

### Worker crashes immediately

**Symptom:** Run appears in TUI then immediately shows `failed` status.

**Check the log:**
```bash
cat runs/logs/QO-123-*.log | head -50
```

**Common causes:**
- Claude CLI not authenticated: `claude auth login`
- Plugin path wrong: check `workspaces/QO-123/.claude/settings.json`
- MCP config missing: check `workspaces/QO-123/.claude/mcp.json`

### Dev server port conflict

**Symptom:** Agent cannot start dev server, preview URL not generated.

**Fix:** Ports are assigned deterministically. Check if another workspace is using the
same port:
```bash
lsof -i :3001   # check if port is occupied
```

Kill the conflicting process or abort the other workspace first.

### Max iterations reached

**Symptom:** Run stops with "max iterations reached" after `max_iterations` passes.

**What to do:**
1. Review the last iteration's output and the Linear comments
2. If work is acceptable: `resonance approve QO-123` to move to Human Review
3. If more work needed: `resonance feedback QO-123 "..."` — this resets the iteration counter
   and starts a fresh run with your feedback

---

## Recovery Procedures

### Restart the orchestrator

```bash
# Find and kill the existing orchestrator process
ps aux | grep "orchestrator.main"
kill <PID>

# Restart
python -m orchestrator.main &
```

Active runs are recovered from `runs/state.json` on startup.
Workspaces are intact. Runs that were `running` at crash time are restarted
as new attempts (subject to max_attempts).

### Recover from corrupted state

```bash
# Back up current state
cp runs/state.json runs/state.json.bak

# Inspect and edit manually if needed
cat runs/state.json | python -m json.tool
```

If a run is stuck in `running` with a dead PID:
```bash
# Edit state.json to set status to "failed" for the stuck run
# Then restart the orchestrator — it will retry
```

### Full reset (nuclear option)

```bash
# Stop orchestrator
kill $(pgrep -f "orchestrator.main")

# Abort all active workspaces
for dir in workspaces/*/; do
    issue=$(basename "$dir")
    git worktree remove "$dir" --force 2>/dev/null || true
done

# Reset state
echo "{}" > runs/state.json

# Restart
python -m orchestrator.main &
```

Note: this does not affect Linear state. Issues remain in whatever state they were in.
Move them manually in Linear if needed.

---

## Configuration Reference

All runtime behaviour is controlled by `WORKFLOW.md` at the repo root.

Key settings operators most commonly need to adjust:

| Setting | Path in WORKFLOW.md | Default |
|---|---|---|
| Max parallel runs | `concurrency.max_parallel_runs` | 2 |
| Poll interval | `polling.interval_seconds` | 60 |
| Stall timeout | `retry.on_stall_minutes` | 30 |
| Max retry attempts | `retry.max_attempts` | 3 |
| Workspace orphan threshold | `workspace.max_age_hours` | 48 |

Changes to `WORKFLOW.md` take effect on the next orchestrator restart.
