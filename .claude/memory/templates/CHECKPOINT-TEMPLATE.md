# Checkpoint Report - Checkpoint [N]

**CheckpointID**: CHECKPOINT-[PlanID]-C[N]
**PlanID**: PLAN-YYYYMMDD-[A-Z][0-9]+-\d{3}
**Checkpoint Number**: [N]
**Phases Covered**: Phase [N-2], Phase [N-1], Phase [N]
**Date**: YYYY-MM-DD
**Status**: in_progress | completed | go | no-go

---

## 🎯 Checkpoint Goal

**Purpose**: Validate progress after completing [N] phases, ensure alignment with plan, address issues before continuing

**Phases Under Review**: Phase [N-2], Phase [N-1], Phase [N]

---

## 🐕 Watchdog Validation Results

### Progressive Validation Summary

```yaml
level_1_continuous:
  total_findings: [count]
  findings_by_severity:
    critical: [count]
    high: [count]
    medium: [count]
    low: [count]
  source: "/.claude/memory/watchdog/findings/findings-buffer.json"

level_2_phase:
  phases_validated: [list]
  total_findings: [count]
  findings_by_severity:
    critical: [count]
    high: [count]
    medium: [count]
    low: [count]
  source: "/.claude/memory/watchdog/findings/phase-*.json"

level_3_checkpoint:
  unique_findings: [count]  # After deduplication
  escalations: [count]
  critical_issues: [count]
```

**Watchdog Overall Status**: ✅ HEALTHY | ⚠️ CONCERNS | ❌ CRITICAL

---

## ✅ Validation Checklist

### 1. Scope Validation
- [ ] **Original requirements still aligned**: Are we building what was requested?
- [ ] **No scope creep**: Have we stayed within defined scope?
- [ ] **Out-of-scope items identified**: Any new requirements discovered?
- [ ] **Assumptions still valid**: Are original assumptions still true?

**Status**: ✅ Aligned | ⚠️ Minor deviations | ❌ Major deviations
**Notes**: [Any scope issues or changes]

---

### 2. Quality Validation
- [ ] **All quality gates passed**: Every phase's quality gates met?
- [ ] **Code standards followed**: Linting, formatting, conventions?
- [ ] **Documentation up to date**: All artifacts documented?
- [ ] **No critical issues**: Any blocking issues exist?

**Status**: ✅ All passed | ⚠️ Some issues | ❌ Critical issues
**Notes**: [Quality issues if any]

---

### 3. Progress Validation
- [ ] **Timeline on track**: Are we within estimated time?
- [ ] **All tasks completed**: Every task in phases done?
- [ ] **No blockers**: Anything preventing next phases?
- [ ] **Resource availability**: Resources available for next phases?

**Status**: ✅ On track | ⚠️ Minor delays | ❌ Significant delays
**Notes**: [Timeline issues if any]

---

### 4. Deliverables Validation
- [ ] **All deliverables complete**: Every expected deliverable exists?
- [ ] **Deliverables meet requirements**: Quality acceptable?
- [ ] **Handoffs successful**: Artifacts passed between agents?
- [ ] **Dependencies resolved**: All dependencies met?

**Status**: ✅ Complete | ⚠️ Partially complete | ❌ Incomplete
**Notes**: [Deliverable issues if any]

---

### 5. Unit Tests Validation
- [ ] **All unit tests passing**: 100% pass rate?
- [ ] **Coverage adequate**: Meeting coverage targets (≥80%)?
- [ ] **Test quality**: Tests are meaningful, not superficial?
- [ ] **Integration tests**: Working across components?

**Status**: ✅ All passing | ⚠️ Some failing | ❌ Critical failures
**Test Coverage**: [percentage]%
**Notes**: [Testing issues if any]

---

## 📊 Phase Recap (Phases [N-2] to [N])

### Phase [N-2]: [Phase Name]

```yaml
status: ✅ Completed | ⚠️ Issues | ❌ Failed
completion_date: YYYY-MM-DD
agents_involved: [list]

tasks:
  total: [count]
  completed: [count]
  completion_rate: [percentage]%

deliverables:
  expected: [count]
  delivered: [count]
  status: ✅ | ⚠️ | ❌

quality_gates:
  total: [count]
  passed: [count]
  status: ✅ | ⚠️ | ❌

unit_tests:
  total: [count]
  passing: [count]
  failing: [count]
  coverage: [percentage]%
  status: ✅ | ⚠️ | ❌

issues:
  - issue: "[Issue description]"
    severity: [low | medium | high]
    status: ✅ Resolved | ⏳ In Progress | ☐ Open
```

