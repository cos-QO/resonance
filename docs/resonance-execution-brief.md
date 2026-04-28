# Resonance — Execution Brief

## Purpose

This document is the implementation brief to hand to `Claude Code` for the first real execution pass.

It translates the product and architecture decision in [Symphony Adaptation for Resonance](./symphony-claude-adaptation.md) into a concrete work package with scope, deliverables, constraints, milestones, and acceptance criteria.

This brief assumes the team wants:

- `Linear` as the control plane
- `Claude Code` as the coding agent runtime
- the existing `cc-pipeline` model retained as the workflow and guardrail layer

---

## Problem Statement

The current repository documents a strong supervised agentic workflow, but it does not yet include a long-running orchestration service that can:

- continuously read eligible work from `Linear`
- allocate one isolated workspace per issue
- launch a Claude-backed agent for each active issue
- keep issue-level work moving without human session babysitting

OpenAI's Symphony validates this direction, but the Queen One implementation must remain compatible with `Claude Code`, the existing `pd-*` pipeline, and the current approval model.

---

## Primary Objective

Design and implement the first usable version of **Resonance** — the Claude-backed orchestrator for this repository, inspired by Symphony's operational model.

The implementation should prove that the Queen One workflow can run issue-level work continuously from `Linear` while preserving mandatory human gates.

---

## Non-Goals

The first implementation should **not** attempt all of the following:

- distributed multi-host orchestration
- production-grade fleet scheduling
- full auto-merge and deployment automation
- perfect parity with OpenAI's Codex-specific Elixir prototype
- replacing the current `cc-pipeline` command and skill layer

The first version should optimize for correctness, clarity, and observability on a single machine.

---

## Required Outputs

Claude Code should produce the following artifacts unless a stronger implementation shape is discovered during execution.

### 1. Root `WORKFLOW.md`

Purpose:

- define the repository-owned runtime contract for the orchestrator

Minimum contents:

- workflow purpose
- issue eligibility rules
- required `Linear` states
- approved-plan requirement
- workspace policy
- hooks and setup expectations
- Claude runtime configuration assumptions
- expected handoff states
- reporting expectations

### 2. Orchestrator design doc

Suggested path:

- `docs/orchestrator-technical-design.md`

Minimum contents:

- component diagram
- polling loop design
- workspace lifecycle
- issue claiming model
- run state model
- retry policy
- logging and observability
- failure modes

### 3. Claude worker adapter spec

Suggested path:

- `docs/claude-worker-adapter.md`

Minimum contents:

- how Claude is launched
- CLI vs SDK decision
- prompt assembly inputs
- plugin and MCP loading
- output parsing contract
- permission mode assumptions
- resumption and retry behavior

### 4. Minimal runnable implementation

Suggested shape:

- a local service or CLI under a clearly named directory such as `orchestrator/` or `apps/orchestrator/`

Minimum capabilities:

- poll `Linear`
- detect one eligible issue
- create one isolated workspace
- launch one Claude-backed run
- persist logs and run state locally
- stop or mark complete on a defined handoff state

### 5. Operator runbook

Suggested path:

- `docs/operator-runbook.md`

Minimum contents:

- setup steps
- required environment variables
- how to start the orchestrator
- how to inspect active runs
- how to stop a stuck run
- how to clean orphan workspaces
- common failure cases

---

## Recommended Implementation Scope

## Milestone 1: Define the repo contract

Tasks:

- create `WORKFLOW.md`
- define the exact `Linear` statuses or other signals used for eligibility
- define how approved plans are detected
- define workspace naming and location rules

Acceptance criteria:

- a human can read the repo contract and determine exactly when an issue may be picked up for implementation

## Milestone 2: Build a single-worker local loop

Tasks:

- poll `Linear` on a fixed cadence
- select one eligible issue
- create a git worktree for that issue
- run Claude headlessly in that workspace
- store run metadata and logs locally

Acceptance criteria:

- one issue can be processed end-to-end without a human manually opening a Claude session

## Milestone 3: Integrate the existing `pd-*` policy

Tasks:

- ensure plan approval is checked before implementation
- ensure the worker uses the current docs and pipeline conventions
- make sure reporting to `Linear` is preserved
- load required plugin dirs and MCP config automatically

Acceptance criteria:

- the orchestrator follows the same mandatory workflow rules as the current interactive process

## Milestone 4: Add recovery and observability

Tasks:

- restart failed runs under bounded conditions
- detect ineligible or terminal issues and stop matching runs
- record structured logs
- expose a simple status view

Acceptance criteria:

- the operator can diagnose why a run is active, failed, stopped, or waiting

---

## Product Rules That Must Be Preserved

