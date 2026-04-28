# Agent Interaction Model

## Purpose

This document extends the Claude/Resonance exploration with a practical model for using multiple agents together, including:

- `Claude` as the primary execution engine
- optional `Codex` participation as a sidecar or specialist
- structured handoffs
- communication boundaries
- ownership rules
- failure and retry behavior

The goal is to answer two related questions:

1. Can Queen One move primarily to `Claude` while still using `Codex` selectively?
2. How difficult is it to build reliable agent-to-agent handoffs and communication?

---

## Executive Summary

Yes, a mixed-agent model is viable.

The right pattern is to separate agents by **role and authority**, not by trying to have multiple agents freely co-own the same work at the same time.

Recommended default:

- `Claude` is the primary agent for workflow execution
- `Codex` is used selectively for bounded secondary tasks
- one orchestrator owns task assignment and state transitions
- all meaningful handoffs happen through structured artifacts rather than loose free-form chat

The simple version is easy to build.

The hard part is not message passing. The hard part is coordination:

- shared state drifting
- unclear ownership
- overlapping edits
- stale assumptions
- poor handoff quality
- missing auditability

That means the system should optimize for disciplined handoffs rather than conversational richness.

---

## Core Position

### Use one primary agent

For a given issue, there should normally be one primary execution agent.

In the Queen One target model, that should usually be `Claude`.

Why:

- one clear owner per issue
- simpler workspace and branch management
- fewer conflicting assumptions
- easier audit trail

### Use secondary agents only for bounded work

Secondary agents such as `Codex` should be invoked when they have a clearly scoped purpose, for example:

- code review
- adversarial review
- research
- debugging a dead-end
- isolated experimentation
- alternative implementation proposals

They should not default to co-owning the same task interactively unless ownership and outputs are tightly bounded.

---

## Recommended Hybrid Model

## Default operating model

- `Claude` owns the issue lifecycle
- `Claude` reads the issue, context, plan, and repo rules
- `Claude` performs implementation or coordinates it
- `Codex` is invoked only when a secondary perspective or specialized bounded execution is useful

This means `Claude` remains the system-of-record agent for the issue, even when `Codex` participates.

## Good use cases for `Codex`

Use `Codex` as a sidecar for:

- second-opinion code review
- adversarial review before merge
- alternative design proposals
- isolated debugging on a tricky failure
- bounded implementation experiments in a separate workspace
- regression hunting after a main implementation pass

## What to avoid

Avoid these patterns by default:

- two agents editing the same files concurrently
- two agents planning independently for the same issue
- switching primary ownership mid-task without a formal handoff
- using one agent for planning and another for execution without a shared plan artifact
- treating informal chat as the source of truth

---

## Difficulty Model

The difficulty depends heavily on the depth of coordination required.

### Low difficulty

One primary agent does the work. A secondary agent provides advice or review only.

Examples:

- `Claude` implements, `Codex` reviews
- `Claude` plans, `Codex` critiques the plan

This is straightforward and reliable.

### Medium difficulty

Multiple agents work in parallel on disjoint tasks with strict ownership.

Examples:

- one agent handles backend
- one agent handles frontend
- one agent handles test hardening

This can work well if write scopes are clearly separated.

### High difficulty

Multiple agents collaborate dynamically on the same issue with shared mutable state and back-and-forth negotiation.

Examples:

- both agents edit the same feature branch
- planning and implementation are split across agents with ongoing mutual adjustments

This becomes fragile quickly.

### Very high difficulty

A fully autonomous multi-agent system manages:

- assignment
- execution
- retries
- rework
- CI reactions
- PR review
- merge preparation
- human approval handoffs

This is possible, but it requires much stronger orchestration, state modeling, and observability than demo-style multi-agent chat suggests.

---

## Why Multi-Agent Coordination Gets Hard

The main challenge is not that agents cannot communicate. The challenge is that communication without discipline produces unreliable systems.

Common failure modes:

- agents work from different assumptions
- one agent changes direction and the other never re-syncs
- outputs transfer without rationale
- two agents touch the same files or branch
- ownership of decisions is unclear
- long-running tasks drift away from the original plan
- operator visibility is weak

Difficulty rises sharply when these factors increase:

- parallelism
- shared write access
- task duration
- ambiguity of authority

---

## Recommended Control Principles

### 1. One orchestrator decides

There should be one orchestrator agent or service that decides:

- who owns the task
- when a sidecar agent is invoked
- what the sidecar is allowed to do
- when a handoff is complete

This should not be left to ad hoc agent conversation.

### 2. One canonical source of truth

Use explicit sources of truth:

- `Linear` for issue state and approvals
- local plan and context artifacts for execution state

Agent chat should never be the canonical state store.

### 3. Explicit ownership

Every agent task should have explicit ownership for:

- the objective
- the workspace
- the allowed write scope
- the expected output

### 4. Structured handoffs

Handoffs should happen through a defined artifact format, not free-form summaries alone.

### 5. Queryable state transitions

