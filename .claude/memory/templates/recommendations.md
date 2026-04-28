---
discovery_id: "SCOPE-YYYYMMDD-XXX_description"
report_type: "recommendations"
created_at: "YYYY-MM-DD HH:MM:SS"
total_recommendations: 0
---

# Discovery Recommendations

## Overview

This document provides **actionable, prioritized recommendations** based on the discovery investigation conducted by the Scoper agent. Each recommendation includes rationale, impact assessment, effort estimation, and suggested implementation approach.

**Discovery Reference**: [SCOPE-YYYYMMDD-XXX_description]
**Synthesis Report**: See 98-SYNTHESIS.md for comprehensive findings
**Total Recommendations**: [Number]

---

## Recommendation Summary

```yaml
by_priority:
  immediate: [Count] # Start within days
  short_term: [Count] # Address within weeks/months
  long_term: [Count] # Plan for future quarters

by_category:
  architecture: [Count]
  code_quality: [Count]
  testing: [Count]
  security: [Count]
  stability: [Count]
  performance: [Count]
  documentation: [Count]

estimated_total_effort: "[X weeks/months]"
```

---

## Immediate Actions (High Priority)

> **Timeline**: Start within days
> **Impact**: CRITICAL - Addresses security vulnerabilities, blocking issues, or compliance violations

### Recommendation 1: [Title]

```yaml
id: "REC-001"
category: "[architecture|quality|testing|security|stability|performance]"
priority: "IMMEDIATE"
confidence: "[HIGH|MEDIUM|LOW]"

rationale:
  why_needed: "[Why is this needed?]"
  problem_solved: "[What problem does it solve?]"
  risk_mitigated: "[What risk does it mitigate?]"

impact:
  expected_outcome: "[Expected outcome]"
  benefit_to_project: "[Benefit to project]"
  risk_reduction: "[Risk reduction]"
  business_value: "[Business value if applicable]"

implementation:
  agents_needed: [list of agent types]
  sequence: "[Sequential steps or phases]"
  dependencies: "[What must be done first]"

effort_estimate:
  time: "[Hours/days]"
  complexity: "[low|medium|high]"
  resources_required: "[Team members, tools, etc.]"

success_criteria:
  - "[How to measure success 1]"
  - "[How to measure success 2]"
  - "[Acceptance criteria]"

risk_mitigation:
  potential_issues: "[What could go wrong]"
  mitigation_strategy: "[How to mitigate]"
  rollback_plan: "[How to rollback if needed]"

evidence_sources:
  - "[Agent findings reference]"
  - "[Specific file/location]"
```

### Recommendation 2: [Title]

[Same structure as Recommendation 1]

---

## Short-Term Actions (Medium Priority)

> **Timeline**: Address within weeks/months
> **Impact**: HIGH/MEDIUM - Technical debt causing friction, missing quality gates, performance issues

### Recommendation 3: [Title]

```yaml
id: "REC-003"
category: "[category]"
priority: "SHORT_TERM"
confidence: "[HIGH|MEDIUM|LOW]"

rationale:
  why_needed: "[Why is this needed?]"
  problem_solved: "[What problem does it solve?]"
  risk_mitigated: "[What risk does it mitigate?]"

impact:
  expected_outcome: "[Expected outcome]"
  benefit_to_project: "[Benefit to project]"
  technical_debt_reduction: "[Debt reduction]"

implementation:
  agents_needed: [list]
  sequence: "[Steps]"

effort_estimate:
  time: "[Days/weeks]"
  complexity: "[low|medium|high]"

success_criteria:
  - "[Criteria 1]"
  - "[Criteria 2]"

evidence_sources:
  - "[References]"
```

[Continue for all short-term recommendations]

---

## Long-Term Considerations (Low Priority)

> **Timeline**: Plan for future quarters
> **Impact**: MEDIUM/LOW - Architecture improvements, optimization opportunities, nice-to-have refactoring

