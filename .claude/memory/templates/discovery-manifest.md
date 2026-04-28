---
discovery_id: "SCOPE-YYYYMMDD-XXX_description"
created_at: "YYYY-MM-DD HH:MM:SS"
status: "in-progress|completed|partial"
pm_request_id: "TODO-YYYYMMDD-XXX"
---

# Discovery Manifest

## Discovery Metadata

```yaml
discovery_id: "SCOPE-YYYYMMDD-XXX_description"
created_at: "YYYY-MM-DD HH:MM:SS"
created_by: "scoper"
status: "in-progress"
pm_request_id: "TODO-YYYYMMDD-XXX"

project_context:
  name: "[Project name]"
  description: "[Brief description]"
  codebase_path: "[Path to codebase]"

investigation_scope:
  focus_areas: "[comprehensive|specific areas]"
  requested_aspects:
    - "architecture"
    - "code quality"
    - "testing"
    - "stability"
    - "dependencies"
```

## Investigation Plan

```yaml
agent_sequence:
  1_mini_troubleshooter:
    purpose: "File structure inventory and quick pattern scan"
    status: "pending"
    started_at: null
    completed_at: null

  2_architect:
    purpose: "System architecture and design pattern analysis"
    status: "pending"
    started_at: null
    completed_at: null

  3_reviewer:
    purpose: "Code quality and technical debt assessment"
    status: "pending"
    started_at: null
    completed_at: null

  4_tester:
    purpose: "Test coverage and quality gate evaluation"
    status: "pending"
    started_at: null
    completed_at: null

  5_troubleshooter:
    purpose: "Known issues and stability risk analysis"
    status: "pending"
    started_at: null
    completed_at: null
```

## Discovery Execution Log

### Phase 1: Initialization
- **Started**: YYYY-MM-DD HH:MM:SS
- **Folder Structure Created**: Yes/No
- **Request Analysis Completed**: Yes/No
- **Investigation Plan Approved**: Yes/No

### Phase 2: Agent Coordination
- **Mini-Troubleshooter**: Status (pending|in-progress|completed|failed)
- **Architect**: Status (pending|in-progress|completed|failed)
- **Reviewer**: Status (pending|in-progress|completed|failed)
- **Tester**: Status (pending|in-progress|completed|failed)
- **Troubleshooter**: Status (pending|in-progress|completed|failed)

### Phase 3: Synthesis
- **Findings Aggregated**: Yes/No
- **Patterns Identified**: Yes/No
- **Cross-References Completed**: Yes/No
- **Synthesis Report Created**: Yes/No
- **Recommendations Generated**: Yes/No

### Phase 4: PM Handoff
- **PM Notified**: Yes/No
- **Handoff Completed**: YYYY-MM-DD HH:MM:SS
- **Ready for Planning**: Yes/No/Partial

## Agent Findings Summary

```yaml
mini_troubleshooter:
  status: "pending"
  outputs: []
  key_findings: null

architect:
  status: "pending"
  outputs: []
  key_findings: null

reviewer:
  status: "pending"
  outputs: []
  key_findings: null

tester:
  status: "pending"
  outputs: []
  key_findings: null

troubleshooter:
  status: "pending"
  outputs: []
  key_findings: null
```

## Discovery Statistics

```yaml
files_analyzed: 0
patterns_detected: 0
issues_identified: 0
recommendations_generated: 0

coverage_metrics:
  architecture: "not_assessed"
  code_quality: "not_assessed"
  testing: "not_assessed"
  stability: "not_assessed"
  dependencies: "not_assessed"
```

## Issues and Blockers

```yaml
errors_encountered: []
blockers: []
partial_completions: []
```

## Deliverables Checklist

- [ ] 01-REQUEST.md (PM request verbatim)
- [ ] 02-INVESTIGATION-PLAN.md (Scoper's strategy)
- [ ] findings/mini-troubleshooter/*.md
- [ ] findings/architect/*.md
- [ ] findings/reviewer/*.md
- [ ] findings/tester/*.md
- [ ] findings/troubleshooter/*.md
- [ ] 98-SYNTHESIS.md (Comprehensive synthesis)
- [ ] 99-RECOMMENDATIONS.md (Actionable recommendations)
- [ ] This manifest file updated with final status

## Notes

<!-- Scoper: Add notes about discovery process, deviations from plan, insights -->

---

**Status**: [in-progress|completed|partial]
**Last Updated**: YYYY-MM-DD HH:MM:SS
**Updated By**: scoper
