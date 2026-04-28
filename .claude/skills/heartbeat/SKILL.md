---
name: heartbeat
description: System health check and maintenance pulse. Runs periodic checks on architecture integrity, skill quality, agent memory, error patterns, and pending work. Can be scheduled via cron or invoked manually.
argument-hint: ["full" | "quick" | "schedule"]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
disable-model-invocation: true
---
# /heartbeat — System Health & Maintenance

Periodic health check across the entire orchestration system.

## Modes

### `/heartbeat quick` (default)
Fast check — 30 seconds. Good for cron scheduling.

1. **Execution Tracker**: Read `/.claude/memory/active/execution-tracker.json`
   - Any stale phases (in-progress for > 1 hour)?
   - Any orphaned plans?
2. **Workflow Compliance**: Check the active plan against mandatory rules
   - Every developer phase has a paired tester phase?
   - /verify skill assigned to tester tasks?
   - Documenter included as final agent?
   - If plan complete: did tester, documenter, and verify all actually run?
   - Security keywords in plan → security agent assigned?
3. **Verify Reports**: Check `/.claude/memory/reports/verify/`
   - Any recent FAIL reports not addressed?
   - Implementation done but no verify report generated?
4. **Error Patterns**: Read `/.claude/memory/reports/errors/tool-failures.jsonl`
   - Any tool failing > 5 times in last 24h?
   - Recurring patterns?
5. **Skill Drafts**: Check `/.claude/memory/active/skill-drafts/`
   - Any pending drafts waiting for installation?
6. **Agent Memory Health**: Spot-check `/.claude/agent-memory/*/MEMORY.md`
   - Are agents actually updating their memory?
   - Any memory files > 200 lines (will be truncated)?

Output: One-line status per check. Write to `/.claude/memory/reports/heartbeat/HEARTBEAT-<timestamp>.md`

### `/heartbeat full`
Comprehensive audit — 2-5 minutes.

Everything in `quick` plus:

7. **Historical Workflow Compliance**: Scan `/.claude/memory/todos/` for completed TODOs
   - For each completed plan: did it follow mandatory sequences?
   - Any completed plans where tester was skipped?
   - Any completed plans missing documenter?
   - Cross-reference with verify reports in `/.claude/memory/reports/verify/`
8. **Skill Audit**: Run the equivalent of `/skill-eval all`
   - Check all skill descriptions for trigger accuracy
   - Check all agent references are valid (not archived)
   - Check for new trigger conflicts
9. **Architecture Integrity**:
   - CLAUDE.md synced between root and .claude/?
   - settings.json valid JSON?
   - All hook scripts exist and are executable?
   - All agents referenced in CLAUDE.md have matching .md files?
10. **Memory Cleanup**:
   - Archive completed TODOs older than 7 days
   - Flag oversized memory files
   - Check for stale discovery/ files
11. **Pattern Detection**:
   - Scan recent git log for repetitive commit patterns
   - Flag potential skill creation opportunities (→ suggest `/create-skill discover`)
   - Check if error patterns suggest a missing skill or rule

Output: Full report to `/.claude/memory/reports/heartbeat/HEARTBEAT-FULL-<timestamp>.md`

### `/heartbeat schedule`
Set up recurring cron jobs for automated health monitoring.

Suggest and create these cron schedules:
```
Workflow compliance every 15 min: CronCreate("*/15 * * * *", "/heartbeat quick")
Full audit every 4 hours:         CronCreate("47 */4 * * *", "/heartbeat full")
Skill eval daily:                 CronCreate("13 10 * * *", "/skill-eval all")
Pattern discovery weekly:         CronCreate("43 10 * * 5", "/create-skill discover")
```

**Why these intervals:**
- **15 min quick**: Catches stale phases, skipped testing, missing verify reports before they compound
- **4 hour full**: Deep compliance check including historical TODO analysis and architecture integrity
- **Daily skill-eval**: Ensures skill descriptions stay accurate as project evolves
- **Weekly discover**: Identifies repetitive patterns for potential new skills

Note: Cron jobs are session-only (lost on exit) and auto-expire after 3 days.
Present the schedule to the user for approval before creating.

## Report Format

```markdown
# Heartbeat Report
**Date**: [timestamp]
**Mode**: quick / full
**Duration**: [seconds]

## Status: HEALTHY / ATTENTION NEEDED / CRITICAL

| Check | Status | Details |
|-------|--------|---------|
| Execution Tracker | OK/WARN/FAIL | [stale phases, orphaned plans] |
| Workflow Compliance | OK/WARN/FAIL | [missing tester, verify, documenter] |
| Verify Reports | OK/WARN/FAIL | [unaddressed failures, missing reports] |
| Error Patterns | OK/WARN/FAIL | [recurring tool failures] |
| Skill Drafts | OK/INFO | [count pending installation] |
| Agent Memory | OK/WARN | [stale, oversized, empty] |

## Workflow Violations (if any)
| Rule | Status | Details |
|------|--------|---------|
| Developer paired with tester | PASS/FAIL | [which phases missing tester] |
| /verify on tester tasks | PASS/FAIL | [which tasks missing verify] |
| Documenter in plan | PASS/FAIL | [present/absent] |
| Security agent on sensitive work | PASS/SKIP | [keywords detected, agent assigned?] |

## Actions Needed
[Prioritized list — workflow violations first, then health issues]
```

## Task
$ARGUMENTS