### Recommendation X: [Title]

```yaml
id: "REC-00X"
category: "[category]"
priority: "LONG_TERM"
confidence: "[HIGH|MEDIUM|LOW]"

rationale:
  why_needed: "[Strategic improvement]"
  problem_solved: "[Future-proofing]"
  opportunity: "[Optimization opportunity]"

impact:
  expected_outcome: "[Outcome]"
  strategic_benefit: "[Long-term benefit]"
  roi: "[Return on investment]"

implementation:
  agents_needed: [list]
  phased_approach: "[How to break into phases]"

effort_estimate:
  time: "[Weeks/months]"
  complexity: "[medium|high]"
  resources_required: "[Resources]"

success_criteria:
  - "[Long-term success metric 1]"
  - "[Long-term success metric 2]"

evidence_sources:
  - "[References]"
```

[Continue for all long-term recommendations]

---

## Suggested Agent Chains

Based on the recommendations above, here are suggested agent workflows for implementation:

### Chain 1: [Workflow Name] (for Recommendations REC-001, REC-003)

```yaml
workflow_name: "[Descriptive name]"
applies_to: ["REC-001", "REC-003"]
total_duration: "[Estimated time]"

phases:
  phase_1:
    name: "[Phase name]"
    agents: [agent1, agent2]
    focus: "[What this phase accomplishes]"
    duration: "[Estimated time]"
    outputs:
      - "[Deliverable 1]"
      - "[Deliverable 2]"

  phase_2:
    name: "[Phase name]"
    agents: [agent3, agent4]
    focus: "[What this phase accomplishes]"
    duration: "[Estimated time]"
    dependencies: ["phase_1"]
    outputs:
      - "[Deliverable 1]"
      - "[Deliverable 2]"

  phase_3:
    name: "[Phase name - usually validation/review]"
    agents: [tester, reviewer]
    focus: "[Validation and quality assurance]"
    duration: "[Estimated time]"
    dependencies: ["phase_2"]
    outputs:
      - "[Test results]"
      - "[Review report]"

quality_gates:
  - gate: "[Coverage threshold]"
    phase: "phase_3"
    blocking: true
  - gate: "[Security scan]"
    phase: "phase_3"
    blocking: true

success_criteria:
  - "[Overall workflow success metric]"
  - "[Validation criteria]"
```

### Chain 2: [Workflow Name] (for Recommendations REC-002, REC-004)

[Same structure as Chain 1]

---

## Risk Mitigation Strategies

### High-Risk Recommendations

For recommendations involving critical systems or significant changes:

#### REC-001: [Title]

**Risks**:
- [Risk 1: Description and likelihood]
- [Risk 2: Description and likelihood]

**Mitigation**:
- [Mitigation strategy 1]
- [Mitigation strategy 2]

**Rollback Plan**:
- [Step-by-step rollback procedure]

**Validation**:
- [How to validate before full deployment]

---

## Resource Requirements

```yaml
team_resources:
  developers: "[Number needed and for how long]"
  testers: "[Number needed and for how long]"
  security_specialists: "[If needed]"
  devops: "[If needed]"

infrastructure:
  environments: "[Staging, testing, etc.]"
  tools: "[New tools needed]"
  services: "[External services needed]"

budget_estimate:
  personnel: "[Cost estimate]"
  infrastructure: "[Cost estimate]"
  tools_licenses: "[Cost estimate]"
  total: "[Total budget estimate]"
```

---

## Success Criteria

### Overall Success Metrics

```yaml
immediate_actions:
  metric: "[How to measure success of immediate actions]"
  target: "[Target value]"
  measurement: "[How to measure]"

short_term_actions:
  metric: "[How to measure success of short-term actions]"
  target: "[Target value]"
  measurement: "[How to measure]"

long_term_improvements:
  metric: "[How to measure success of long-term improvements]"
  target: "[Target value]"
  measurement: "[How to measure]"

project_health_indicators:
  code_quality: "[Target improvement]"
  test_coverage: "[Target improvement]"
  technical_debt: "[Target reduction]"
  stability: "[Target improvement]"
  performance: "[Target improvement]"
```

