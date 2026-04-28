# Analysis Document - [Request Title]

**AnalysisID**: ANALYSIS-YYYYMMDD-[A-Z][0-9]+-\d{3}
**Request**: "[Original user request]"
**Date**: YYYY-MM-DD
**Status**: draft | reviewed | approved
**Created By**: PM Agent
**Reviewed By**: [business-analyst | researcher | architect]

---

## 📊 Executive Summary

**One-paragraph summary of the analysis, key findings, and recommended approach.**

---

## 🔍 Data Gathering

### 1. Request Analysis
```yaml
original_request: "[User's exact words]"
intent: "[What user really wants to achieve]"
explicit_requirements:
  - "[Requirement 1]"
  - "[Requirement 2]"
implicit_requirements:
  - "[Inferred requirement 1]"
  - "[Inferred requirement 2]"
constraints:
  - "[Constraint 1]"
  - "[Constraint 2]"
```

### 2. Context Gathering
```yaml
project_context:
  current_state: "[Current project status]"
  existing_systems: "[Related systems/modules]"
  dependencies: "[External dependencies]"

memory_consulted:
  - "/.claude/memory/standards/[file]"
  - "/.claude/memory/[relevant-file]"

patterns_identified:
  - "[Pattern 1 from standards]"
  - "[Pattern 2 from conventions]"
```

### 3. Stakeholder Needs
```yaml
primary_stakeholder: "[Who benefits]"
secondary_stakeholders: "[Other affected parties]"
success_criteria:
  - "[How we measure success 1]"
  - "[How we measure success 2]"
```

---

## 🧠 Semantic Analysis

### Request Classification
```yaml
complexity: trivial | small | medium | large | very_large
scope: single_file | multi_file | module | system | multi_system
domain: [frontend | backend | database | infrastructure | security | etc]
type: [new_feature | bug_fix | refactor | optimization | documentation | etc]
```

### Pattern Recognition
```yaml
semantic_patterns_detected:
  - "[Pattern 1: e.g., 'build api' → architecture needed]"
  - "[Pattern 2: e.g., 'authentication' → security review needed]"

architectural_implications:
  - "[Implication 1]"
  - "[Implication 2]"

security_implications:
  - "[Security consideration 1]"
  - "[Security consideration 2]"

performance_implications:
  - "[Performance consideration 1]"
  - "[Performance consideration 2]"
```

---

## 🎯 Strategic Assessment

### Approach Options
```yaml
option_1:
  name: "[Approach name]"
  description: "[How we would do it]"
  pros:
    - "[Pro 1]"
    - "[Pro 2]"
  cons:
    - "[Con 1]"
    - "[Con 2]"
  effort: [low | medium | high]
  risk: [low | medium | high]

option_2:
  name: "[Alternative approach]"
  description: "[How we would do it]"
  pros: [...]
  cons: [...]
  effort: [...]
  risk: [...]

recommended_approach: "option_1"
reasoning: "[Why we recommend this approach]"
```

### Required Capabilities
```yaml
agents_needed:
  - agent: architect
    reasoning: "[Why architect needed]"
    phase: "Phase 1 - Design"

  - agent: developer
    reasoning: "[Why developer needed]"
    phase: "Phase 2 - Implementation"

  - agent: tester
    reasoning: "[Why tester needed - MANDATORY with developer]"
    phase: "Phase 3 - Verification"

total_agents: [count]
delegation_needed: true | false
delegation_reasoning: "[If orchestrator needed, why]"
```

### Resource Requirements
```yaml
knowledge_modules_required:
  - module: "workflows/specialized/developer/[module].md"
    for_agent: developer
    reasoning: "[Why needed]"

tools_required:
  - "[Tool 1]"
  - "[Tool 2]"

dependencies:
  - "[Dependency 1]"
  - "[Dependency 2]"
```

---

## 📈 Scope Definition

### In Scope
- [ ] "[Deliverable 1]"
- [ ] "[Deliverable 2]"
- [ ] "[Deliverable 3]"

### Out of Scope
- "[What we're NOT doing]"
- "[What's deferred to later]"

### Assumptions
- "[Assumption 1]"
- "[Assumption 2]"

### Risks & Mitigation
```yaml
risk_1:
  description: "[Risk description]"
  impact: [low | medium | high]
  probability: [low | medium | high]
  mitigation: "[How we mitigate]"
```

---

## 📊 Effort Estimation

### Phase Breakdown
```yaml
phase_1_design:
  tasks: [count]
  agents: [list]
  estimated_time: "[X-Y minutes AI time]"

phase_2_implementation:
  tasks: [count]
  agents: [list]
  estimated_time: "[X-Y minutes AI time]"

total_phases: [count]
total_estimated_time: "[X-Y hours AI time]"
checkpoint_intervals: "Every 3 phases"
```

---

## ✅ Quality Gates

### Per-Phase Quality Gates
```yaml
design_phase:
  - "Architecture document reviewed and approved"
  - "Data model validated"

implementation_phase:
  - "Code follows project standards"
  - "Unit tests written and passing"

verification_phase:
  - "All tests passing"
  - "Code coverage >= 80%"
```

---

## 🎯 Recommended Next Steps

1. **Create Plan Document** - `PLAN-[ID].md` with phases, tasks, agents, handoffs
2. **Define Checkpoints** - Set checkpoints every 3 phases
3. **Assign Knowledge Modules** - Specify which knowledge each agent needs
4. **Create TODO Tracker** - `TODO-[ID].md` as simplified progress tracker
5. **Begin Execution** - Start with Phase 1 after plan approval

---

## 📎 Related Artifacts

- **Plan Document**: `/.claude/memory/plans/PLAN-[ID].md` (to be created)
- **TODO Tracker**: `/.claude/memory/todos/TODO-[ID].md` (to be created)

---

## 📝 Approval & Sign-off

**Analysis Status**: ⏳ Awaiting review
**Approved By**: [PM | User]
**Ready for Planning**: ☐ Yes  ☐ No

