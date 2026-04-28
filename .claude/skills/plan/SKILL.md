---
name: plan
description: Multi-phase project planning with stage-based execution and user checkpoints between stages. Use when user says "plan" or needs structured phased execution with manual approval between stages.
argument-hint: [project-description]
model: opus
context: fork
agent: pm
disable-model-invocation: true
---
# /plan — Phased Project Planning

Create and execute a multi-phase project plan with user checkpoints between stages.

## Workflow
1. PM analyzes request and creates phased plan
2. For plans >10 phases: divide into stages (5-7 phases each)
3. Execute one stage at a time
4. Present stage recap to user between stages
5. User approves next stage or provides feedback

## Rules
- Developer always paired with Tester
- Each phase has clear objective, agent assignment, and completion criteria
- Unit tests mandatory for implementation phases
- Create TODO file in `.claude/memory/todos/`
- Quality keywords trigger additional agents (security, reviewer, documenter)

## Arguments
- `$ARGUMENTS` — Project or feature description