---

## Memory Updates Recommended

Based on discovery findings, the following memory updates are recommended:

### Standards to Update

1. **[Standard file to update]**
   - **Reason**: [Why it needs updating]
   - **Additions**: [What to add]
   - **Priority**: [HIGH|MEDIUM|LOW]

2. **[Another standard file]**
   - **Reason**: [Why it needs updating]
   - **Additions**: [What to add]
   - **Priority**: [HIGH|MEDIUM|LOW]

### New Patterns to Document

1. **[Pattern name]**
   - **Location**: [Where to document it]
   - **Description**: [Brief description]
   - **Example**: [Code example or reference]

### Conventions to Establish

1. **[Convention name]**
   - **Area**: [Where it applies]
   - **Rule**: [The convention rule]
   - **Rationale**: [Why this convention]

---

## Follow-Up Discovery Recommendations

[If discovery revealed areas requiring deeper investigation before implementation]

### Recommended Additional Investigations

1. **[Investigation topic]**
   - **Scope**: [What to investigate]
   - **Reason**: [Why deeper investigation needed]
   - **Agents**: [Which agents to use]
   - **Estimated Time**: [Time estimate]
   - **Blocking**: [Does this block implementation?]

2. **[Another investigation topic]**
   [Same structure]

---

## Implementation Roadmap

Suggested phased implementation approach:

### Sprint 1 (Immediate - Days 1-7)
- [ ] REC-001: [Title] ([X days])
- [ ] REC-002: [Title] ([X days])

**Deliverables**: [Expected outputs]
**Success Gate**: [How to measure sprint success]

### Sprint 2 (Short-term - Weeks 2-4)
- [ ] REC-003: [Title] ([X days])
- [ ] REC-004: [Title] ([X days])
- [ ] REC-005: [Title] ([X days])

**Deliverables**: [Expected outputs]
**Success Gate**: [How to measure sprint success]

### Quarter 1 (Long-term - Months 1-3)
- [ ] REC-006: [Title] ([X weeks])
- [ ] REC-007: [Title] ([X weeks])

**Deliverables**: [Expected outputs]
**Success Gate**: [How to measure quarter success]

---

## Appendices

### Appendix A: Recommendation Cross-Reference Matrix

| Rec ID | Category | Priority | Effort | Agent Chain | Dependencies |
|--------|----------|----------|--------|-------------|--------------|
| REC-001 | [Cat] | IMMEDIATE | [X days] | Chain 1 | None |
| REC-002 | [Cat] | IMMEDIATE | [X days] | Chain 2 | None |
| REC-003 | [Cat] | SHORT_TERM | [X days] | Chain 1 | REC-001 |
| ... | ... | ... | ... | ... | ... |

### Appendix B: Evidence Summary

Links to detailed evidence for each recommendation:

- **REC-001**: [List of evidence sources from agent findings]
- **REC-002**: [List of evidence sources]
- [Continue for all recommendations]

### Appendix C: Cost-Benefit Analysis

| Rec ID | Effort (days) | Risk Reduction | Business Value | ROI Score |
|--------|---------------|----------------|----------------|-----------|
| REC-001 | [X] | CRITICAL | HIGH | 9/10 |
| REC-002 | [X] | HIGH | MEDIUM | 8/10 |
| ... | ... | ... | ... | ... |

---

**Report Generated**: YYYY-MM-DD HH:MM:SS
**Generated By**: scoper
**Discovery ID**: SCOPE-YYYYMMDD-XXX_description
**Total Recommendations**: [Number]
**Immediate**: [Count] | **Short-Term**: [Count] | **Long-Term**: [Count]
