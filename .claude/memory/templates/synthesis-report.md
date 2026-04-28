---
discovery_id: "SCOPE-YYYYMMDD-XXX_description"
report_type: "synthesis"
created_at: "YYYY-MM-DD HH:MM:SS"
confidence_overall: "HIGH|MEDIUM|LOW"
---

# Discovery Synthesis Report

## Executive Summary

[2-3 paragraph high-level summary of the discovery]

**Overall Assessment**: [Brief statement of project health and readiness]

**Top 3 Key Findings**:
1. [Most critical discovery with confidence level]
2. [Second most critical discovery with confidence level]
3. [Third most critical discovery with confidence level]

**Ready for Planning**: [YES|NO|PARTIAL] - [Explanation]

**Critical Issues**: [Number] issues requiring immediate attention

---

## Investigation Scope

```yaml
discovery_id: "SCOPE-YYYYMMDD-XXX_description"
investigation_date: "YYYY-MM-DD"
requested_by: "PM"
pm_request_id: "TODO-YYYYMMDD-XXX"

project_context:
  name: "[Project name]"
  description: "[Brief description]"
  codebase_location: "[Path]"

investigation_aspects:
  - architecture: "✅ Completed"
  - code_quality: "✅ Completed"
  - testing: "✅ Completed"
  - stability: "✅ Completed"
  - dependencies: "✅ Completed"

agents_involved:
  - mini-troubleshooter
  - architect
  - reviewer
  - tester
  - troubleshooter
```

---

## Key Findings by Category

### Architecture

**Overall Assessment**: [excellent|good|acceptable|poor]
**Confidence**: [HIGH|MEDIUM|LOW]

#### Architecture Style
[Identified architecture pattern - monolith, microservices, hybrid, etc.]

#### Design Patterns
[Major design patterns detected and their health assessment]

#### Scalability
[Current capacity and scaling characteristics]

#### Integration Points
[External integrations and their reliability]

#### Technology Stack
[Stack assessment and modernization needs]

**Key Insights**:
- [Insight 1 with evidence]
- [Insight 2 with evidence]
- [Insight 3 with evidence]

**Evidence Sources**: architect/01-ARCHITECTURE-STYLE.md, architect/02-DESIGN-PATTERNS.md

---

### Code Quality

**Overall Quality**: [excellent|good|acceptable|poor]
**Confidence**: [HIGH|MEDIUM|LOW]

#### Quality Metrics
- **Readability**: [X/10]
- **Maintainability**: [X/10]
- **Complexity**: [Average cyclomatic complexity]
- **Function Length**: [Average LOC]

#### Technical Debt
- **Total Items**: [Count]
- **High Priority**: [Count]
- **Estimated Effort**: [Hours/days to address]

#### Best Practices Compliance
[Assessment of adherence to standards and best practices]

#### Refactoring Opportunities
[High-ROI refactoring opportunities identified]

**Key Insights**:
- [Insight 1 with evidence]
- [Insight 2 with evidence]
- [Insight 3 with evidence]

**Evidence Sources**: reviewer/01-CODE-QUALITY-ASSESSMENT.md, reviewer/02-TECHNICAL-DEBT.md

---

### Testing

**Overall Coverage**: [X%]
**Target Coverage**: [X%]
**Assessment**: [excellent|good|acceptable|poor]
**Confidence**: [HIGH|MEDIUM|LOW]

#### Coverage by Layer
- **Unit Tests**: [X%]
- **Integration Tests**: [X%]
- **E2E Tests**: [X%]

#### Critical Testing Gaps
[Most important gaps identified with priority]

#### Quality Gates
[CI/CD testing integration assessment]

#### Testing Framework
[Framework evaluation and recommendations]

**Key Insights**:
- [Insight 1 with evidence]
- [Insight 2 with evidence]
- [Insight 3 with evidence]

**Evidence Sources**: tester/01-TEST-COVERAGE-ANALYSIS.md, tester/03-TESTING-GAPS.md

---

### Stability & Reliability

