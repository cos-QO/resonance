# Symphony Adaptation for Resonance

## Purpose

This document explains what OpenAI's Symphony is, which parts are directly relevant to this repository, which parts should not be copied as-is, and how to adapt the model so **Resonance** — the Queen One orchestrator — can keep `Linear` as the control plane while using `Claude Code` as the execution engine.

This is a product and architecture handoff document. It is intended for:

- PMs deciding whether Symphony changes the current roadmap
- engineers implementing the orchestration layer
- Claude Code sessions that need enough context to build the first version correctly

---

## Executive Summary

OpenAI published Symphony on **April 27, 2026** as an open-source orchestration spec and reference implementation for turning `Linear` into a control plane for coding agents.

Key point: Symphony is **not primarily a new planning methodology**. It is an **operational runtime pattern**:

- poll the issue tracker continuously
- map one active issue to one isolated workspace
- run an agent against that workspace
- keep the run alive until the issue reaches a defined handoff state
- recover from crashes, stalls, and CI friction automatically

That means Symphony overlaps only partially with this repository.

This repo already has stronger workflow policy than Symphony in a few important areas:

- structured pre-execution inputs via `PEP`
- explicit broad-awareness context gathering
- a mandatory plan approval gate before code
- structured execution reporting back into `Linear`

The main missing capability is a **long-running orchestrator service** that can supervise issue-level work without a human manually opening and steering individual agent sessions.

Recommended direction:

- keep the existing `cc-pipeline` workflow and guardrails
- add **Resonance** — a Symphony-pattern orchestration service — on top
- use `Claude Code` headless or via the `Claude Agent SDK` as the worker runtime
- do **not** copy OpenAI's Elixir prototype directly into production

---

## Source Summary

### OpenAI's published position

OpenAI describes Symphony as an orchestrator that turns a project-management board such as `Linear` into a control plane for coding agents. Their announcement states that each open task gets an agent, agents run continuously, and humans review the results.

Primary sources:

- OpenAI announcement: <https://openai.com/index/open-source-codex-orchestration-symphony/>
- Symphony repo: <https://github.com/openai/symphony>
- Symphony spec: <https://github.com/openai/symphony/blob/main/SPEC.md>
- Symphony Elixir reference implementation: <https://github.com/openai/symphony/blob/main/elixir/README.md>

### Claude Code runtime capabilities

Anthropic documents two practical ways to drive Claude Code programmatically:

- `claude -p` for non-interactive execution
- `Claude Agent SDK` for longer-running, programmatic control

Primary sources:

- Claude Code CLI reference: <https://code.claude.com/docs/en/cli-usage>
- Claude Agent SDK overview: <https://code.claude.com/docs/en/agent-sdk/overview>

---

## What Symphony Actually Is

Symphony should be understood as a **service contract** more than a product binary.

The `SPEC.md` defines Symphony as a long-running automation service that:

- continuously reads work from an issue tracker
- creates an isolated workspace for each issue
- runs a coding agent session inside that workspace
- keeps workflow policy in a repository-owned `WORKFLOW.md`
- provides enough observability to debug many concurrent runs

The spec is also explicit about an important architectural boundary:

- Symphony is a scheduler/runner and tracker reader
- ticket writes are usually performed by the coding agent itself
- a run may end at a handoff state such as `Human Review`, not necessarily `Done`

This is important because it means Symphony does **not** replace:

- workflow design
- issue quality standards
- approval policy
- coding standards
- project-specific prompts and skills

It only gives those things a durable runtime.

---

## How Symphony Compares to the Current Repo

### What already exists here

This repository already defines a strong delivery workflow:

- `Linear` is the source of truth for intent, ownership, approval state, and reporting
- `PEP` creates a structured input layer before execution
- `pd-linear-scope` and `pd-context-pack` gather broad awareness before planning
- `pd-guardrail.md` blocks code execution until a plan is approved
- execution report flows back to `Linear`

Relevant local documents:

- [Project Overview](./project-overview.md)
- [Workflow and Approval Model](./workflow-and-approval-model.md)
- [Skills and Rules Architecture](./skills-and-rules-architecture.md)
- [System Architecture](./system-architecture.md)

### What is missing here

The current design is still mostly **session-centric** rather than **issue-centric** at runtime.

Missing capabilities:

- a daemon or long-running service that polls `Linear`
- workspace lifecycle management per issue
- deterministic claiming and reconciliation of active work
- automatic retry on crashes or stalls
- bounded concurrency controls
- orchestration-level observability and operator controls

### Bottom line

Symphony does **not** invalidate the current design.

It validates the strategic direction:

- `Linear` as control plane
- agent execution as an operational loop
- humans reviewing plans and outputs rather than supervising every keystroke

The adaptation path is to add the missing **runtime orchestration layer** without discarding the current **policy layer**.

