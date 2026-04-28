# Memory Protocol

## Memory-First Decision Making
ALL agents MUST consult memory before making ANY decisions:
- Read existing standards from `.claude/memory/standards/` before starting work
- Check project context from `.claude/memory/` to understand current state
- Follow established patterns discovered in previous analysis phases
- Update memory with new learnings and discoveries for future reference

**Memory takes precedence over assumptions — even when not explicitly mentioned.**

## Two-Tier Memory System

### Shared Project Memory (`.claude/memory/`)
Knowledge that all agents share: standards, plans, TODOs, handoffs, discoveries.
Read before every task. Write to share findings with other agents.

### Agent-Specific Memory (`.claude/agent-memory/<name>/`)
Personal learning that persists across sessions (PM, developer, tester).
First 200 lines of MEMORY.md auto-loaded on agent start.
Update after completing work — record what worked, what failed, project quirks.
This is YOUR memory — other agents can't see it.

## Memory Zones — Complete Directory Map

| Directory | Purpose | Who writes | Who reads |
|---|---|---|---|
| `standards/` | Project conventions, architecture, coding style (SACRED) | PM, /prepare | ALL agents |
| `plans/` | PLAN-[id]/ directories with plan details | PM | Main Claude, all agents |
| `todos/` | TODO-YYYYMMDD-[ID].md task files | PM | All agents (find assigned tasks) |
| `handoffs/` | HANDOFF-[PlanID]-P[N]-to-P[N+1].md phase transitions | Completing agent | Next agent in chain |
| `active/` | execution-tracker.json + runtime state | PM creates, hooks update | Main Claude orchestrates |
| `discovery/` | Research findings, brainstorm designs | researcher, /brainstorm | PM (for planning) |
| `reports/` | verify/, troubleshooting/, training/, errors/ | tester, troubleshooter, trainer | PM, agents |
| `templates/` | Reusable templates for plans, TODOs, handoffs, reports | Read-only | All agents |
| `temp/` | Temporary coordination files (troubleshooter teams) | troubleshooter | troubleshooter team |
| `project/` | Project context, roadmap | PM | All agents |
| `archive/` | Completed plans and work (moved after completion) | PM | Reference only |
| `watchdog/` | Quality monitoring data and findings | watchdog | PM, reviewer |

## Handoff Protocol

When completing a phase, the finishing agent MUST write a handoff document:

**Path**: `/.claude/memory/handoffs/HANDOFF-[PlanID]-P[N]-to-P[N+1].md`
**Template**: `/.claude/memory/templates/handoff-template.md`

The handoff must include:
1. **What was done** — deliverables with file paths
2. **Key decisions** — choices made and why
3. **For next agent** — what to start with, must-know context
4. **Issues** — problems found, fixed or unfixed

The next agent reads this handoff BEFORE starting work. The SubagentStart hook also injects handoff paths from the execution tracker's `handoff_files` field.

## Agent Memory Update Protocol

After completing ANY task, agents with persistent memory (PM, developer, tester) MUST update:

**Path**: `/.claude/agent-memory/<name>/MEMORY.md`
**Format**: Append new entries under the appropriate section heading
**Rule**: Keep under 200 lines — if approaching limit, summarize oldest entries

What to record:
- **PM**: plan patterns, user preferences, estimation accuracy, agent effectiveness
- **Developer**: codebase patterns, what worked/failed, framework quirks, test feedback
- **Tester**: flaky tests, coverage gaps, tool availability, verify history

## Standards Are Sacred
- `standards/conventions.md` — single source of truth for project patterns
- `standards/tree.md` — authoritative file tree map
- `standards/folder-structure.md` — where files belong
- `standards/security-standards.md` — security requirements

Always check these exist before starting. Create if missing.
