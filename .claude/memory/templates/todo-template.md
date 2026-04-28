# TODO Tracker - [Project Title]

**TodoID**: TODO-YYYYMMDD-[A-Z][0-9]+-\d{3}
**PlanID**: PLAN-YYYYMMDD-[A-Z][0-9]+-\d{3}
**AnalysisID**: ANALYSIS-YYYYMMDD-[A-Z][0-9]+-\d{3}
**Request**: "[Original user request]"
**Status**: pending | in_progress | completed
**Created**: YYYY-MM-DD
**Last Updated**: YYYY-MM-DD

---

## 📋 Quick Summary

**What**: [One sentence - what are we building]
**Approach**: [One sentence - how we're doing it]
**Total Phases**: [count]
**Current Phase**: Phase [N] of [total]
**Progress**: [percentage]% complete

---

## ✅ Phase Checklist

### Phase 1: [Phase Name]
- [ ] Task 1.1: [Task name] - **Agent**: [agent] - [Status]
- [ ] Task 1.2: [Task name] - **Agent**: [agent] - [Status]
**Status**: ☐ Not Started | ⏳ In Progress | ✅ Completed

### Phase 2: [Phase Name]
- [ ] Task 2.1: [Task name] - **Agent**: [agent] - [Status]
**Status**: ☐ Not Started | ⏳ In Progress | ✅ Completed

### Phase 3: [Phase Name]
- [ ] Task 3.1: [Task name] - **Agent**: [agent] - [Status]
**Status**: ☐ Not Started | ⏳ In Progress | ✅ Completed

### 🔍 CHECKPOINT 1 (After Phase 3)
- [ ] All Phase 1-3 tasks completed
- [ ] All quality gates passed
- [ ] All unit tests passing
- [ ] Checkpoint review completed
**Status**: ☐ Not Started | ⏳ In Progress | ✅ Passed

### Phase 4: [Phase Name]
- [ ] Task 4.1: [Task name] - **Agent**: [agent] - [Status]
**Status**: ☐ Not Started | ⏳ In Progress | ✅ Completed

### Phase 5: [Phase Name]
- [ ] Task 5.1: [Task name] - **Agent**: [agent] - [Status]
**Status**: ☐ Not Started | ⏳ In Progress | ✅ Completed

### Phase 6: [Phase Name]
- [ ] Task 6.1: [Task name] - **Agent**: [agent] - [Status]
**Status**: ☐ Not Started | ⏳ In Progress | ✅ Completed

### 🔍 CHECKPOINT 2 (After Phase 6)
- [ ] All Phase 4-6 tasks completed
- [ ] All quality gates passed
- [ ] Checkpoint review completed
**Status**: ☐ Not Started | ⏳ In Progress | ✅ Passed

[Continue for remaining phases...]

---

## 📊 Progress Summary

```yaml
overall_status:
  phases_completed: [count] / [total]
  tasks_completed: [count] / [total]
  progress_percentage: [percentage]%

phase_status:
  completed: [list of phase numbers]
  in_progress: [phase number]
  pending: [list of phase numbers]

watchdog_status:
  enabled: true | false
  risk_level: "low" | "medium" | "high"
  checkpoint_interval: [count] phases
  next_checkpoint: "After Phase [N]"

  findings_summary:
    l1_continuous: [count] findings
    l2_phase: [count] findings
    critical: [count]
    high: [count]

checkpoints:
  checkpoint_1: ☐ Pending | ⏳ In Progress | ✅ Passed
  checkpoint_2: ☐ Pending | ⏳ In Progress | ✅ Passed

quality_gates:
  passed: [count] / [total]
  failed: [count]

unit_tests:
  status: ✅ All Passing | ⚠️ Some Failing | ❌ Failing
  coverage: [percentage]%
```

---

## ⏱️ Timeline

**Started**: YYYY-MM-DD HH:MM
**Estimated Completion**: YYYY-MM-DD HH:MM
**Actual Completion**: YYYY-MM-DD HH:MM (when done)

**Time Spent**: [X hours Y minutes AI time]
**Estimated Remaining**: [X hours Y minutes AI time]

---

## 🚨 Issues & Blockers

### Active Issues
```yaml
issue_1:
  description: "[Issue description]"
  severity: [low | medium | high]
  phase: "Phase [N]"
  owner: [agent]
  status: ☐ Open | ⏳ In Progress | ✅ Resolved
```

### Resolved Issues
```yaml
issue_1:
  description: "[Issue description]"
  resolution: "[How it was resolved]"
  resolved_by: [agent]
  resolved_date: YYYY-MM-DD
```

---

## 📎 Related Artifacts

- **Full Plan**: `/.claude/memory/plans/PLAN-[ID].md`
- **Analysis**: `/.claude/memory/reports/ANALYSIS-[ID].md`
- **Handoffs**: `/.claude/memory/handoffs/HANDOFF-[PlanID]-P[N]-to-P[N+1].md`
- **Checkpoints**: `/.claude/memory/checkpoints/CHECKPOINT-[PlanID]-C[N].md`

---

## 📝 Quick Notes

- [Note 1 - important decision or context]
- [Note 2 - important decision or context]

---

**This is a simplified tracker. See PLAN-[ID].md for complete details including deliverables, dependencies, knowledge requirements, and handoffs.**
