# System Architecture

## Overview

The system has three main control planes:

1. `Linear` for intent, context, ownership, approval state, and documentation
2. `Claude Code` or `Cursor` for planning and execution
3. `GitHub` for review, CI, merge, and deployment governance

## Systems Of Record

### Linear

Use Linear as the source of truth for:

- project and product intent
- issue ownership
- approval state
- project documents
- final execution history
- cross-team references

### Repo-local memory

Use repo-local memory as the agent working ledger for:

- context packs
- plan mirrors
- checkpoints
- handoffs
- draft reports
- execution artifacts useful across sessions

This data should support the agent, not replace Linear.

### GitHub

Use GitHub as the enforcement layer for:

- pull request review
- CODEOWNERS review
- CI status checks
- merge restrictions
- deployment approvals where needed

## Component Responsibilities

### Linear responsibilities

- store PRDs, specs, decisions, and project-level context
- track issues, priority, assignees, and status
- provide MCP-accessible context for agents
- receive final summaries, outcomes, and follow-up items

### Agent responsibilities

- gather context before planning
- create structured plans
- maintain working artifacts during execution
- implement changes
- run verification
- post clean summaries back to Linear

### Human responsibilities

- approve plan before execution
- clarify ambiguous intent
- review the pull request
- approve deployment when needed
- confirm acceptance of delivered outcome

## Architecture Constraint

Avoid treating the same field as editable truth in multiple places.

The practical rule should be:

- intent and status live in Linear
- implementation state lives locally while work is active
- merge and deployment authority live in GitHub

## Tool Selection Model

### Cursor

Best suited when you want:

- direct issue-to-agent execution
- background agents
- fast implementation loops
- PR creation tied closely to ticket execution

### Claude Code

Best suited when you want:

- deterministic hooks
- local memory and checkpoint discipline
- custom orchestration behavior
- stronger control over plan, report, and handoff artifacts

## Recommended Combined Approach

Keep the same upstream process regardless of which coding tool runs the work:

- Linear defines and approves the work
- the agent execution engine performs the work
- GitHub enforces review and merge rules

That allows different teams to use different agent environments without breaking the operating model.