**Key Achievements**:
- [Achievement 1]
- [Achievement 2]

**Lessons Learned**:
- [Lesson 1]
- [Lesson 2]

---

### Phase [N-1]: [Phase Name]

```yaml
status: ✅ Completed | ⚠️ Issues | ❌ Failed
completion_date: YYYY-MM-DD
agents_involved: [list]

tasks:
  total: [count]
  completed: [count]
  completion_rate: [percentage]%

deliverables:
  expected: [count]
  delivered: [count]
  status: ✅ | ⚠️ | ❌

quality_gates:
  total: [count]
  passed: [count]
  status: ✅ | ⚠️ | ❌

unit_tests:
  total: [count]
  passing: [count]
  failing: [count]
  coverage: [percentage]%
  status: ✅ | ⚠️ | ❌

issues:
  - issue: "[Issue description]"
    severity: [low | medium | high]
    status: ✅ Resolved | ⏳ In Progress | ☐ Open
```

**Key Achievements**:
- [Achievement 1]
- [Achievement 2]

**Lessons Learned**:
- [Lesson 1]
- [Lesson 2]

---

### Phase [N]: [Phase Name]

```yaml
status: ✅ Completed | ⚠️ Issues | ❌ Failed
completion_date: YYYY-MM-DD
agents_involved: [list]

tasks:
  total: [count]
  completed: [count]
  completion_rate: [percentage]%

deliverables:
  expected: [count]
  delivered: [count]
  status: ✅ | ⚠️ | ❌

quality_gates:
  total: [count]
  passed: [count]
  status: ✅ | ⚠️ | ❌

unit_tests:
  total: [count]
  passing: [count]
  failing: [count]
  coverage: [percentage]%
  status: ✅ | ⚠️ | ❌

issues:
  - issue: "[Issue description]"
    severity: [low | medium | high]
    status: ✅ Resolved | ⏳ In Progress | ☐ Open
```

**Key Achievements**:
- [Achievement 1]
- [Achievement 2]

**Lessons Learned**:
- [Lesson 1]
- [Lesson 2]

---

## 📈 Overall Progress Summary

```yaml
phases_completed: [N] / [total]
progress_percentage: [percentage]%

cumulative_stats:
  total_tasks: [count]
  completed_tasks: [count]
  task_completion_rate: [percentage]%
  
  total_quality_gates: [count]
  passed_quality_gates: [count]
  quality_gate_pass_rate: [percentage]%
  
  total_unit_tests: [count]
  passing_unit_tests: [count]
  test_pass_rate: [percentage]%
  test_coverage: [percentage]%

timeline:
  planned_duration: "[X hours]"
  actual_duration: "[Y hours]"
  variance: "+/- [Z hours]"
  on_track: true | false
```

---

## 🚨 Issues Identified

### Critical Issues
```yaml
critical_issue_1:
  description: "[Issue description]"
  phase: "Phase [N]"
  impact: "[How this affects project]"
  resolution_required: "[What must be done]"
  owner: [agent]
  deadline: YYYY-MM-DD
  status: ☐ Open | ⏳ In Progress | ✅ Resolved
```

### Medium Issues
```yaml
medium_issue_1:
  description: "[Issue description]"
  phase: "Phase [N]"
  impact: "[How this affects project]"
  resolution: "[Proposed solution]"
  owner: [agent]
  status: ☐ Open | ⏳ In Progress | ✅ Resolved
```

### Low Issues / Observations
- [Observation 1]
- [Observation 2]

---

## 💡 Decisions Made at Checkpoint

### Decision 1: [Decision Title]
```yaml
description: "[What was decided]"
reasoning: "[Why we made this decision]"
alternatives_considered: "[Other options we considered]"
impact: "[How this affects next phases]"
approved_by: [PM | User | Team]
date: YYYY-MM-DD
```

### Decision 2: [Decision Title]
```yaml
description: "[What was decided]"
reasoning: "[Why we made this decision]"
alternatives_considered: "[Other options we considered]"
impact: "[How this affects next phases]"
approved_by: [PM | User | Team]
date: YYYY-MM-DD
```

---

## 🔄 Plan Adjustments

### Adjustments Required
- [ ] **Scope adjustment**: [Description if needed]
- [ ] **Timeline adjustment**: [Description if needed]
- [ ] **Resource adjustment**: [Description if needed]
- [ ] **Quality gate adjustment**: [Description if needed]

