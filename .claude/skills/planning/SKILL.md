---
name: planning
description: Full project planning and auto-execution for large multi-phase work. Triggers when user explicitly asks to plan and build a project, system, or major feature from scratch. NOT for single tasks (use /task), quick fixes, or questions. Requires clear project scope description.
argument-hint: [project-description]
model: opus
context: fork
agent: pm
---
# /planning — Auto-Execution Planning

Execute a 5-stage planning and execution workflow:

1. **Request Analysis** (3-5 min) — PM deeply analyzes request using memory and project context
2. **Pre-Scoping** (10-20 min) — Spawn researcher, troubleshooter, architect in parallel to gather data
3. **Plan Creation** (5-10 min) — PM creates master plan with phases, agents, checkpoints
4. **Auto-Execution** (20-180 min) — Execute plan phases sequentially, pause only on blockers
5. **Completion Report** (5-10 min) — PM + documenter generate comprehensive report

## Rules
- Each phase includes mini-scoping at start and validation at end
- Developer phases ALWAYS include unit tests
- Watchdog L3 checkpoint every 3-5 phases
- PM coordinates but NEVER executes
- Pause on: blockers, critical decisions, validation failures, test failures
- All artifacts stored in `.claude/memory/planning/[PLAN-ID]/`

## Plan Structure
- Present pre-execution report to user before starting auto-execution
- Track progress in `execution-status.json`
- Generate completion report with deliverables, metrics, learnings

## Arguments
- `$ARGUMENTS` — Project description to plan and execute