---

## What To Adopt Directly

These Symphony concepts fit this repo well and should be adopted.

### 1. Issue-centric orchestration

The primary unit of execution should be the `Linear` issue, not a terminal session or a pull request.

Recommended rule:

- one eligible issue maps to one active workspace and one active runner

### 2. Repository-owned workflow contract

OpenAI's spec keeps runtime policy in `WORKFLOW.md`. That is a strong pattern and should be copied.

Recommended use here:

- keep high-level workflow policy versioned with the repo
- use `WORKFLOW.md` to define orchestration behavior, not to replace `cc-pipeline` skills

### 3. Bounded concurrency

The orchestrator should poll `Linear` on a fixed cadence and dispatch work with an explicit concurrency cap.

This protects:

- local developer machines
- CI quota
- API budgets
- review capacity

### 4. Per-issue isolated workspaces

Workspaces should be deterministic and derived from the issue identifier.

Recommended implementation:

- git worktree per issue
- workspace directory name derived from sanitized issue identifier

### 5. Reconciliation loop

The orchestrator should continuously reconcile the external source of truth with local execution state.

That includes:

- issue no longer eligible
- issue moved to terminal state
- issue blocked by dependency
- runner crashed
- workspace orphaned

---

## What Not To Copy Blindly

### 1. OpenAI's Elixir prototype

The Elixir README explicitly says the implementation is prototype software for evaluation and recommends building a hardened implementation from `SPEC.md`.

That means:

- use the prototype for reference
- do not treat it as production-ready architecture

### 2. Codex-specific runtime assumptions

The reference implementation launches Codex in app-server mode and exposes a `linear_graphql` tool to the agent.

This repo should not assume those exact interfaces exist for Claude.

Instead:

- use Claude Code CLI or SDK as the worker runtime
- keep `Linear` access available through project MCP and/or a small orchestration-owned API helper

### 3. Loose approval semantics

Symphony intentionally leaves approval and sandbox policies implementation-defined.

For this repo, that is too loose. The current plan gate should remain explicit and queryable in `Linear`.

### 4. Status model copy-paste

Do not import OpenAI's sample statuses unchanged.

Use states that fit the existing Queen One workflow and reporting expectations.

---

## Target Architecture for Queen One

## Layer 1: Policy layer

This layer already mostly exists.

Responsibilities:

- issue quality standards
- PEP generation and validation
- context gathering rules
- plan format
- approval gate
- reporting format
- team-specific execution rules

Artifacts:

- `.claude/cc-pipeline/commands/*`
- `.claude/cc-pipeline/skills/*`
- `.claude/cc-pipeline/rules/*`
- repository docs under `docs/`

## Layer 2: Orchestrator service

This is the new layer inspired by Symphony.

Responsibilities:

- poll `Linear`
- determine issue eligibility
- create and clean up workspaces
- launch Claude-backed runs
- reconcile issue state with runtime state
- retry failed runs with bounded backoff
- expose status, logs, and operator controls

Suggested responsibilities that should stay in this layer:

- claiming and deduplicating work
- concurrency and scheduling
- workspace lifecycle
- process lifecycle
- metrics and logs

## Layer 3: Claude worker adapter

This layer translates issue work into actual Claude Code execution.

Responsibilities:

- build the prompt from issue, PEP, context pack, and workflow policy
- run Claude Code headless
- parse structured output or stream events
- pass plugin directories and MCP config into the session
- capture logs, exit status, and artifacts

Likely runtime options:

- `claude -p` for simple runs or prototypes
- `Claude Agent SDK` for a more robust long-running worker model

---

## Recommended State Model

The first version should stay simple.

Recommended execution states in `Linear`:

- `Todo`
- `Ready for Planning`
- `Plan Proposed`
- `Plan Approved`
- `In Progress`
- `Human Review`
- `Done`
- `Cancelled`

Optional later:

- `Blocked`
- `Rework`
- `Ready to Merge`
- `Deployed`

Important rule:

- only issues with a valid approved plan should be eligible for implementation runs

This preserves the strongest part of the current delivery model.

---

## Recommended Runtime Contract

The repository should gain a root `WORKFLOW.md` whose job is to tell the orchestrator and the Claude worker how this repo wants to run.

That file should define:

- tracker configuration assumptions
- issue eligibility rules
- polling expectations
- workspace policy
- hooks to run before and after a work session
- agent runtime settings
- prompt template or prompt references
- required handoff behavior
- reporting expectations

It should not duplicate all implementation detail from `cc-pipeline`; it should point to that policy layer where useful.

---

## Claude Code Feasibility

## Why Claude can work here

Anthropic documents exactly the capabilities needed for a first implementation:

