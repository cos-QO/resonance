# Skill: Compound Coordination

## Purpose
Enable parallel multi-agent work through isolated sub-plans with coordinated merging.

## When to Use
- Large codebase investigation (3+ domains)
- Multi-domain feature development
- Parallel exploration of different areas
- Competitive analysis (different approaches)
- Team simulation (different perspectives)

## Prerequisites
- Multiple terminal windows available (3-6 recommended)
- Clear objective that divides into independent areas
- Understanding of scope boundaries

## Components

### Commands Used
| Command | Purpose |
|---------|---------|
| `/mode compound` | Set execution mode |
| `/compound-start` | Initialise compound plan |
| `/compound-join` | Join a sub-plan from terminal |
| `/compound-sync` | Merge sub-plans |
| `/compound-status` | View current status |
| `/watchdog status` | Monitor all sub-plans |

### Knowledge Loaded
- `system/subplan-isolation.md` - Isolation protocol
- `system/agent-coordination.md` - Coordination patterns
- `system/agent-handoff-protocol.md` - Handoff tiers

### Agents Involved
- **PM**: Creates parent plan and sub-plans
- **@watchdog**: Monitors all sub-plans continuously
- **Domain agents**: Work in isolated sub-plans

## Workflow

```
┌─────────────────────────────────────────────────────────┐
│ 1. INITIATE                                             │
│    /compound-start "objective" --subplans "a, b, c"     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. JOIN (each terminal)                                 │
│    Terminal 2: /compound-join PLAN-001 A                │
│    Terminal 3: /compound-join PLAN-001 B                │
│    Terminal 4: /compound-join PLAN-001 C                │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. WORK (parallel, isolated)                            │
│    Each agent works within scope boundaries             │
│    @watchdog monitors continuously                      │
│    Coordinator checks: /watchdog status                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 4. SYNC (when all complete)                             │
│    /compound-sync PLAN-001                              │
│    Merges findings → synthesis.md                       │
│    Auto-commits with compound message                   │
└─────────────────────────────────────────────────────────┘
```

## Isolation Layers

### Layer 1: File Scope
Each SUBPLAN has allowed/forbidden paths.

### Layer 2: Memory Scope
Each SUBPLAN writes only to its own `claude/memory/compound/PLAN-{id}/SUBPLAN-X/` directory.

### Layer 3: Hook Enforcement
`compound-scope-enforcement.py` blocks cross-boundary access.

### Layer 4: Watchdog Monitoring
@watchdog detects violations and conflicts in real-time.

## Best Practices

### Scope Definition
- Keep scopes non-overlapping
- Use glob patterns for clarity
- Include test directories with source

### During Execution
- Check `/watchdog status` regularly
- If blocked, note in findings (don't wait silently)
- Discover cross-cutting concerns → note for sync

### Sync Phase
- Review conflicts before syncing
- Use synthesis for combined insights
- Plan follow-up work from synthesis

## Example Usage

### Scenario: Refactor Payment System
```bash
# Terminal 1 (Coordinator)
/compound-start "Refactor payment system" --subplans "api,database,frontend"

# Terminal 2
/compound-join PLAN-20260202-A1 A
# → @developer focuses on API layer

# Terminal 3
/compound-join PLAN-20260202-A1 B
# → @data focuses on database layer

# Terminal 4
/compound-join PLAN-20260202-A1 C
# → @developer focuses on frontend

# Terminal 1 (when all complete)
/compound-sync PLAN-20260202-A1
# → Merges all findings, auto-commits
```

## Metrics
- **Time savings**: ~61% for multi-domain tasks
- **Overhead**: <50ms per operation
- **Conflict detection**: Real-time