Task state should be represented in a way the orchestrator can inspect and reason about.

Good examples:

- explicit issue statuses
- explicit run states
- explicit artifact locations

Bad examples:

- “someone mentioned it in chat”
- “the branch probably means it is in review”

### 6. Reconciliation over optimism

The orchestrator should reconcile actual state continuously rather than assuming prior handoffs remain valid forever.

---

## Recommended Handoff Protocol

The basic handoff object should include:

- task ID
- goal
- scope
- constraints
- inputs
- expected output
- current owner
- next owner
- status
- blocking questions

This is enough for a first version.

## Suggested handoff template

```md
## Handoff

- Task ID: <issue-id or run-id>
- Goal: <what outcome is required>
- Scope: <what is in / out>
- Constraints: <approval, architecture, policy, runtime>
- Inputs: <docs, files, issue links, plan references>
- Current owner: <agent or service>
- Next owner: <agent or human>
- Expected output: <patch, review, summary, recommendation, test result>
- Status: <active, blocked, complete, waiting-review>
- Blocking questions: <only unresolved questions>
```

---

## Recommended Role Model

## Role 1: Orchestrator

Responsibilities:

- poll `Linear`
- determine task eligibility
- assign ownership
- create workspaces
- launch primary or sidecar runs
- reconcile state
- stop or reassign work when needed

Authority:

- highest runtime authority

## Role 2: Primary execution agent

Recommended default:

- `Claude`

Responsibilities:

- own the issue lifecycle during execution
- interpret plan and context
- implement or coordinate implementation
- produce execution artifacts
- prepare for human review handoff

Authority:

- owns the active issue workspace unless reassigned

## Role 3: Sidecar specialist agent

Recommended default:

- `Codex` when needed

Responsibilities:

- bounded review, debugging, research, or experiment work
- return explicit outputs to the orchestrator or primary agent

Authority:

- advisory by default
- write authority only in bounded, isolated scopes

## Role 4: Human reviewer or approver

Responsibilities:

- approve plans
- review PRs
- resolve ambiguity
- make release decisions

Authority:

- final authority on protected gates

---

## Recommended Claude vs Codex Split

## Claude should usually own

- issue intake
- context synthesis
- planning
- implementation
- execution reporting
- main human handoff preparation

## Codex is well suited for

- second-opinion review
- adversarial review
- regression detection
- isolated debugging
- alternative solution exploration
- bounded implementation experiments

## Default rule

If there is doubt, do not split ownership. Keep `Claude` primary and invoke `Codex` only as a specialist.

---

## Communication Rules

### Rule 1

Agents should communicate through structured artifacts whenever the output matters.

### Rule 2

Conversation can help with local reasoning, but task state must be reflected in durable records.

### Rule 3

A handoff is not complete until:

- the output artifact exists
- the next owner is explicit
- unresolved questions are explicit

### Rule 4

No shared write access without an explicit ownership rule.

### Rule 5

When the primary plan changes materially, downstream agents must be re-briefed.

---

## Failure and Retry Model

### Failure cases to expect

- sidecar agent returns incomplete work
- primary agent changes plan after sidecar started
- workspace conflicts occur
- run crashes or stalls
- issue state changes during execution

### Recommended handling

- abort or pause stale sidecar work if the parent plan changes materially
- never merge overlapping edits without explicit reconciliation
- prefer restarting a bounded sidecar task rather than improvising around stale context
- record why the retry happened

### Important principle

Retries should preserve context about:

- what failed
- why it failed
- what inputs were used
- whether the plan changed since the last attempt

---

## Observability Requirements

If the system involves handoffs between agents, the operator needs visibility into:

- which agent owns the issue
- which sidecar tasks are active
- what workspace each task uses
- what state each task is in
- what the last successful handoff was
- what is blocked and why

Without this, multi-agent orchestration becomes difficult to trust.

---

## Practical Recommendation for Queen One

For this repository, the safest near-term model is:

- `Claude` as the primary issue owner
- `Codex` as a sidecar for review, debugging, and alternative proposals
- orchestrator-managed handoffs
- no uncontrolled multi-agent co-editing
- structured handoff artifacts
- `Linear` plus local plan files as the source of truth

This gets most of the upside of hybrid-agent collaboration without the fragility of “agents chatting freely” as the operating model.

---

## Suggested Next Design Artifacts

If Queen One chooses to support multi-agent participation intentionally, the next docs should be:

1. a handoff schema
2. an agent role and authority matrix
3. a sidecar invocation policy
4. a workspace ownership policy
5. a run-state and retry-state model

These should sit alongside the Symphony adaptation and Resonance execution brief.

---

## Related Docs

- [Symphony Adaptation for Resonance](./symphony-claude-adaptation.md)
- [Resonance Execution Brief](./resonance-execution-brief.md)
- [Resonance Kickoff Ticket](./resonance-kickoff-ticket.md)
- [Workflow and Approval Model](./workflow-and-approval-model.md)
- [Skills and Rules Architecture](./skills-and-rules-architecture.md)