**Overall Stability**: [stable|mostly-stable|unstable|critical]
**Confidence**: [HIGH|MEDIUM|LOW]

#### Known Issues
- **Total Issues**: [Count]
- **Critical Issues**: [Count]
- **High Priority Issues**: [Count]

#### Risk Assessment
- **Critical Risks**: [Count]
- **High Risks**: [Count]

#### Resilience Mechanisms
[Assessment of retry, circuit breaker, fallback patterns]

#### Observability
[Monitoring, logging, alerting assessment]

**Key Insights**:
- [Insight 1 with evidence]
- [Insight 2 with evidence]
- [Insight 3 with evidence]

**Evidence Sources**: troubleshooter/01-KNOWN-ISSUES-CATALOG.md, troubleshooter/02-RISK-ASSESSMENT-MATRIX.md

---

### Dependencies

**Internal Dependencies**: [Assessment]
**External Dependencies**: [Assessment]
**Confidence**: [HIGH|MEDIUM|LOW]

#### Dependency Health
[Analysis of dependency versions, security, maintenance status]

#### Integration Stability
[Assessment of external API integrations]

#### Modernization Needs
[Outdated dependencies requiring updates]

**Key Insights**:
- [Insight 1 with evidence]
- [Insight 2 with evidence]
- [Insight 3 with evidence]

**Evidence Sources**: architect/05-TECHNOLOGY-STACK.md, troubleshooter/03-STABILITY-ANALYSIS.md

---

## Cross-Cutting Insights

[Patterns and themes appearing across multiple categories]

### Systemic Issues
1. [Issue appearing in multiple agent findings]
2. [Another cross-cutting concern]

### Architectural Themes
1. [Architectural pattern or principle recurring across findings]
2. [Another architectural theme]

### Quality Themes
1. [Quality pattern appearing in multiple areas]
2. [Another quality theme]

---

## Validation Results

```yaml
cross_agent_validation:
  high_confidence_findings:
    - finding: "[Finding confirmed by 3+ agents]"
      agents: [agent1, agent2, agent3]
      confidence: "HIGH"

  medium_confidence_findings:
    - finding: "[Finding confirmed by 2 agents or validated by tests]"
      agents: [agent1, agent2]
      confidence: "MEDIUM"

  flagged_contradictions:
    - issue: "[Disagreement between agents]"
      agent1_view: "[Perspective 1]"
      agent2_view: "[Perspective 2]"
      recommendation: "PM review required"
      confidence: "MEDIUM"

test_validation_results:
  tests_run: [Number]
  tests_passed: [Number]
  tests_failed: [Number]
  new_issues_discovered: [Number]
```

---

## Findings Confidence Matrix

| Category | Coverage | Validation | Confidence | Notes |
|----------|----------|------------|------------|-------|
| Architecture | [comprehensive\|partial] | [high\|medium\|low] | HIGH/MEDIUM/LOW | [Notes] |
| Code Quality | [comprehensive\|partial] | [high\|medium\|low] | HIGH/MEDIUM/LOW | [Notes] |
| Testing | [comprehensive\|partial] | [high\|medium\|low] | HIGH/MEDIUM/LOW | [Notes] |
| Stability | [comprehensive\|partial] | [high\|medium\|low] | HIGH/MEDIUM/LOW | [Notes] |
| Dependencies | [comprehensive\|partial] | [high\|medium\|low] | HIGH/MEDIUM/LOW | [Notes] |

**Overall Confidence**: [HIGH|MEDIUM|LOW]

---

## Identified Patterns

### Pattern 1: [Pattern Name]

```yaml
type: "[architecture|code|testing|etc]"
prevalence: "[widespread|common|localized|rare]"
health: "[good|acceptable|needs-refactoring|problematic]"
confidence: "[HIGH|MEDIUM|LOW]"

description: "[What the pattern is]"

evidence:
  - "[Specific examples with file locations]"
  - "[Metrics or measurements]"
  - "[Agent findings supporting this]"

assessment:
  strengths: "[What works well]"
  concerns: "[What could be improved]"

recommendation: "[keep|improve|refactor|replace]"
rationale: "[Why this recommendation]"

impact_on_project: "[How this affects project goals]"
```

