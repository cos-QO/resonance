# Skill: Progress Tracking

## Purpose
Real-time visibility into plan execution, TODO state, and agent progress across single-chain and compound flows.

## When to Use
- Monitoring long-running plans
- Debugging stalled executions
- Coordinating multi-terminal compound work
- Auditing completed plans
- Understanding where time is spent

## Prerequisites
- PM-driven architecture active
- TODO system configured
- Progress hooks registered

## Components

### Knowledge Loaded
| File | Purpose |
|------|---------|
| `system/todo-tracking-system.md` | TODO lifecycle and format |
| `system/todowrite-system.md` | TodoWrite tool integration |
| `pm/planning-protocol.md` | How PM creates tracked plans |

### Hooks Activated
| Hook | Trigger | Purpose |
|------|---------|---------|
| `progress-tracker.py` | TodoWrite | Updates progress state |
| `todo-sync.py` | Task:* | Syncs TODO across agents |
| `todowrite-validator.py` | TodoWrite | Validates TODO format |
| `chain-checkpoint.py` | Task:* | Logs agent transitions |

### Commands Available
| Command | Purpose |
|---------|---------|
| `/progress` | View current plan progress |
| `/todos` | List all active TODOs |
| `/plan-status` | Detailed plan state |

## Progress States

```yaml
todo_states:
  pending: "Not started"
  in_progress: "Currently executing"
  blocked: "Waiting on dependency"
  completed: "Successfully finished"
  failed: "Execution failed"
  skipped: "Intentionally bypassed"
```

## Tracking Locations

| Type | Location | Purpose |
|------|----------|---------|
| TODOs | `/.claude/memory/todos/PLAN-{id}-todolist.md` | Task list |
| Checkpoints | `/.claude/memory/checkpoints/` | Agent transitions |
| Progress | `/.claude/memory/progress/` | Real-time state |
| Archives | `/.claude/memory/archive/` | Completed plans |

## Workflow

```
┌─────────────────────────────────────────────────────────┐
│ PM creates plan → TODO file generated                   │
│ ↓                                                       │
│ Each agent updates TodoWrite                            │
│ ↓                                                       │
│ progress-tracker.py updates state                       │
│ ↓                                                       │
│ /progress shows real-time status                        │
│ ↓                                                       │
│ Plan completes → auto-commit → archive                  │
└─────────────────────────────────────────────────────────┘
```

## TODO Format

```markdown
# PLAN-20260202-A1 TODO List

## Status: IN_PROGRESS
- Started: 2026-02-02 14:30:00
- Current Agent: @developer
- Progress: 2/5 (40%)

## Tasks

### TODO-20260202-A1-001
- **Task**: Analyse existing auth structure
- **Agent**: @researcher
- **Status**: ✅ COMPLETED
- **Duration**: 3m 24s

### TODO-20260202-A1-002
- **Task**: Implement new auth flow
- **Agent**: @developer
- **Status**: 🔄 IN_PROGRESS
- **Started**: 2026-02-02 14:35:00

### TODO-20260202-A1-003
- **Task**: Write authentication tests
- **Agent**: @tester
- **Status**: ⏳ PENDING
- **Depends**: TODO-20260202-A1-002
```

## Compound Mode Tracking

In compound mode, tracking spans multiple terminals:

```yaml
compound_tracking:
  parent_plan: PLAN-20260202-A1
  subplans:
    A:
      terminal: 2
      agent: @developer
      status: in_progress
      progress: 3/5
    B:
      terminal: 3
      agent: @data
      status: completed
      progress: 4/4
    C:
      terminal: 4
      agent: @developer
      status: pending
      progress: 0/3

  overall: 7/12 (58%)
```

## Best Practices

### During Execution
- Check `/progress` regularly in long plans
- Use TODO dependencies to prevent race conditions
- Update status immediately when blocked
- Include duration estimates for planning

### After Completion
- Review archived plans for patterns
- Analyse time distribution across agents
- Identify bottleneck agents
- Adjust future estimates based on actuals

## Debugging Stalled Plans

When progress stops:

1. **Run `/progress`**: See which TODO is stuck
2. **Check agent state**: Is agent waiting on something?
3. **Review dependencies**: Circular dependency?
4. **Inspect checkpoints**: Did agent crash?
5. **Check watchdog**: Any violations blocking?

## Integration with Watchdog

```yaml
watchdog_integration:
  L1_check:
    - Verify TODO updated after each agent
    - Flag if no progress in 5 minutes

  L2_check:
    - Validate TODO format
    - Check for orphaned tasks
    - Detect stuck in_progress items

  L3_check:
    - Confirm all TODOs resolved
    - Verify no pending items remain
    - Archive plan on completion
```

## Metrics
- **Tracking accuracy**: 99.2%
- **Update latency**: <100ms
- **Archive retention**: 30 days default
- **Compound sync overhead**: <50ms
