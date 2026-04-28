# Claude Code Kickoff Ticket

## Title

Implement Resonance — the Claude-backed orchestrator for the Queen One agentic pipeline

---

## Goal

Design and build the first usable version of **Resonance** — a `Symphony`-inspired orchestration layer for this repository — so that:

- `Linear` remains the control plane
- `Claude Code` is the execution engine
- the existing `cc-pipeline` workflow remains the policy and guardrail layer
- issue-level work can be supervised continuously without manual session babysitting

This ticket is the starting point for:

- exploration
- technical analysis
- scoping
- planning

It is **not** a request to jump straight into broad implementation without first producing a clear architecture and execution plan.

---

## Problem Statement

The current repository defines a strong supervised agentic workflow, but it lacks a durable orchestration runtime.

What already exists:

- `Linear` is treated as the source of truth for planning, ownership, approvals, and reporting
- `PEP` acts as the structured work input
- the pipeline gathers broad awareness context before planning
- code execution is guarded by a required approved plan
- execution reporting flows back into `Linear`

What is missing:

- a long-running service that continuously polls `Linear`
- issue eligibility detection
- one-workspace-per-issue runtime management
- automated Claude session startup per eligible issue
- orchestration-level retry, reconciliation, and observability

The opportunity is to build **Resonance** by adapting the architectural model from OpenAI's `Symphony` while preserving the stronger planning and approval discipline already present in this repository.

---

## Why This Matters

If this works, the team gets:

- less manual session coordination
- issue-centric execution rather than terminal-centric execution
- a scalable path for supervised multi-issue agent work
- stronger consistency between planning, implementation, and reporting
- a runtime model that can later support more automation without weakening approvals

---

## Required Outcome

The first delivery should produce a clear, documented, local-first orchestration system that can:

1. read eligible work from `Linear`
2. determine if the issue is actually allowed to start
3. create an isolated workspace for that issue
4. launch `Claude Code` non-interactively
5. persist logs and run metadata
6. stop at an explicit human handoff state

The first delivery does **not** need to solve:

- multi-host scheduling
- full production hardening
- autonomous merge/deploy
- perfect parity with OpenAI's Codex-specific implementation

---

## Working Hypothesis

The correct architecture is likely:

- existing `cc-pipeline` remains the policy layer
- a new orchestrator is added as a runtime layer
- a Claude worker adapter translates issue work into headless Claude execution
- the repo gains a root `WORKFLOW.md` as the machine-readable runtime contract

This hypothesis should be tested during exploration rather than assumed to be final.

---

## Scope for This Ticket

Claude Code should use this ticket to complete the following phases in order.

### Phase 1: Exploration

Understand:

- the current repo workflow and guardrails
- what `Symphony` actually defines in `SPEC.md`
- what is prototype-specific in OpenAI's reference implementation
- what Claude Code officially supports for non-interactive or orchestrated execution

### Phase 2: Analysis

Produce a grounded comparison between:

- the current Queen One pipeline
- the Symphony orchestration model
- the practical constraints of running Claude locally

### Phase 3: Scoping

Define the smallest viable first implementation:

- local-first
- single-machine
- bounded concurrency
- strong observability
- explicit approval checks

### Phase 4: Planning

Produce an implementation plan with:

- workstreams
- milestones
- dependencies
- risks
- acceptance criteria

Only after those steps should actual implementation begin.

---

## Primary Questions To Answer

Claude Code should explicitly answer these questions during the exploration and planning work.

### Product and workflow questions

- Which parts of Symphony should be adopted directly?
- Which parts should remain Queen One-specific?
- What must not be weakened from the current approval model?
- What should the first runtime handoff state be?

### Technical architecture questions

- What should the orchestrator own versus the Claude worker?
- Should the first implementation use `claude -p` or the `Claude Agent SDK`?
- What language should the orchestrator use?
- How should workspaces be created and cleaned up?
- How should local run state be persisted?

### Linear workflow questions

- What exact issue states should determine eligibility?
- How should approved-plan state be represented and queried?
- What should happen if an issue becomes ineligible during execution?
- Which updates should the orchestrator post versus which should remain agent-posted?

---

## Constraints

These constraints should be treated as hard unless there is a strong documented reason to change them.

### Workflow constraints