### Pattern 2: [Pattern Name]

[Same structure as Pattern 1]

[Continue for all significant patterns detected]

---

## Gap Analysis

### Documentation Gaps
- [Gap 1: Description, Impact, Priority]
- [Gap 2: Description, Impact, Priority]

### Testing Gaps
- [Gap 1: Description, Impact, Priority]
- [Gap 2: Description, Impact, Priority]

### Security Gaps
- [Gap 1: Description, Impact, Priority]
- [Gap 2: Description, Impact, Priority]

### Performance Gaps
- [Gap 1: Description, Impact, Priority]
- [Gap 2: Description, Impact, Priority]

---

## PM Handoff Summary

### Discovery Status

**Status**: [COMPLETED|PARTIAL|INCOMPLETE]
**Completeness**: [X% of planned investigation completed]
**Confidence in Findings**: [HIGH|MEDIUM|LOW]

### Top 3 Executive-Level Findings

1. **[Critical Finding 1]**
   - **Category**: [Architecture|Quality|Testing|Stability]
   - **Confidence**: [HIGH|MEDIUM|LOW]
   - **Impact**: [Business/technical impact]
   - **Recommendation**: [Brief recommendation]

2. **[Critical Finding 2]**
   - **Category**: [Architecture|Quality|Testing|Stability]
   - **Confidence**: [HIGH|MEDIUM|LOW]
   - **Impact**: [Business/technical impact]
   - **Recommendation**: [Brief recommendation]

3. **[Critical Finding 3]**
   - **Category**: [Architecture|Quality|Testing|Stability]
   - **Confidence**: [HIGH|MEDIUM|LOW]
   - **Impact**: [Business/technical impact]
   - **Recommendation**: [Brief recommendation]

### Recommended Next Steps

1. [Immediate action 1 - what PM should do first]
2. [Follow-up action 2 - what should happen next]
3. [Planning step 3 - how to incorporate findings]

### Blockers (if any)

[List any blockers discovered that would prevent implementation]

### Ready for Planning?

**Answer**: [YES|NO|PARTIAL]

**Explanation**: [Why the project is or isn't ready for planning based on findings]

**Conditions for Readiness** (if PARTIAL):
- [Condition 1 that needs to be met]
- [Condition 2 that needs to be met]

---

## Quick Stats

```yaml
discovery_metrics:
  files_analyzed: [Number]
  patterns_detected: [Number]
  issues_identified: [Number]
  critical_issues: [Number]
  high_priority_recommendations: [Number]

agent_completion:
  mini_troubleshooter: "✅ completed"
  architect: "✅ completed"
  reviewer: "✅ completed"
  tester: "✅ completed"
  troubleshooter: "✅ completed"

time_metrics:
  discovery_started: "YYYY-MM-DD HH:MM:SS"
  discovery_completed: "YYYY-MM-DD HH:MM:SS"
  total_duration: "[X minutes]"
```

---

## Appendices

### Appendix A: Agent Output Locations

- **Mini-Troubleshooter**: findings/mini-troubleshooter/
- **Architect**: findings/architect/
- **Reviewer**: findings/reviewer/
- **Tester**: findings/tester/
- **Troubleshooter**: findings/troubleshooter/

### Appendix B: Artifacts

- **File Trees**: artifacts/file-trees/
- **Test Results**: artifacts/test-results/
- **Diagrams**: artifacts/diagrams/
- **Raw Data**: artifacts/raw-data/

### Appendix C: Follow-Up Discovery Recommendations

[If discovery revealed areas requiring deeper investigation, list them here]

---

**Report Generated**: YYYY-MM-DD HH:MM:SS
**Generated By**: scoper
**Discovery ID**: SCOPE-YYYYMMDD-XXX_description
**Confidence Level**: [HIGH|MEDIUM|LOW]
