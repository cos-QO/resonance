# Watchdog Quality Check Report - Checkpoint [N]

**WatchdogID**: WATCHDOG-{PlanID}-C{N}
**PlanID**: PLAN-YYYYMMDD-[A-Z][0-9]+-\d{3}
**Checkpoint**: C{N}
**Phases Validated**: Phase [N-2], Phase [N-1], Phase [N]
**Timestamp**: YYYY-MM-DDTHH:MM:SSZ
**Duration**: [X minutes]
**Status**: in_progress | completed

---

## 🎯 Watchdog Mission

**Validate**: Phases [N-2, N-1, N] compliance with plan
**Parallel**: Yes (execution continued with Phase [N+1])
**Report To**: PM at plan completion

---

## ✅ VALIDATION CHECKLIST

### 1. Plan Compliance Check

```yaml
plan_file: "/.claude/memory/plans/PLAN-{ID}.md"
phases_validated: [N-2, N-1, N]

compliance_status: ✅ PASS | ⚠️ ISSUES | ❌ FAIL

checks:
  all_planned_tasks_completed:
    status: ✅ | ⚠️ | ❌
    expected_tasks: [count]
    completed_tasks: [count]
    missing_tasks: [list if any]

  correct_agents_executed:
    status: ✅ | ⚠️ | ❌
    deviations: [list if any]

  deliverables_match_plan:
    status: ✅ | ⚠️ | ❌
    planned_deliverables: [count]
    delivered: [count]
    missing: [list if any]

  unplanned_work:
    detected: true | false
    items: [list if any]
```

**Summary**: [Brief summary of compliance]

---

### 2. Documentation Files Check

```yaml
documentation_status: ✅ PASS | ⚠️ ISSUES | ❌ FAIL

handoff_files:
  expected:
    - "HANDOFF-{PlanID}-P[N-2]-to-P[N-1].md"
    - "HANDOFF-{PlanID}-P[N-1]-to-P[N].md"
  found: [count]/[total]
  missing: [list if any]
  status: ✅ | ⚠️ | ❌

todo_file:
  path: "/.claude/memory/todos/TODO-{ID}.md"
  exists: true | false
  last_updated: "YYYY-MM-DD HH:MM:SS"
  status: ✅ | ⚠️ | ❌

handoff_completeness:
  required_sections: [artifacts, context, notes]
  files_checked: [count]
  complete_files: [count]
  incomplete_files: [list if any]
  status: ✅ | ⚠️ | ❌
```

**Summary**: [Brief summary of documentation status]

---

### 3. Tracking Files Check

```yaml
tracking_status: ✅ PASS | ⚠️ | ❌ FAIL

todo_checklist:
  path: "/.claude/memory/todos/TODO-{ID}.md"
  phases_checked: [count]
  phases_marked_complete: [count]
  status: ✅ | ⚠️ | ❌

progress_percentage:
  calculated: "[percentage]%"
  matches_actual: true | false
  status: ✅ | ⚠️ | ❌

phase_statuses:
  phase_N-2:
    expected: "✅ Completed"
    actual: "[status]"
    correct: true | false

  phase_N-1:
    expected: "✅ Completed"
    actual: "[status]"
    correct: true | false

  phase_N:
    expected: "✅ Completed"
    actual: "[status]"
    correct: true | false

issues_blockers_documented:
  issues_found: [count]
  documented: true | false
  status: ✅ | ⚠️ | ❌
```

**Summary**: [Brief summary of tracking status]

---

### 4. Quality Gates Check

```yaml
quality_gates_status: ✅ PASS | ⚠️ ISSUES | ❌ FAIL

plan_quality_gates:
  total_defined: [count]
  per_phase: [count per phase]

handoff_quality_gates:
  phase_N-2:
    total_gates: [count]
    passed: [count]
    failed: [count]
    status: ✅ | ⚠️ | ❌

  phase_N-1:
    total_gates: [count]
    passed: [count]
    failed: [count]
    status: ✅ | ⚠️ | ❌

  phase_N:
    total_gates: [count]
    passed: [count]
    failed: [count]
    status: ✅ | ⚠️ | ❌

critical_gates_failed:
  - "[Gate name if any]"

overall_pass_rate: "[percentage]%"
```

**Summary**: [Brief summary of quality gates]

---

### 5. Unit Tests Check (via Tester Agent)

```yaml
unit_tests_status: ✅ PASS | ⚠️ ISSUES | ❌ FAIL

tester_invocation:
  agent: "tester"
  task: "Soft check phases [N-2, N-1, N]"
  duration: "[X minutes]"
  completed: true | false

test_results:
  implementation_tasks_checked: [count]
  unit_tests_found:
    phase_N-2: true | false
    phase_N-1: true | false
    phase_N: true | false

  test_execution:
    total_tests: [count]
    passing: [count]
    failing: [count]
    pass_rate: "[percentage]%"

  coverage:
    measured: true | false
    percentage: "[percentage]%"
    meets_target: true | false  # ≥80%

  critical_failures:
    found: true | false
    list: [test names if any]

tester_report_location: "/.claude/memory/[tester-report-path]"
```

