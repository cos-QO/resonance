---
name: task
description: "Use when user has a specific bounded task (5-20 min) or says 'task', 'do this', 'implement this'. Routes simple work directly, complex work through 2-4 agents. NOT for multi-phase projects (use /planning) or design exploration (use /brainstorm)."
argument-hint: [task-description]
context: fork
agent: pm
disable-model-invocation: true
---
# /task — Focused Task Execution

Execute a focused task with appropriate agent(s).

## Workflow
1. PM analyzes task complexity and scope
2. Simple (1 agent): Route directly to specialist
3. Medium (2-3 agents): Sequential coordination
4. Complex (4+ agents): Escalate to /plan
5. Create TODO, execute, validate, report

## Rules
- Developer always paired with Tester
- Auto-detect if task should escalate to /plan (>4 agents or >20 min)
- Create TODO file even for small tasks
- Follow quality gate rules from CLAUDE.md

## Arguments
- `$ARGUMENTS` — Task description
