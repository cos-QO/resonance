# Skill: Agent Handoff

## Purpose
Ensure clean, context-preserving handoffs between agents in single-chain and compound flows.

## When to Use
- Complex multi-agent chains (3+ agents)
- When context loss between agents is occurring
- Debugging broken handoff sequences
- Establishing handoff standards in new projects

## Prerequisites
- PM-driven architecture active
- Chain checkpoint hook registered
- Agent coordination knowledge loaded

## Components

### Knowledge Loaded
| File | Purpose |
|------|---------|
| `system/agent-handoff-protocol.md` | Tiered handoff definitions |
| `system/agent-coordination.md` | Multi-agent patterns |
| `agents/pm.md` | PM coordination rules |

### Hooks Activated
| Hook | Trigger | Purpose |
|------|---------|---------|
| `chain-checkpoint.py` | Task:* | Logs every agent transition |

### Commands Available
| Command | Purpose |
|---------|---------|
| `/handoff-status` | View current handoff state |
| `/handoff-debug` | Diagnose handoff failures |

## Handoff Tiers

### Tier 1: Inline (Default)
```yaml
trigger: Simple, isolated tasks
format: 3-5 line summary in agent response
example: "✓ Created utils.py with 3 functions"
```

### Tier 2: Section
```yaml
trigger: Multi-file changes, shared state
format: Structured section with context
example: |
  ## Handoff: @developer → @tester
  - Files modified: [auth.py, user.py]
  - State created: UserSession object
  - Test focus: Authentication flow
```

### Tier 3: Full Document
```yaml
trigger: Cross-domain, architecture changes
format: Dedicated handoff.md file
location: /.claude/memory/handoffs/HANDOFF-{id}.md
```

## Workflow

```
┌─────────────────────────────────────────────────────────┐
│ Agent A completes work                                  │
│ ↓                                                       │
│ chain-checkpoint.py logs transition                     │
│ ↓                                                       │
│ Handoff tier detected (1/2/3)                           │
│ ↓                                                       │
│ Context packaged per tier rules                         │
│ ↓                                                       │
│ Agent B receives context + clear instructions           │
└─────────────────────────────────────────────────────────┘
```

## Best Practices

### For Sending Agents
- Summarise what was done, not how
- Include state changes (files, objects, configs)
- Flag dependencies for receiving agent
- Use structured format, not prose

### For Receiving Agents
- Read handoff context before starting
- Acknowledge receipt in first response
- Ask PM for clarification if context insufficient
- Don't re-do work already completed

## Debugging Handoffs

When handoffs break:

1. **Check checkpoint log**: `/.claude/memory/checkpoints/`
2. **Verify tier assignment**: Was correct tier used?
3. **Inspect context size**: Tier 3 needed but Tier 1 used?
4. **Review agent response**: Did it include handoff section?

## Example

```yaml
# Single-chain with proper handoffs
request: "Add user authentication with tests"

flow:
  pm:
    output: Plan with developer → tester chain
    handoff_tier: 2 (multi-file changes expected)

  developer:
    work: Create auth.py, middleware.py, user.py
    handoff: |
      ## Handoff: @developer → @tester
      Files: auth.py, middleware.py, user.py
      New objects: AuthToken, UserSession
      Test focus: login flow, token validation
      Edge cases: expired tokens, invalid creds

  tester:
    receives: Full context from developer
    work: Create test_auth.py with 12 test cases
    handoff_tier: 1 (final agent, simple summary)
```

## Metrics
- **Context preservation**: 94% with Tier 2+
- **Handoff failures**: <2% with proper tier selection
- **Debug time saved**: ~40% with checkpoint logs