**Summary**: [Brief summary from tester]

---

## 📊 OVERALL ASSESSMENT

### Health Score
```yaml
overall_health: ✅ HEALTHY | ⚠️ CONCERNS | ❌ CRITICAL

health_breakdown:
  plan_compliance: ✅ | ⚠️ | ❌
  documentation: ✅ | ⚠️ | ❌
  tracking: ✅ | ⚠️ | ❌
  quality_gates: ✅ | ⚠️ | ❌
  unit_tests: ✅ | ⚠️ | ❌

score: "[X]/5 passing"
```

### Blocking Issues
```yaml
blocking_issues_found: true | false

issues:
  - issue: "[Description]"
    severity: HIGH | MEDIUM | LOW
    phase: "Phase [N]"
    impact: "[Impact description]"
    status: OPEN | IN_PROGRESS | RESOLVED
```

### Recommendations
```yaml
immediate_actions:
  - "[Action 1]"
  - "[Action 2]"

for_next_phases:
  - "[Recommendation 1]"
  - "[Recommendation 2]"

lessons_learned:
  - "[Lesson 1]"
  - "[Lesson 2]"
```

---

## 🔍 DETAILED FINDINGS

### Phase [N-2] Analysis
```yaml
phase_name: "[Phase Name]"
agent: [agent]
status: ✅ Completed | ⚠️ Issues | ❌ Failed

strengths:
  - "[Strength 1]"
  - "[Strength 2]"

issues:
  - "[Issue 1]"
  - "[Issue 2]"

quality_score: "[X]/10"
```

### Phase [N-1] Analysis
```yaml
phase_name: "[Phase Name]"
agent: [agent]
status: ✅ Completed | ⚠️ Issues | ❌ Failed

strengths:
  - "[Strength 1]"
  - "[Strength 2]"

issues:
  - "[Issue 1]"
  - "[Issue 2]"

quality_score: "[X]/10"
```

### Phase [N] Analysis
```yaml
phase_name: "[Phase Name]"
agent: [agent]
status: ✅ Completed | ⚠️ Issues | ❌ Failed

strengths:
  - "[Strength 1]"
  - "[Strength 2]"

issues:
  - "[Issue 1]"
  - "[Issue 2]"

quality_score: "[X]/10"
```

---

## 📈 METRICS

### Execution Metrics
```yaml
planned_vs_actual:
  planned_duration: "[X hours]"
  actual_duration: "[Y hours]"
  variance: "+/- [Z]%"

task_completion:
  total_tasks: [count]
  completed: [count]
  completion_rate: "[percentage]%"

deliverable_completion:
  total_deliverables: [count]
  delivered: [count]
  completion_rate: "[percentage]%"
```

### Quality Metrics
```yaml
quality_gates:
  total: [count]
  passed: [count]
  pass_rate: "[percentage]%"

unit_tests:
  total: [count]
  passing: [count]
  pass_rate: "[percentage]%"
  coverage: "[percentage]%"

code_quality:
  linting_passed: true | false
  standards_followed: true | false
```

---

## 🎯 WATCHDOG CONCLUSION

**Overall Verdict**: ✅ HEALTHY | ⚠️ CONCERNS | ❌ CRITICAL

**Key Points**:
1. [Key finding 1]
2. [Key finding 2]
3. [Key finding 3]

**Execution Continuing**: Phase [N+1] started immediately (parallel execution)

**Next Watchdog**: Checkpoint C{N+1} (After Phase [N+3])

---

## 📎 RELATED ARTIFACTS

- **Plan**: `/.claude/memory/plans/PLAN-{ID}.md`
- **TODO**: `/.claude/memory/todos/TODO-{ID}.md`
- **Handoffs**:
  - `/.claude/memory/handoffs/HANDOFF-{PlanID}-P[N-2]-to-P[N-1].md`
  - `/.claude/memory/handoffs/HANDOFF-{PlanID}-P[N-1]-to-P[N].md`
- **Tester Report**: `/.claude/memory/[tester-report-path]`

---

## 📝 WATCHDOG METADATA

**Watchdog Agent**: watchdog
**Invoked By**: Main Claude (automatically after Phase [N])
**Parallel Execution**: Yes (Phase [N+1] started concurrently)
**Report Created**: YYYY-MM-DD HH:MM:SS
**Duration**: [X] minutes
**Status**: ✅ Completed

**Report For**: PM (will read at plan completion - Phase 5)

---

**Note**: This is an automated quality check. Execution continued without pause. Findings shared with PM at plan end.
