# Execution Plan - [Project Title]

**PlanID**: PLAN-YYYYMMDD-[A-Z][0-9]+-\d{3}
**AnalysisID**: ANALYSIS-YYYYMMDD-[A-Z][0-9]+-\d{3}
**Request**: "[Original user request]"
**Date**: YYYY-MM-DD
**Status**: draft | approved | in_progress | completed
**Total Phases**: [count]
**Checkpoint Frequency**: Every 3 phases

---

## 📋 Plan Overview

**Summary**: [One-paragraph description of what this plan achieves]

**Approach**: [Brief description of the chosen approach from analysis]

**Total Estimated Time**: [X-Y hours AI time]

---

## 🎯 Success Criteria

- [ ] "[Success criterion 1]"
- [ ] "[Success criterion 2]"
- [ ] "[Success criterion 3]"

---

## 📊 Phase Structure

```
Phase 1 → Phase 2 → Phase 3 → [🐕 WATCHDOG C1 PARALLEL] → Phase 4 → Phase 5 → Phase 6 → [🐕 WATCHDOG C2 PARALLEL] → ...
                                        ↓ (non-blocking)                                           ↓ (non-blocking)
                                   Validates P1-3                                            Validates P4-6
```

**Total Phases**: [count]
**Watchdog Invocations**: Every 3 phases (parallel, non-blocking)
**Key**: Watchdog runs in parallel - execution continues without pause

---

## 🔄 Phase 1: [Phase Name]

**Phase Goal**: [What this phase achieves]
**Status**: ☐ Not Started | ⏳ In Progress | ✅ Completed
**Estimated Time**: [X-Y minutes AI time]

### Tasks

**MANDATORY: Task N.1 is ALWAYS Phase Scoping (NO EXCEPTIONS)**

#### Task 1.1: Scope Phase 1 (MANDATORY FIRST TASK)
```yaml
agent: [phase_primary_agent]
description: "Understand Phase 1 requirements, context, constraints, and success criteria"
mandatory: true  # ALWAYS include as Task N.1 in EVERY phase
why_mandatory: "Ensures agent fully understands requirements before execution, reduces rework"

deliverables:
  - "Phase scope summary"
  - "Key constraints identified"
  - "Success criteria for this phase clarified"
  - "Dependencies from previous phase understood"

required_knowledge:
  - "Previous phase handoff (if applicable)"
  - "/.claude/memory/standards/conventions.md"
  - "/.claude/memory/plans/PLAN-[ID].md (this plan)"

dependencies:
  previous_task: null  # First task in phase
  previous_phase: "Phase [N-1] (if applicable)"
  needs_from_previous:
    - "Handoff artifacts from previous phase"
    - "Context and decisions from previous phase"

handoff_to_next:
  artifacts:
    - "Phase scope document"
  context:
    - "Understanding of phase requirements"
    - "Identified constraints and dependencies"
  notes:
    - "Clarifications needed for execution tasks"

quality_gates:
  - "Phase requirements clearly understood"
  - "Constraints and dependencies identified"
  - "Success criteria defined"

unit_tests_required: false  # Scoping task, not implementation
unit_test_scope: []

estimated_time: "2-5 minutes AI time"
```

#### Task 1.2: [Execution Task Name]
```yaml
agent: [agent_name]
description: "[What this task does - actual implementation/work]"

deliverables:
  - "[Deliverable 1]"
  - "[Deliverable 2]"
  - "[Deliverable 3]"

required_knowledge:
  - "/.claude/knowledge/[module1].md"
  - "/.claude/knowledge/[module2].md"

dependencies:
  previous_task: "Task 1.1 (Phase scoping - MANDATORY)"
  needs_from_previous:
    - "Phase scope summary"
    - "Constraints identified"

handoff_to_next:
  artifacts:
    - "[Artifact 1 to pass to next agent]"
    - "[Artifact 2 to pass to next agent]"
  context:
    - "[Context information for next agent]"
  notes:
    - "[Important note for next agent]"

quality_gates:
  - "[Quality check 1]"
  - "[Quality check 2]"

unit_tests_required: true | false  # true for implementation tasks (developer), false for others
unit_tests_mandatory: true | false  # true for developer tasks (cannot be false), false for others
unit_test_scope:
  - "[Test scope 1]"
  - "[Test scope 2]"

estimated_time: "[X-Y minutes AI time]"
```

