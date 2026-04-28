---
handoff_id: P{N}-{agent}
plan_id: PLAN-{YYYYMMDD}-{CATEGORY}-{SEQ}
from_agent: {agent-name}
to_agent: {next-agent-name}
phase: {N}
status: complete
created: {timestamp}
---

# P{N}: {Agent} → {Next Agent}

## Summary
{1-2 sentences: what accomplished + what next agent does}

---

## Completed

```yaml
deliverables:
  - name: {deliverable-1}
    path: {file-path}
    status: complete
  - name: {deliverable-2}
    path: {file-path}
    status: complete

quality_gates:
  - {gate-1}: {result}
  - {gate-2}: {result}
```

---

## Key Decisions

```yaml
decision_1:
  what: {decision made}
  why: {rationale}
  impact: {how affects next agent}

decision_2:
  what: {decision made}
  why: {rationale}
  impact: {how affects next agent}
```

---

## Artifacts

```yaml
code:
  - path: {file-path}
    purpose: {what it does}

tests:
  - path: {file-path}
    coverage: {X%}
    status: {passing/failing}

docs:
  - path: {file-path}
    purpose: {what documents}
```

---

## For Next Agent

```yaml
start_here:
  - {first thing to review}
  - {key files to understand}

must_know:
  - {critical context 1}
  - {critical context 2}

recommendations:
  - {approach suggestion 1}
  - {consistency tip 2}
```

---

## Issues & Fixes

```yaml
issue_1:
  problem: {what went wrong}
  fixed: {yes/no}
  how: {solution if fixed, reason if not}
  impact: {what this means for next agent}

issue_2:
  problem: {critical discovery}
  fixed: {yes/no}
  how: {solution if fixed, reason if not}
  impact: {what this means for next agent}
```

---

## Health Status

```yaml
watchdog_validation:
    level_1_findings: {count} # Continuous monitoring
    level_2_findings: {count} # Phase validation
    status: ✅ PASS | ⚠️ WARNINGS | ❌ ISSUES

quality_metrics:
    unit_tests: "{X}% passing ({Y}/{Z} tests)"
    coverage: "{X}%"
    critical_issues: {count}
```

---

## Links

- **Plan**: `/.claude/memory/plans/PLAN-{ID}.md`
- **Previous**: `/.claude/memory/handoffs/PLAN-{ID}/P{N-1}-{agent}.md`
- **Index**: `/.claude/memory/handoffs/PLAN-{ID}/handoff-index.md`
- **Watchdog Findings**: `/.claude/memory/watchdog/findings/phase-{N}.json`