### Changes to Plan
```yaml
change_1:
  type: [scope | timeline | resource | quality]
  description: "[What is changing]"
  reasoning: "[Why we need this change]"
  impact: "[How this affects project]"
  approved: true | false
```

### Updated Timeline
```yaml
original_completion: "YYYY-MM-DD"
revised_completion: "YYYY-MM-DD"
variance: "+/- [X] hours"
reasoning: "[Why timeline changed]"
```

---

## 🎯 Readiness for Next Phases

### Prerequisites for Phase [N+1]
- [x] Phase [N] completed
- [x] All deliverables from Phase [N] available
- [x] Quality gates passed
- [x] Unit tests passing
- [ ] **Additional requirement**: [If any]

**Status**: ✅ Ready | ⚠️ Ready with conditions | ❌ Not ready

### Conditions for Proceeding (if any)
- **Condition 1**: [What must be addressed before Phase [N+1]]
- **Condition 2**: [What must be addressed before Phase [N+1]]

---

## 📤 Handoff to Next Phases

### Artifacts Ready for Phase [N+1]
- **Artifact 1**: [Name] - Location: [path]
- **Artifact 2**: [Name] - Location: [path]
- **Artifact 3**: [Name] - Location: [path]

### Context for Phase [N+1] to [N+3]
```yaml
context_summary: "[What next phases need to know]"

key_decisions: 
  - "[Decision 1 that affects next phases]"
  - "[Decision 2 that affects next phases]"

constraints_for_next_phases:
  - "[Constraint 1]"
  - "[Constraint 2]"

recommendations:
  - "[Recommendation 1 for next agents]"
  - "[Recommendation 2 for next agents]"
```

---

## ✅ Go/No-Go Decision

### Checkpoint Assessment

**Overall Status**: ✅ GO | ⚠️ GO WITH CONDITIONS | ❌ NO-GO

### GO Criteria
- [x] All phases completed (Phase [N-2], [N-1], [N])
- [x] Quality gates: [percentage]% passed (threshold: ≥90%)
- [x] Unit tests: [percentage]% passing (threshold: ≥95%)
- [x] Test coverage: [percentage]% (threshold: ≥80%)
- [x] No critical blockers
- [x] Timeline variance acceptable (+/- 20%)

### Decision
**Status**: ☑️ GO - Proceed to Phase [N+1]

**Reasoning**: [Why we're proceeding or why we're pausing]

**Conditions** (if GO WITH CONDITIONS):
- [Condition 1 that must be met]
- [Condition 2 that must be met]

**Actions Required** (if NO-GO):
- [Action 1 before proceeding]
- [Action 2 before proceeding]

---

## 📋 Action Items for Next Phases

### Immediate Actions
- [ ] **Action 1**: [What needs to be done] - Owner: [agent] - Due: YYYY-MM-DD
- [ ] **Action 2**: [What needs to be done] - Owner: [agent] - Due: YYYY-MM-DD

### Phase [N+1] Preparation
- [ ] **Prep 1**: [Preparation needed] - Owner: [agent]
- [ ] **Prep 2**: [Preparation needed] - Owner: [agent]

---

## 📎 Related Documents

- **Full Plan**: `/.claude/memory/plans/PLAN-[ID].md`
- **Analysis**: `/.claude/memory/reports/ANALYSIS-[ID].md`
- **TODO Tracker**: `/.claude/memory/todos/TODO-[ID].md`
- **Handoffs**: 
  - Phase [N-2] → [N-1]: `/.claude/memory/handoffs/HANDOFF-[PlanID]-P[N-2]-to-P[N-1].md`
  - Phase [N-1] → [N]: `/.claude/memory/handoffs/HANDOFF-[PlanID]-P[N-1]-to-P[N].md`
  - Phase [N] → [N+1]: `/.claude/memory/handoffs/HANDOFF-[PlanID]-P[N]-to-P[N+1].md`

---

## 📝 Checkpoint Sign-off

**Checkpoint Completed**: ✅
**Reviewed By**: [PM | Team | User]
**Date**: YYYY-MM-DD
**Decision**: ☑️ GO | ☐ GO WITH CONDITIONS | ☐ NO-GO

**Next Checkpoint**: Checkpoint [N+1] (After Phase [N+3])
**Next Checkpoint Date**: YYYY-MM-DD (estimated)

---

**IMPORTANT**:
- 📊 **Update TODO tracker** with checkpoint status
- 📋 **Update plan** with any adjustments made
- 📤 **Create handoff** for Phase [N+1] if GO decision
- 🔄 **Communicate decision** to all relevant agents
- 📅 **Schedule next checkpoint** (after Phase [N+3])
