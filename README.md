# Resonance

Resonance is a supervised agentic delivery orchestrator. It polls a Linear team for issues in "Plan Approved" state, launches Claude Code agents in isolated git worktrees, monitors their output for structured signals, and keeps humans in control at every decision point. The human approves work before it starts and again before anything merges.

---

## How it works

The full loop from Linear ticket to reviewed output:

1. You create a Linear issue and apply a label that tells Resonance what kind of work it is (`frontend`, `bug` + `frontend`, or `design`).
2. You (or a teammate) reviews the issue, confirms there is enough context for an agent to act on it, and moves it to **Plan Approved** in the Linear board.
3. Resonance polls your Linear team every 60 seconds. When it finds an issue in Plan Approved, it re-verifies the state hasn't changed (fail-closed), then creates an isolated git worktree at `workspaces/RND-123/`, builds a prompt from the issue title, description, and label, and launches `claude -p "<prompt>" --output-format stream-json`.
4. The agent works inside the worktree. When it needs a human decision, it emits a structured signal to stdout:
   ```
   AGENT_SIGNAL: {"type": "human_input_needed", "question": "...", "context": "..."}
   ```
   Resonance detects this, moves the Linear issue to **Agent Feedback Needed**, and pauses the run. You respond with `resonance approve RND-123` or `resonance feedback RND-123 "..."`.
5. When the agent finishes, it emits:
   ```
   AGENT_SIGNAL: {"type": "ready_for_review", "summary": "...", "artifacts": {"preview_url": "..."}}
   ```
   Resonance moves the issue to **Human Review** and posts a comment with the summary and preview URL.
6. You open the PR, review the code, and merge — or send feedback with `resonance feedback` to trigger another iteration.

**Human gates are mandatory:** work cannot begin without Plan Approved, and nothing merges without your PR review.

**Labels control task type:**

| Label(s) | Task type |
|---|---|
| `frontend` | frontend_feature |
| `frontend` + `bug` | frontend_bug |
| `design` | design_to_code (requires FIGMA_API_KEY) |

Issues with no recognized label are rejected: Resonance posts a comment explaining what labels are supported, then returns the issue to Todo.

---

## Quick start

