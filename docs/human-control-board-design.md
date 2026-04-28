# Human Control Board — Design Brainstorm

## Purpose

This document captures the design thinking from the initial brainstorming session on the
Resonance — the Queen One orchestrator — with a human-in-the-loop TUI dashboard.

It is a working design artifact, not a final spec. Decisions are marked explicitly.

---

## Problem Statement

Symphony gives you a runtime loop (poll Linear → run agent → handoff state) but no structured
human presence during execution. The gap for Queen One:

- Agents are iterative, not one-shot. Design-to-code, complex features, and ambiguous tickets
  all require back-and-forth between human and agent.
- "Agent says done" ≠ actually done. Agents self-assess unreliably. Linear should only reflect
  human-verified completion, not agent self-report.
- No visibility into what agents are doing between plan approval and PR review — a long autonomy
  stretch with no structured intervention surface.

---

## Design Principles

1. **Linear = official record** — states, approvals, completed work, decisions. Never updated by
   agent self-report alone. Always human-gated.
2. **TUI = human control board** — real-time view of what agents are doing, where to intervene,
   how to approve or redirect.
3. **Workspace folder = the runtime** — everything agents do leaves a trace on disk. The TUI
   reads the folder, not agents.
4. **Agents signal, humans decide** — agents surface uncertainty and completion readiness. Humans
   confirm, approve, or redirect.

---

## Three-Layer Architecture

```
.claude/cc-pipeline/     Policy layer (existing — lives inside .claude/)
                         pd-guardrail, pd-plan, pd-scope, pd-report
                         Skills, rules, commands — the workflow contract
                         Always available to Claude agents without extra setup

orchestrator/            Runtime layer (new — Resonance, Symphony-inspired)
                         Polls Linear, manages workspaces, launches Claude,
                         reconciles issue state, handles recovery

tui/                     Human control layer (new)
                         Real-time agent view, intervention surface,
                         approval gate, query/co-work interface
```

These three concerns are kept strictly separate. The orchestrator does not contain policy.
The TUI does not contain business logic. cc-pipeline does not know about the runtime.

**Key structural decision:** `cc-pipeline` lives inside `.claude/` — not at the repo root.
It is Claude agent configuration (skills, rules, commands) and belongs in the agent
environment. Root level contains only application code: orchestrator, TUI, CLI.

---

## Orchestrator Design

### What it does

- Polls Linear on a fixed cadence
- Detects eligible issues (Plan Approved state + no active run)
- Creates a git worktree per issue (named from issue identifier)
- Launches Claude headlessly (`claude -p --output-format stream-json`)
- Persists run state and logs locally
- Reconciles: detects ineligible/terminal issues, cleans up orphan workspaces
- Retry with bounded backoff on failure

### What it does not do

- No workflow policy decisions
- No prompt construction (that belongs to the Claude worker adapter)
- No direct Linear writes (those are human-gated or agent-posted via cc-pipeline)

### Issue eligibility

An issue is eligible for a run when:
1. Linear state = `Plan Approved`
2. No active run already exists for this issue (checked via local state)
3. Concurrency cap not exceeded (defined in `WORKFLOW.md`)

Fail closed: if approval cannot be verified, do not start.

### Recommended Linear state model

```
Todo
Ready for Planning
Plan Proposed          ← agent posts draft plan
Plan Approved          ← human approves (gate 1 — existing)
In Progress            ← orchestrator starts iteration
Agent Feedback Needed  ← agent posts artifact, pauses, waits for human
  ↑___________________↓  (loop until human approves)
Human Review           ← human approves via TUI, PR opened (gate 2)
Done                   ← human-verified complete
```

`Agent Feedback Needed` is the key addition. It is a structured pause state, not a terminal
state. The orchestrator waits here until the human acts.

---

## TUI Dashboard Design

### Role

The TUI is the human's window into the runtime. It is not a log viewer — it is an active
control surface where the human can approve, redirect, query, and co-work with agents.

