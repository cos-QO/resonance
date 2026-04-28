# 🚨 AGENTIC FLOW CONFIGURATION

## Execution Mode
**SINGLE-CHAIN** (default): PM → Agent₁ → Agent₂ → Auto-commit
**COMPOUND**: PM → SUBPLANs → Parallel terminals → Sync → Auto-commit

PM auto-detects mode. Override: `/mode single` or `/mode compound`

## Core Rules (NEVER VIOLATE)

1. **PM FIRST** - Every request → `Task(subagent_type='pm')`
2. **PM CREATES TODO** - All tasks tracked in `/.claude/memory/todos/`
3. **YOU EXECUTE** - Main Claude runs PM's agent chain via Task tool
4. **NEVER SKIP PM** - Even trivial tasks go through PM
5. **AUTO-COMMIT** - Completion triggers git commit hook

## Default Flow

```yaml
step_1: Task(pm) → Creates TODO with agent chain
step_2: Read TODO file
step_3: Execute agents sequentially via Task tool
step_4: Report results → Auto-commit triggers
```

## Mandatory Pairing

| Trigger | Add Agent |
|---------|-----------|
| @developer | Always add @tester |
| auth/password/token/payment | Add @security |
| API/endpoint/REST | Add @documenter |
| deploy/release/production | Add @reviewer |
| system/architecture/design | Prepend @architect |

## TODO Tracking

- **Path**: `/.claude/memory/todos/PLAN-{id}-todolist.md`
- **Format**: `TODO-YYYYMMDD-A1-001`
- **Rule**: All agents read/update assigned TODOs

## Watchdog

- **L1**: Quick check after each agent
- **L2**: Mid-execution standards check
- **L3**: Final quality gate

## Compound Commands

```
/compound-start "obj" --subplans "a,b,c"  # Init
/compound-join PLAN-ID A                   # Join sub-plan
/watchdog status                           # Monitor
/compound-sync PLAN-ID                     # Merge
```

## Agents

**Core**: pm, orchestrator, developer, tester, security, reviewer, documenter, watchdog
**Strategic**: architect, ux-designer, product-manager, business-analyst
**Support**: researcher, data, troubleshooter

## Knowledge Loading

PM loads contextually (never all at once):
- Simple → `pm/quick-execution-patterns.md`
- Complex → `pm/planning-protocol.md` + `system/agent-coordination.md`
- Security → `pm/security-planning-protocol.md`

---
<!-- END AGENTIC BLOCK - Do not remove this marker -->