Prerequisites: Python 3.11+, Git, [Claude Code CLI](https://claude.ai/code) (`claude auth login`)

```bash
# 1. Clone
git clone https://github.com/cos-QO/resonance && cd resonance

# 2. Run setup (installs resonance via pip install -e . automatically)
./setup.sh

# 3. Health check
resonance doctor

# 4. Start the orchestrator
./onair.sh
```

`./setup.sh` installs the `resonance` CLI via `pip install -e .` before running the interactive wizard. It collects your Linear API key, lists your teams so you can pick one, creates the required workflow states and labels in Linear, and writes a `.env` file.

To update a single credential later: `./setup.sh update`  
To start over: `./setup.sh overwrite`  
To remove credentials and clear runtime state: `./setup.sh wipe`

---

## Setting up your Linear board

`resonance setup` creates four workflow states in your Linear team automatically:

| State | Role |
|---|---|
| Plan Approved | You move issues here to authorize agent work |
| In Progress | Set automatically when a run starts |
| Agent Feedback Needed | Set when the agent emits `human_input_needed` |
| Human Review | Set when the agent emits `ready_for_review` |

**The states are created, but they appear in "Hidden columns" on the team board by default.** Linear hides custom workflow states until you explicitly show them.

To unhide them:
1. Open your team's board view in Linear.
2. Look for the **"Hidden columns"** button on the right side of the board.
3. Click it and enable **Plan Approved**, **Agent Feedback Needed**, and **Human Review**.

Once visible, your board shows the full pipeline: Todo → Plan Approved → In Progress → Agent Feedback Needed / Human Review → Done.

---

## Your first run

**Step 1 — Create a Linear issue in your team.** Write a clear title and description. The description is passed directly to the agent as its task specification, so be specific about what you want.

**Step 2 — Add a label.** Apply `frontend` (or `frontend` + `bug`, or `design`) to the issue. Without a recognized label, Resonance will reject the issue.

**Step 3 — Move to Plan Approved.** Drag the issue to the Plan Approved column (make sure it's unhidden — see above). This is your explicit authorization for the agent to begin.

**Step 4 — Start the orchestrator if it isn't running.** In your terminal: `./onair.sh`

**Step 5 — Wait up to 60 seconds.** Resonance polls Linear on a 60-second interval. When it picks up the issue, it moves it to In Progress automatically.

**Step 6 — Monitor with the CLI:**
```bash
resonance status              # see all runs and their current status
resonance status RND-123      # detail for your issue: status, branch, log file
resonance logs RND-123        # recent event stream for this run
```

**Step 7 — Respond to signals.** If the agent pauses with `human_input_needed`, you'll see the Linear issue move to Agent Feedback Needed and a comment with the question. Use:
```bash
resonance feedback RND-123 "use the secondary button variant here"
resonance approve RND-123     # to approve without additional feedback
```

**Step 8 — Review.** When the agent finishes, the issue moves to Human Review and a comment is posted with a preview URL (if applicable). Review the code branch. Merge when satisfied.

---

## Commands reference

Both `resonance` and `reso` work as the CLI name.

```bash
# Setup and health
resonance setup               # guided wizard: credentials + create Linear states/labels
resonance doctor              # verify credentials, dependencies, and Linear configuration

# Monitoring
resonance status              # all runs on record with status, task type, last event
resonance status RND-123      # detail for one run: status, branch, log file, artifacts
resonance logs RND-123        # recent events for a run (default: last 50)
resonance attach RND-123      # print worktree path and log file path for manual inspection

# Human control
resonance approve RND-123     # resume a run waiting for human input (waiting_human or paused)
resonance feedback RND-123 "text"  # queue feedback for the agent; run resumes automatically
resonance pause RND-123       # pause an active run cleanly (resume later with approve)
resonance abort RND-123       # stop a run permanently; workspace preserved for inspection
resonance abort RND-123 --yes # skip the confirmation prompt

# TUI (Milestone 2)
resonance watch               # placeholder — TUI dashboard is coming in Milestone 2
```

---

## Configuration

**`.env`** — credentials, written by `./setup.sh`, never committed:

```
LINEAR_API_KEY=lin_api_...         # required
LINEAR_TEAM_ID=<uuid>              # required — the team Resonance watches
FIGMA_API_KEY=figd_...             # optional — required for design_to_code tasks
GITHUB_TOKEN=ghp_...               # optional — required for PR creation (Milestone 3)
```

Note: the variable is `LINEAR_TEAM_ID`, not `LINEAR_PROJECT_ID`. The setup wizard writes the correct name; if you have an old `.env` with `LINEAR_PROJECT_ID`, `resonance setup` will migrate it.

**`WORKFLOW.md`** — runtime policy, committed and safe to share:
- Defines which labels map to which task types
- Sets polling interval (default: 60s), max parallel runs (default: 2), retry policy (max 3 attempts), stall timeout (30 minutes)
- Controls required artifacts per task type, verify levels, and iteration limits
- No credentials — edit this to tune orchestrator behaviour for your team

Changes to `WORKFLOW.md` take effect on the next orchestrator restart.

---

## Architecture

```
orchestrator/          Runtime — polls Linear, manages worktrees, runs Claude
  main.py              Entry point (run via ./onair.sh)
  poller.py            Main loop: tick, classify, start/advance/reconcile runs
  runner.py            Subprocess management: launches claude, parses stream-json, detects AGENT_SIGNALs
  classifier.py        Maps issue labels to task type config from WORKFLOW.md
  workspace.py         Creates and manages git worktrees
  linear_client.py     Linear GraphQL API client
  state.py             Reads/writes runs/state.json and runs/commands.jsonl
  events.py            Appends to runs/events.jsonl
  hooks/               Event bridge, artifact poster, uncertainty detector, phase tracker
  config.py            Loads .env + WORKFLOW.md into a single Config object

cli/
  main.py              resonance/reso CLI — setup, doctor, status, approve, feedback, pause, abort, attach, logs, watch

runs/                  Runtime state — gitignored
  state.json           Current state of all runs (authoritative)
  events.jsonl         Append-only structured event log
  commands.jsonl       CLI commands queued for the orchestrator
  logs/                Per-run log files: RND-123-20260428T143200.log

workspaces/            Git worktrees — one per active issue, gitignored
  RND-123/             Isolated worktree on branch agent/RND-123

WORKFLOW.md            Policy contract — task types, retry config, concurrency
.env                   Credentials — gitignored, written by setup
.env.example           Template — committed, shows required variables
docs/                  Architecture docs, design notes, this runbook
```

---

## Milestone status

- **Milestone 1 — Orchestrator core** complete: polling, worker management, git worktrees, AGENT_SIGNAL protocol, CLI (setup, doctor, status, approve, feedback, pause, abort, attach, logs), Linear state management
- **Milestone 2 — TUI dashboard**: real-time Textual dashboard (`resonance watch`). Not yet built; the command currently prints a placeholder message.
- **Milestone 3 — cc-pipeline integration**: plan gate wiring, automated PR creation, execution reports posted to Linear