### Real-time update mechanism

The TUI does not poll agents. It watches the filesystem and reads Claude's stream:

- **`watchdog` (Python library)** — fires on any file change in the workspace directory
- **Claude stream-json** — orchestrator captures stdout from `claude -p --output-format stream-json`
- **Event stream** — hooks write structured events to `runs/events.jsonl`, TUI tails this file

Everything agents do — writing memory, loading skills, modifying files, completing phases —
leaves a trace on disk. The TUI reads the trace.

### Display panels

**Active issues panel** — all running issues with agent tree, current task, last activity, status

**Live output panel** — streaming Claude stdout for the selected issue

**Workspace activity panel** — real-time file changes in the worktree (which files, which memory
zones, which skills loaded)

**Notification panel** — agent uncertainty flags and decisions requiring human input

### Human actions (keyboard-driven)

| Key | Action |
|-----|--------|
| Q | Open query panel for selected issue |
| A | Approve current iteration → updates Linear |
| F | Send feedback → injected into next iteration |
| P | Pause run cleanly |
| T | Hand off entirely (open full interactive session) |
| Esc | Close panel, resume |

### Query panel (embedded terminal)

Pressing Q opens an embedded terminal panel inside the TUI (Textual's Terminal widget).

The session launched in that panel:
- Points at the same worktree as the running issue
- Has context injected: current plan, last agent action, memory state, active skill
- Is a full interactive Claude Code session — human can type freely

When the human closes the panel, the orchestrator resumes from where it paused.
The query conversation is logged alongside the run.

This is the co-working surface. The human does not take over the session — they join it.

### Technology

**Textual** (Python) — reactive TUI framework, CSS-like layout, Terminal widget for embedded
sessions, keyboard shortcut handling, live update support.

---

## Multi-Model Worker Adapter

The orchestrator is model-agnostic. The worker layer abstracts which model runs a given issue.

### Worker interface

```python
class WorkerAdapter:
    async def run(self, issue, context, workspace) -> WorkerResult: ...
    async def stream(self, issue, context, workspace) -> AsyncIterator[WorkerEvent]: ...
```

Concrete implementations:
- `ClaudeWorker` — `claude -p --output-format stream-json` (v1)
- `OpenRouterWorker` — routes to GPT-4o, Gemini, or any OpenRouter model
- `LocalWorker` — Ollama for sensitive work that must not leave the machine

### Routing via WORKFLOW.md

```yaml
workers:
  default: claude-sonnet
  routing:
    - task_type: planning        → claude-opus      # complex reasoning
    - task_type: context_scope   → claude-haiku     # fast, cheap parallel scoping
    - task_type: code_review     → codex            # second opinion
    - task_type: design_to_code  → claude-sonnet    # vision capable
    - label: sensitive           → local-ollama     # never leaves machine
  concurrency: 2
```

The TUI shows which model is running for each active issue. The query panel opens a session
with whatever model is assigned to that issue — not always Claude.

### Recommended for v1

Use `claude -p --output-format stream-json` only. Design the interface for extensibility
so switching to OpenRouter or the Agent SDK in v2 requires changing the worker, not the
orchestrator or TUI.

---

## Hooks as the Event Bridge

Claude Code hooks fire on lifecycle events and are the bridge between Claude execution and the
TUI + orchestrator state.

### Key hooks

| Hook event | What it does |
|------------|-------------|
| `Stop` | Scans output for uncertainty signals, writes event to stream, updates run state |
| `SubagentStop` | Marks phase complete in execution tracker, signals TUI to update agent tree |
| `SubagentStart` | Signals TUI to add new agent entry, injects context into subagent |
| `PostToolCall` (Write/Edit) | Logs file activity to event stream → TUI workspace panel |
| `PostToolCall` (Linear MCP) | Logs Linear interactions → Linear activity visible in TUI |

### Event stream pattern

All hooks write structured JSON events to a shared append-only log:

```
runs/events.jsonl
```

The TUI tails this file. The orchestrator reads it for state management.
This decouples hooks from the TUI — hooks do not know about the TUI, and the TUI
does not know about hooks.

### Uncertainty detection

The agent's system prompt instructs it to emit a structured signal when uncertain:

```json
{"type": "human_input_needed", "question": "...", "options": [...], "context": "..."}
```

The `Stop` hook detects this pattern in the output stream, writes the event, and
signals the orchestrator to pause and move the issue to `Agent Feedback Needed`.
The TUI shows the ⚠ indicator for that issue.

### Completion integrity

The agent signals readiness (`{"type": "ready_for_review", "summary": "..."}`).
The hook writes this event. The TUI shows it. The orchestrator moves the issue to
`Agent Feedback Needed`. Nothing moves to `Human Review` until the human presses A.

---

## Iterative Execution Model

Agents are iterative, not one-shot. The orchestrator manages iteration cycles:

```
Issue: Plan Approved
  → Orchestrator starts iteration 1
  → Claude runs bounded task (scoped in cc-pipeline prompt)
  → Agent emits ready_for_review or human_input_needed
  → Hook captures signal, orchestrator pauses
  → TUI shows issue in Agent Feedback Needed
  → Human reviews (TUI live output + workspace activity)
  → Human sends feedback (F) or approves (A)
    → Feedback: orchestrator starts iteration 2 with feedback prepended to context
    → Approve: orchestrator opens PR, moves issue to Human Review in Linear
```

The iteration loop is the primary execution model. A one-pass run is just an iteration
loop that completes on the first pass.

---

## What Linear Reflects

Linear is updated only at these explicit points:

| Event | Who updates Linear | When |
|-------|-------------------|------|
| Plan posted | Agent (pd-plan-post skill) | After plan draft |
| Plan approved | Human (in Linear directly) | Before execution starts |
| Progress update | Agent (cc-pipeline hook) | At natural phase boundaries |
| Artifact posted | Orchestrator hook (SubagentStop) | On phase completion |
| Ready for review | Orchestrator (on agent signal) | When agent emits ready signal |
| Human Review | TUI (on human A keypress) | Only when human explicitly approves |
| Done | Human (in Linear) | After PR merged |

Linear never shows a terminal state the human didn't confirm. The agent's self-assessment
drives the TUI display. The human's action drives Linear.

---

## File Tree

```
agentic-pipeline/
│
├── .claude/                          ← everything Claude needs
│   ├── cc-pipeline/                  ← policy plugin (moved from root)
│   │   ├── commands/                   /pd-start, /pd-scope, /pd-plan, /pd-report
│   │   ├── rules/                      pd-guardrail, pd-linear-sync, pd-issue-standard
│   │   ├── skills/                     pd-linear-scope, pd-context-pack, pd-plan-post
│   │   └── README.md
│   ├── agents/                       ← 15 agent definitions
│   ├── hooks/                        ← dev workflow hooks
│   ├── memory/                       ← shared project memory
│   ├── agent-memory/                 ← per-agent persistent memory
│   ├── rules/                        ← repo-level rules
│   ├── skills/                       ← repo-level skills
│   ├── settings.json                 ← permissions + hook config (references cc-pipeline)
│   └── CLAUDE.md                     ← full architecture guide
│
├── WORKFLOW.md                       ← machine-readable runtime contract
│                                       eligibility rules, worker routing, concurrency cap
│
├── orchestrator/                     ← Python application
│   ├── main.py
│   ├── poller.py                     ← Linear polling, eligibility detection
│   ├── workspace.py                  ← git worktree lifecycle
│   │                                    writes .claude/settings.json per workspace
│   ├── runner.py                     ← process launch, stream capture
│   ├── reconciler.py                 ← state drift, orphan detection
│   ├── state.py                      ← runs/state.json
│   ├── linear_client.py              ← Linear API wrapper
│   ├── workers/                      ← model-agnostic worker layer
│   │   ├── base.py                   ← WorkerAdapter interface
│   │   ├── claude_worker.py          ← claude -p (v1)
│   │   ├── openrouter_worker.py      ← GPT-4o, Gemini, etc.
│   │   └── router.py                 ← reads WORKFLOW.md, selects worker
│   └── hooks/                        ← hooks for orchestrated runs only
│       ├── event_bridge.py           ← all events → runs/events.jsonl
│       ├── uncertainty_detector.py   ← flags ⚠ when agent is uncertain
│       ├── phase_tracker.py          ← updates execution-tracker.json
│       └── artifact_poster.py        ← posts to Linear on completion
│
├── tui/                              ← Textual dashboard
│   ├── app.py
│   ├── widgets/
│   │   ├── issues_panel.py           ← active issues + agent tree + model label
│   │   ├── live_output.py            ← streaming worker output
│   │   ├── workspace_panel.py        ← file activity (watchdog)
│   │   ├── notifications.py          ← ⚠ flags, decisions needed
│   │   └── query_panel.py            ← embedded terminal, context-injected
│   ├── event_reader.py               ← tails runs/events.jsonl
│   └── actions.py                    ← approve/feedback/pause/abort → Linear
│
├── cli/
│   └── main.py                       ← resonance watch / attach / approve / feedback / abort
│
├── runs/                             ← gitignored runtime
│   ├── state.json
│   ├── events.jsonl                  ← append-only event stream
│   └── logs/
│
├── workspaces/                       ← gitignored runtime
│   └── QO-123/                       ← git worktree per issue
│       └── .claude/                  ← orchestrator-created, minimal
│           ├── settings.json           orchestrator hooks only
│           └── memory/pd/              scoped issue memory
│
└── docs/                             ← design documentation
```

---

## Decisions

All decisions are recorded in `WORKFLOW.md`. Summary:

| Decision | Choice | Rationale |
|---|---|---|
| Plan approval detection | Custom Linear status `Plan Approved` | Queryable, unambiguous, board-visible |
| Issue classification | Linear labels (`design`, `frontend`, `bug`) | Explicit human signal, no agent inference |
| Orchestrator language | Python | asyncio, subprocess, watchdog, Anthropic SDK, typer |
| Worker runtime v1 | `claude -p --output-format stream-json` | Lowest coupling, sufficient for proof of concept |
| Worker runtime v2 | Claude Agent SDK | Better session control, structured events |
| Feedback injection v1 | Async (prepend to next iteration context) | Simpler, safer than mid-session injection |
| Concurrency cap | 2 parallel runs | Defined in WORKFLOW.md, not hardcoded |
| Visual artifact requirement | Preview URL posted to Linear | Agent starts dev server; human opens browser |
| V1 task scope | design_to_code, frontend_feature, frontend_bug | Matches existing cc-pipeline focus |
| Unsupported task handling | Post comment and return to Todo | Explicit rejection, no silent failures |

---

## Milestone Sequence

### Milestone 0 — Define the contract
- Write `WORKFLOW.md` (runtime contract)
- Define Linear state model and eligibility rules
- Define approved-plan detection mechanism

### Milestone 1 — Orchestrator skeleton
- Linear polling loop
- Workspace lifecycle (git worktrees)
- Single-issue run with `claude -p`
- Local run state + log persistence

### Milestone 2 — TUI dashboard
- Textual app with active issues panel
- Live output streaming
- Workspace file activity panel
- Approve / feedback / pause actions

### Milestone 3 — Hooks + event bridge
- Event stream (`runs/events.jsonl`)
- Uncertainty detector hook
- Phase tracker hook
- TUI reads event stream in real-time

### Milestone 4 — Query panel
- Embedded terminal in TUI
- Context injection on open
- Resume on close
- Conversation logged

### Milestone 5 — cc-pipeline integration
- Plan gate enforcement in orchestrator
- Worker adapter loads cc-pipeline plugin automatically
- Execution reporting back to Linear via pd-report