### Phase 1 Summary
```yaml
total_tasks: [count]
agents_involved: [list]
estimated_time: "[X-Y minutes AI time]"
dependencies: [none | list]
quality_gates_total: [count]
unit_tests_required: true | false
```

---

## 🔄 Phase 2: [Phase Name]

**Phase Goal**: [What this phase achieves]
**Status**: ☐ Not Started | ⏳ In Progress | ✅ Completed
**Estimated Time**: [X-Y minutes AI time]

### Tasks

**MANDATORY: Task 2.1 is ALWAYS Phase 2 Scoping (NO EXCEPTIONS)**

#### Task 2.1: Scope Phase 2 (MANDATORY FIRST TASK)
```yaml
agent: [phase_primary_agent]
description: "Understand Phase 2 requirements, context, constraints, and success criteria"
mandatory: true  # ALWAYS include as Task N.1 in EVERY phase

deliverables:
  - "Phase scope summary"
  - "Key constraints identified"
  - "Success criteria for this phase clarified"

required_knowledge:
  - "/.claude/memory/handoffs/HANDOFF-*-P1-to-P2.md"
  - "/.claude/memory/standards/conventions.md"

dependencies:
  previous_task: null  # First task in phase
  previous_phase: "Phase 1"
  needs_from_previous:
    - "Handoff artifacts from Phase 1"
    - "Design decisions from Phase 1"
    - "Context from Phase 1"

handoff_to_next:
  artifacts:
    - "Phase 2 scope document"
  context:
    - "Understanding of implementation requirements"
  notes:
    - "Constraints for implementation"

quality_gates:
  - "Phase requirements clearly understood"
  - "Constraints identified"

unit_tests_required: false  # Scoping task
unit_test_scope: []

estimated_time: "2-5 minutes AI time"
```

#### Task 2.2: [Implementation Task Name]
```yaml
agent: [agent_name]
description: "[What implementation task does]"

deliverables:
  - "[Implementation deliverable]"
  - "Unit tests (MANDATORY if agent=developer)"

required_knowledge:
  - "/.claude/knowledge/[module].md"

dependencies:
  previous_task: "Task 2.1 (Phase 2 scoping - MANDATORY)"
  previous_phase: "Phase 1"
  needs_from_previous:
    - "Phase scope summary"
    - "Artifacts from Phase 1"

handoff_to_next:
  artifacts:
    - "[Implementation artifacts]"
  context:
    - "[Implementation context]"
  notes:
    - "[Important decisions made]"

quality_gates:
  - "[Quality check 1]"
  - "Unit tests passing (if implementation)"

unit_tests_required: true | false  # MANDATORY=true for developer, false for others
unit_tests_mandatory: true | false  # true for developer (cannot be false)
unit_test_scope:
  - "[Test scope]"

estimated_time: "[X-Y minutes]"
```

### Phase 2 Summary
```yaml
total_tasks: [count]
agents_involved: [list]
estimated_time: "[X-Y minutes AI time]"
```

---

## 🔄 Phase 3: [Phase Name]

[Same structure as Phase 1 & 2]

---

## 🐕 WATCHDOG INVOCATION C1 (After Phase 3 - Parallel)

**Watchdog Mission**: Validate Phases 1-3 while execution continues with Phase 4+

**Key**: **NO PAUSE** - Watchdog runs in parallel, Phase 4 starts immediately

