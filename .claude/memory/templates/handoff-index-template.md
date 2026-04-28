# Handoff Index - PLAN-{YYYYMMDD}-{CATEGORY}-{SEQ}

```yaml
plan_title: {Plan title}
started: {timestamp}
status: {in_progress/complete}
current_phase: {N}/{total}
```

---

## Chain Status

| Phase | Agent | Status | File | Summary | Time |
|-------|-------|--------|------|---------|------|
| P1 | {agent} | {☐/⚙️/✅} | P1-{agent}.md | {1-sentence summary} | {timestamp} |
| P2 | {agent} | {☐/⚙️/✅} | P2-{agent}.md | {1-sentence summary} | {timestamp} |
| P3 | {agent} | {☐/⚙️/✅} | P3-{agent}.md | {1-sentence summary} | {timestamp} |

**Legend**: ☐ Pending | ⚙️ In Progress | ✅ Complete

---

## Quick Context

```yaml
key_decisions:
  - from: P{N}-{agent}
    decision: {what was decided}
    why: {brief reason}

current_artifacts:
  - {artifact-1} → {path}
  - {artifact-2} → {path}

active_phase:
  agent: {current-agent}
  focus: {what they're working on}
  needs: {what they need from previous work}
```

---

## Next Agent

**For @{next-agent} (Phase {N+1}):**
```yaml
read_first:
  - P{N}-{previous-agent}.md

focus_on:
  - {task-1}
  - {task-2}

watch_for:
  - {concern-1}
  - {concern-2}
```