These are non-negotiable unless explicitly changed by a later decision.

### 1. `Linear` remains the source of truth

The orchestrator may cache local state, but local state must never become the canonical source of issue truth.

### 2. No implementation without an approved plan

This repo's strongest control is the plan gate. The orchestrator must preserve it.

### 3. Human review remains mandatory

The first successful end state should normally be a handoff state such as `Human Review`, not autonomous merge and deploy.

### 4. Repo-owned workflow policy

Runtime behavior should be documented and versioned with the repository.

### 5. Clear separation of responsibilities

Keep these concerns separate:

- `cc-pipeline`: workflow and policy
- orchestrator: scheduling and runtime supervision
- Claude worker: implementation execution

---

## Technical Recommendations

### Recommendation: start with `claude -p`, plan for SDK

Reasoning:

- `claude -p` is the fastest route to a proof of concept
- the `Claude Agent SDK` is a better long-term fit for robust orchestration

Relevant docs:

- CLI reference: <https://code.claude.com/docs/en/cli-usage>
- Agent SDK overview: <https://code.claude.com/docs/en/agent-sdk/overview>

### Recommendation: keep orchestration vendor-neutral where possible

The orchestrator should not hardcode Codex-specific assumptions. Only the worker adapter should know how Claude is launched and observed.

### Recommendation: use git worktrees for isolation

This is the cleanest path for:

- parallel issue work
- easy cleanup
- deterministic workspace roots

### Recommendation: fail closed on approval ambiguity

If the orchestrator cannot verify that the plan is approved, it should not start implementation work.

### Recommendation: start with bounded local concurrency

Do not optimize for many parallel runs before:

- status semantics are stable
- logs are readable
- workspace cleanup is reliable

---

## Open Decisions Claude Code Should Resolve

Claude Code should explicitly answer these during implementation and record the result in docs.

### 1. Where should approved-plan state live in `Linear`?

Options:

- custom status
- label
- structured comment convention

Expected outcome:

- choose one queryable mechanism and document it

### 2. What is the first orchestrator implementation language?

Candidate choices:

- Python
- TypeScript

Expected outcome:

- choose the smallest language/runtime that fits local ops and Claude integration best

### 3. Should the first worker use CLI print mode or SDK?

Expected outcome:

- choose one for v1 and document why

### 4. How should repo plugins and MCP config be loaded automatically?

Expected outcome:

- define the canonical startup command

### 5. What local persistence is needed?

Expected outcome:

- define where run metadata, logs, and workspace mappings live

---

## Suggested Task Breakdown in Linear

If this work is split into child tasks, use something close to the following structure:

1. Define `Linear` orchestration state model and approved-plan contract
2. Draft root `WORKFLOW.md`
3. Design orchestrator architecture and local persistence model
4. Implement single-worker polling and workspace lifecycle
5. Implement Claude worker adapter
6. Integrate `cc-pipeline` rules and reporting requirements
7. Add recovery, cleanup, and operator status output
8. Write runbook and usage documentation

---

## Acceptance Criteria for the First Real Delivery

The first real delivery should be considered successful only if all of the following are true:

- the repo has a root `WORKFLOW.md`
- the orchestrator can read `Linear` and pick up an eligible issue
- the orchestrator creates an isolated workspace for that issue
- the orchestrator can launch Claude Code non-interactively
- implementation work does not begin unless the plan is approved
- logs and run metadata are persisted locally
- a human can see why a run is active, blocked, failed, or complete
- the orchestrator can stop work cleanly when the issue becomes ineligible or terminal

---

## Implementation Constraints

Claude Code should work within these constraints unless there is a strong reason to change them:

- preserve existing repo docs and pipeline concepts
- do not weaken the approval model to match a simpler demo workflow
- keep the first version local-first and easy to operate
- prefer explicit documentation over clever hidden behavior
- produce operator-facing docs as part of implementation, not after

---

## References

### External

- OpenAI announcement, April 27, 2026: <https://openai.com/index/open-source-codex-orchestration-symphony/>
- Symphony spec: <https://github.com/openai/symphony/blob/main/SPEC.md>
- Symphony Elixir README: <https://github.com/openai/symphony/blob/main/elixir/README.md>
- Claude Code CLI reference: <https://code.claude.com/docs/en/cli-usage>
- Claude Agent SDK overview: <https://code.claude.com/docs/en/agent-sdk/overview>

### Internal

- [Symphony Adaptation for Resonance](./symphony-claude-adaptation.md)
- [Workflow and Approval Model](./workflow-and-approval-model.md)
- [Skills and Rules Architecture](./skills-and-rules-architecture.md)
- [System Architecture](./system-architecture.md)