### Watchdog Invocation
```yaml
invoke_watchdog:
  checkpoint: "C1"
  after_phase: 3
  validates: [Phase 1, Phase 2, Phase 3]
  parallel: true  # Non-blocking
  report: "/.claude/memory/watchdog/WATCHDOG-{PlanID}-C1.md"

  watchdog_tasks:
    1. "Verify plan compliance (phases 1-3)"
    2. "Check documentation files exist"
    3. "Verify tracking files updated"
    4. "Check quality gates from handoffs"
    5. "Invoke tester for soft unit test check"
    6. "Create watchdog report (checklist)"

  duration: "10-15 minutes"
  blocking: false

concurrent_execution:
  - "Phase 4 starts immediately"
  - "Watchdog C1 validates P1-3 in parallel"
  - "Both run at same time"
```

### Watchdog Checklist (Auto-validated by Watchdog Agent)
```yaml
plan_compliance:
  - [ ] All planned tasks completed (P1-3)?
  - [ ] Correct agents executed?
  - [ ] Deliverables match plan?

documentation:
  - [ ] Handoff files exist for P1-3?
  - [ ] TODO file updated?

tracking:
  - [ ] TODO checklist updated?
  - [ ] Phase statuses correct?

quality_gates:
  - [ ] Quality gates passed?
  - [ ] No critical failures?

unit_tests:
  - [ ] Tests exist for implementation?
  - [ ] Tests passing?
  - [ ] Coverage ≥80%?
```

### Watchdog Report Location
```bash
# Watchdog creates report at:
/.claude/memory/watchdog/WATCHDOG-{PlanID}-C1.md

# PM reads at plan completion (Phase 5)
```

### Execution Flow
```
Phase 3 Completes →
  ├─ Phase 4 Starts (IMMEDIATE)
  └─ Watchdog C1 Invoked (PARALLEL)
       ↓ (10-15 min)
       Report: WATCHDOG-{PlanID}-C1.md
```

**Note**: No GO/NO-GO decision. Execution continues. Watchdog reports findings to PM at end.

---

## 🔄 Phase 4: [Phase Name]

[Continue with same structure]

---

## 🔄 Phase 5: [Phase Name]

---

## 🔄 Phase 6: [Phase Name]

---

## 🔍 CHECKPOINT 2 (After Phase 6)

[Same structure as Checkpoint 1]

---

## 📊 Agent Knowledge Requirements

### Architect
**Knowledge Modules to Load**:
- `/.claude/knowledge/workflows/specialized/architect/[module].md`
- `/.claude/knowledge/architecture/[pattern].md`

**When to Load**: Before Phase 1, Task 1.1
**Why Needed**: [Reasoning]

---

### Developer
**Knowledge Modules to Load**:
- `/.claude/knowledge/workflows/specialized/developer/[module].md`
- `/.claude/knowledge/languages/[language]/[module].md`

**When to Load**: Before Phase 2, Task 2.1
**Why Needed**: [Reasoning]

---

### Tester
**Knowledge Modules to Load**:
- `/.claude/knowledge/workflows/specialized/tester/[module].md`
- `/.claude/knowledge/testing/[framework].md`

**When to Load**: Before Phase 3, Task 3.1
**Why Needed**: [Reasoning]

---

### [Other Agents...]

---

## 🔄 Handoff Chain

```
Phase 1: Architect (Task 1.1)
   ↓ [Design artifacts, architecture decisions]
Phase 2: Developer (Task 2.1)
   ↓ [Implementation artifacts, code]
Phase 3: Tester (Task 3.1)
   ↓ [Test results, verified implementation]
Phase 4: Security (Task 4.1)
   ↓ [Security audit report, approved implementation]
Phase 5: Documenter (Task 5.1)
   ↓ [Documentation, user guides]
```

### Handoff Details

**Phase 1 → Phase 2**:
- Artifacts: [list]
- Context: [list]
- Notes: [list]

**Phase 2 → Phase 3**:
- Artifacts: [list]
- Context: [list]
- Notes: [list]

[Continue for all phase transitions]

---

## ✅ Quality Gates Summary

### Overall Quality Gates
- [ ] **Architecture**: Design approved, patterns validated
- [ ] **Implementation**: Code follows standards, linting passes
- [ ] **Testing**: All tests passing, coverage ≥ 80%
- [ ] **Security**: Security checklist complete, no critical issues
- [ ] **Documentation**: Docs complete, examples provided