- `Linear` remains the source of truth
- no implementation work should start without an approved plan
- human review remains mandatory
- the first successful end state should usually be `Human Review`, not merge or deploy

### Architecture constraints

- keep orchestration separate from the `cc-pipeline` policy layer
- do not assume Codex-only interfaces
- keep the first version local-first and easy to operate
- prefer explicit documentation over hidden orchestration behavior

### Delivery constraints

- documentation is part of the deliverable, not follow-up work
- operator workflows must be documented
- failure modes and recovery paths must be documented

---

## Expected Deliverables

Claude Code should aim to produce these artifacts as part of the planning and first implementation pass.

### Documentation

- root `WORKFLOW.md`
- `docs/orchestrator-technical-design.md`
- `docs/claude-worker-adapter.md`
- `docs/operator-runbook.md`

### Implementation

- a minimal runnable orchestrator
- a Claude worker adapter
- local persistence for run state and logs
- workspace lifecycle management

### Planning outputs

- implementation milestones
- acceptance criteria
- recommended `Linear` state contract
- explicit risk register

---

## Suggested First Milestones

### Milestone 1

Define the runtime contract.

Output:

- root `WORKFLOW.md`
- documented `Linear` eligibility and approval rules

### Milestone 2

Build a local single-worker prototype.

Output:

- polling loop
- one eligible issue selection
- one isolated workspace
- one headless Claude run

### Milestone 3

Integrate current repo policy.

Output:

- plan-gate enforcement
- repo-specific prompt/context loading
- reporting and handoff behavior

### Milestone 4

Add recovery and observability.

Output:

- logs
- run status visibility
- retry policy
- orphan cleanup behavior

---

## Acceptance Criteria

This ticket should not be considered complete unless the resulting plan and/or implementation makes the following concrete:

- exactly when an issue is eligible to run
- exactly how approved-plan status is verified
- exactly how Claude is launched non-interactively
- exactly where logs and run metadata live
- exactly how workspaces are created and cleaned up
- exactly what state the orchestrator stops at for human review
- exactly how a failed or interrupted run is reconciled

If implementation begins, success for the first version should mean:

- one issue can be picked up from `Linear`
- a dedicated workspace is created
- Claude Code runs headlessly in that workspace
- the run is observable
- the process respects the plan gate

---

## Recommended Internal References

Claude Code should read these local documents first:

- [docs/symphony-claude-adaptation.md](./symphony-claude-adaptation.md)
- [docs/resonance-execution-brief.md](./resonance-execution-brief.md)
- [docs/workflow-and-approval-model.md](./workflow-and-approval-model.md)
- [docs/skills-and-rules-architecture.md](./skills-and-rules-architecture.md)
- [cc-pipeline/README.md](../.claude/cc-pipeline/README.md)

---

## Recommended External References

- OpenAI announcement: <https://openai.com/index/open-source-codex-orchestration-symphony/>
- Symphony repository: <https://github.com/openai/symphony>
- Symphony spec: <https://github.com/openai/symphony/blob/main/SPEC.md>
- Symphony Elixir README: <https://github.com/openai/symphony/blob/main/elixir/README.md>
- Claude Code CLI reference: <https://code.claude.com/docs/en/cli-usage>
- Claude Agent SDK overview: <https://code.claude.com/docs/en/agent-sdk/overview>

---

## Instructions for Claude Code

Use this ticket as the starting artifact for the work.

Expected operating sequence:

1. Read the internal reference docs listed above.
2. Review the external source material, especially Symphony `SPEC.md`.
3. Compare the Symphony model to the current repo architecture.
4. Identify what should be adopted, what should be adapted, and what should be rejected.
5. Draft the smallest viable implementation scope.
6. Produce a concrete implementation plan before broad coding begins.

When documenting conclusions:

- be explicit about tradeoffs
- separate facts from assumptions
- prefer local-first decisions for v1
- fail closed on approval ambiguity

When implementation starts:

- preserve the current plan gate
- preserve human review
- preserve `Linear` as the source of truth

---

## Notes

This work should be approached as a **PM + architect + systems implementation** task, not just a coding task.

The value of the work depends on:

- clarity of the operating model
- quality of the workflow contract
- correctness of approval boundaries
- usability for human operators

If there is ambiguity, document it and convert it into an explicit decision rather than silently assuming.
