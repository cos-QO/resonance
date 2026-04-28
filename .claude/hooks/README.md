# Hooks — Automated Orchestration

12 hook scripts wired across 9 events that enforce workflow rules without requiring agent cooperation.

## Active Hooks

| Event | Script | Purpose |
|-------|--------|---------|
| **SessionStart** | `session-context.py` | Checks for active tracker, pending TODOs, skill drafts on session start |
| **PreToolUse** (security agent) | `online-security-research.py` | Injects latest security advisories before security agent runs |
| **PostToolUse** (TodoWrite) | `todo-sync.py` | Syncs TODO state with execution tracker |
| **PostToolUse** (Write/Edit) | `folder-structure-enforcer.py` | Validates file placement matches organization rules |
| **SubagentStart** (all) | `execution-tracker.py` | Injects agent's assigned tasks + previous agent outputs |
| **SubagentStop** (pm) | `validate-pm-output.py` | Validates PM created TODO + execution-tracker.json |
| **SubagentStop** (all) | `execution-tracker.py` | Marks progress, identifies next agents, checks workflow compliance |
| **PostToolUseFailure** | `error-tracker.py` | Logs failures to `memory/reports/errors/tool-failures.jsonl` |
| **Stop** | Agent hook (haiku) | Verifies tracker/TODO consistency after every response |
| **PreCompact** | `unified-context-processor.py` | Saves context checkpoint before compression |

## Configuration

Hooks are configured in two places:
- `settings.json` — for direct project use (hardcoded paths)
- `hooks/hooks.json` — for plugin distribution (`${CLAUDE_PLUGIN_DIR}` paths)

## Three-Layer Workflow Enforcement

1. **Real-time** (SubagentStop): Developer paired with tester? Documenter in plan? /verify assigned?
2. **Per-response** (Stop hook): Haiku agent checks tracker consistency after every Main Claude response
3. **Periodic** (/heartbeat cron): Catches stale phases, missed testing, unaddressed failures

## Troubleshooting

If hooks fail silently, check permissions:
```bash
python3 .claude/scripts/hooks-permission.py
```

All hooks fail gracefully — they never block Claude Code operations.