### Per-Phase Quality Gates
**Phase 1**: [list gates]
**Phase 2**: [list gates]
**Phase 3**: [list gates]
[Continue for all phases]

---

## 🧪 Unit Testing Strategy

**MANDATORY: All Implementation Tasks MUST Include Unit Tests**

```yaml
mandatory_unit_testing_rule:
  trigger: "agent = developer (ANY implementation task)"
  requirement: "unit_tests_required MUST be true"
  exceptions: NONE

  implementation_tasks:
    unit_tests_required: true  # MANDATORY - ALWAYS true
    unit_tests_mandatory: true  # Cannot be set to false
    deliverables_must_include:
      - "Implementation code"
      - "Unit tests for implementation (MANDATORY)"
      - "Test coverage report (≥80%)"
    quality_gates_must_include:
      - "All unit tests passing (100%)"
      - "Code coverage ≥80%"

  non_implementation_tasks:
    agents: [architect, documenter, reviewer, business-analyst, researcher]
    unit_tests_required: false  # Can be false for non-code work
    unit_tests_mandatory: false
```

**Why Mandatory**:
- Ensures code quality before handoff to tester
- Catches bugs during development (not testing phase)
- Reduces rework and iteration cycles
- Validates implementation meets requirements
- Developer is responsible for test creation (tester verifies)

### Testing Scope
```yaml
phase_1_tests:
  - "[What to test in Phase 1]"
  - "Unit tests if implementation in Phase 1 (MANDATORY)"

phase_2_tests:
  - "[What to test in Phase 2]"
  - "Unit tests for implementation (MANDATORY)"

phase_3_tests:
  - "[What to test in Phase 3]"
  - "Integration tests and verification"

testing_approach: "[TDD | BDD | Integration | E2E]"
coverage_target: "≥ 80% (MANDATORY for implementation)"
```

### Test Checkpoints
- **After Phase 2**: Unit tests for implementation (MANDATORY - must exist and pass)
- **After Phase 3**: Integration tests and tester verification
- **After Phase 5**: End-to-end tests
- **At Each Checkpoint**: Full test suite run (100% pass rate required)

---

## 📈 Progress Tracking

### Phase Status
- [x] Phase 1: ✅ Completed
- [x] Phase 2: ✅ Completed
- [ ] Phase 3: ⏳ In Progress (60% complete)
- [ ] Phase 4: ☐ Not Started
- [ ] Phase 5: ☐ Not Started

### Overall Progress
**Completed**: [count]/[total] phases ([percentage]%)
**Estimated Remaining Time**: [X-Y hours AI time]
**Next Checkpoint**: Checkpoint 1 (after Phase 3)

---

## 📎 Related Artifacts

- **Analysis Document**: `/.claude/memory/reports/ANALYSIS-[ID].md`
- **TODO Tracker**: `/.claude/memory/todos/TODO-[ID].md`
- **Handoff Documents**: `/.claude/memory/handoffs/HANDOFF-[PlanID]-P[N]-to-P[N+1].md`
- **Checkpoint Reports**: `/.claude/memory/checkpoints/CHECKPOINT-[PlanID]-C[N].md`

---

## 📝 Plan Approval & Updates

**Plan Version**: 1.0
**Last Updated**: YYYY-MM-DD
**Approved By**: [PM | User]
**Status**: ☐ Draft | ☐ Approved | ⏳ In Progress | ☐ Completed

### Change Log
- **YYYY-MM-DD**: Plan created
- **YYYY-MM-DD**: [Change description]

---

**IMPORTANT FOR AGENTS**:
- 📖 **Read this entire plan** before starting your assigned task
- 🔍 **Review previous handoff** to understand context from previous agent
- ✅ **Complete quality gates** before marking task as done
- 🧪 **Write unit tests** where required
- 📤 **Create handoff document** for next agent when complete
- 🎯 **Keep plan vision in mind** while focusing on your specific task