- non-interactive execution with `claude -p`
- JSON and `stream-json` output modes
- session naming and resumption
- plugin loading via `--plugin-dir`
- MCP config loading via `--mcp-config`
- permission modes for non-interactive runs

Relevant doc pages:

- CLI reference: <https://code.claude.com/docs/en/cli-usage>
- SDK overview: <https://code.claude.com/docs/en/agent-sdk/overview>

## Recommended runtime choice

For Queen One:

- use `claude -p` only for the first local prototype
- switch to the `Claude Agent SDK` for the first serious orchestrator

Reason:

- CLI print mode is enough to prove the architecture
- SDK is a better fit for long-running orchestration, structured control, and integration with logs and retries

---

## Recommended Build Plan

### Phase 0: repository contract

Deliverables:

- define `Linear` status model
- define approved-plan detection rule
- define `WORKFLOW.md` schema for this repo
- define workspace naming rules
- define the minimal operator commands

Exit criteria:

- the team can explain exactly when an issue is eligible for agent execution

### Phase 1: local single-worker prototype

Deliverables:

- poll one `Linear` project
- pick one eligible issue
- create one worktree
- launch one Claude session headlessly
- write run logs and status locally

Exit criteria:

- a single issue can be picked up, processed, and moved to a handoff state without manual session babysitting

### Phase 2: integrate current pipeline policy

Deliverables:

- run `pd-*` preparation logic as part of worker flow
- enforce plan approval before implementation
- load repo plugins and MCP config automatically
- post execution updates back to `Linear`

Exit criteria:

- the orchestrator respects the same guardrails a human operator would use interactively

### Phase 3: concurrency and recovery

Deliverables:

- bounded concurrency
- run restart policy
- orphan workspace cleanup
- issue reconciliation loop
- operator dashboard or CLI status output

Exit criteria:

- multiple issues can run safely in parallel on one machine

### Phase 4: CI and PR automation

Deliverables:

- watch CI
- retry transient failures
- reopen/rebase as needed
- move issues cleanly into human review

Exit criteria:

- humans review work products, not process noise

---

## Risks and Mitigations

### Risk: plan gate gets bypassed

Mitigation:

- make approved-plan detection a hard orchestrator prerequisite
- fail closed if approval cannot be verified

### Risk: status semantics drift

Mitigation:

- define one explicit status contract in docs and `WORKFLOW.md`
- avoid mixing labels, comments, and custom statuses without a precedence rule

### Risk: Claude runtime behaves differently from Codex assumptions

Mitigation:

- define a thin Claude adapter interface
- keep orchestration logic independent of model vendor

### Risk: runaway machine usage

Mitigation:

- hard cap concurrency
- cap spend where supported
- isolate workspaces
- time-box retries

### Risk: local-only orchestration becomes hard to operate

Mitigation:

- start local
- add logs, checkpoints, and resumability early
- avoid over-building distributed coordination before the single-machine loop is stable

---

## Product Recommendations

### Recommendation 1

Treat Symphony as an **architecture pattern**, not a dependency choice.

### Recommendation 2

Keep `cc-pipeline` as the workflow and guardrail layer. Do not replace it with a thinner generic orchestrator.

### Recommendation 3

Introduce a new orchestration module whose job is only runtime supervision:

- poll
- claim
- run
- reconcile
- recover

### Recommendation 4

Build the first version around `Claude Code`, not around a forced Codex dependency.

### Recommendation 5

Make `WORKFLOW.md` the top-level machine-readable contract for the repo and keep detailed standards in the existing `cc-pipeline` docs and skills.

---

## Suggested Next Deliverables

The next implementation-oriented documents should be:

1. a repo root `WORKFLOW.md`
2. an orchestrator technical design doc
3. a `Linear` state contract doc
4. a Claude worker adapter spec
5. a local operator runbook

The companion document [Resonance Execution Brief](./resonance-execution-brief.md) is written to drive that implementation work directly.

---

## References

### External

- OpenAI announcement, April 27, 2026: <https://openai.com/index/open-source-codex-orchestration-symphony/>
- Symphony repository: <https://github.com/openai/symphony>
- Symphony spec: <https://github.com/openai/symphony/blob/main/SPEC.md>
- Symphony Elixir README: <https://github.com/openai/symphony/blob/main/elixir/README.md>
- Claude Code CLI reference: <https://code.claude.com/docs/en/cli-usage>
- Claude Agent SDK overview: <https://code.claude.com/docs/en/agent-sdk/overview>

### Internal

- [Project Overview](./project-overview.md)
- [System Architecture](./system-architecture.md)
- [Workflow and Approval Model](./workflow-and-approval-model.md)
- [Skills and Rules Architecture](./skills-and-rules-architecture.md)
- [Risks, Weaknesses, and Open Questions](./risks-weaknesses-and-open-questions.md)
