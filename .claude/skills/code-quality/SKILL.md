# Skill: Code Quality

## Purpose
Production-ready code quality workflow with smart scoping, incremental review, and fast feedback loops.

## When to Use
- After code changes need review
- Before merging PRs
- During development for quick quality checks
- As part of CI/CD pipeline integration

## Components

### Agents
| Agent | Role | Model |
|-------|------|-------|
| `@code-qa` | Fast, scoped review | Haiku |
| `@reviewer` | Deep analysis (escalation) | Sonnet |
| `@tester` | Test execution | Sonnet |

### Commands
| Command | Purpose |
|---------|---------|
| `/review` | Invoke code review |
| `/debug` | Investigate issues |

### Knowledge Loaded
| File | Purpose |
|------|---------|
| `code-quality-standards.md` | Quality standards |
| `quality-gates.md` | Pass/fail criteria |
| `agent-coordination.md` | Handoff protocols |

## Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ Developer completes changes                                 │
│ ↓                                                           │
│ PM invokes @code-qa (smart-scoped)                          │
│ ↓                                                           │
│ Code-QA reviews ONLY changed files (<500 lines)             │
│ ↓                                                           │
│ PASS → @tester for test execution                           │
│ CONDITIONAL → @developer fixes minor issues → re-review     │
│ FAIL → @developer fixes critical issues → full re-review    │
│ ESCALATE → @reviewer for deep analysis                      │
└─────────────────────────────────────────────────────────────┘
```

## Smart Scoping Rules

```yaml
scope_limits:
  max_files_per_pass: 5
  max_lines_per_file: 200
  max_total_lines: 500

priority_order:
  1: "Security-critical code"
  2: "New code (additions)"
  3: "Modified code (changes)"
  4: "Touched dependencies"

context_protection:
  - Never load unchanged files
  - Never load entire codebase
  - Split large reviews into passes
  - Report scope decisions to PM
```

## Quality Gates

### Blocking (Must Pass)
```yaml
critical_gates:
  - No security vulnerabilities
  - No hardcoded secrets
  - No breaking API changes without docs
  - No unhandled errors in critical paths
  - Tests pass (if @tester involved)
```

### Conditional (Should Fix)
```yaml
major_gates:
  - Error handling present
  - Input validation exists
  - No performance anti-patterns
  - Logic correctness verified
```

### Advisory (Recommendations)
```yaml
minor_gates:
  - Naming consistency
  - Code style compliance
  - Documentation present
  - No obvious duplication
```

## Escalation Triggers

When to escalate from `@code-qa` to `@reviewer`:

```yaml
escalate_when:
  - Security vulnerability confirmed
  - Architecture concerns detected
  - >10 files need review
  - Performance profiling required
  - Full audit explicitly requested
  - Complex refactoring involved
```

## Integration with Developer Chain

```yaml
standard_chain:
  pm_creates: "Plan with quality gates"
  developer: "Implements code"
  code_qa: "Fast review (Haiku, <2 min)"
  tester: "Test execution"
  auto_commit: "On all pass"

enhanced_chain:
  pm_creates: "Plan with strict quality"
  developer: "Implements code"
  code_qa: "Fast review"
  reviewer: "Deep analysis (if escalated)"
  security: "Security audit (if triggered)"
  tester: "Full test suite"
  auto_commit: "On all pass"
```

## Performance Targets

```yaml
code_qa_targets:
  review_time: "<2 minutes for typical PR"
  context_usage: "<2000 tokens input"
  report_length: "<500 tokens output"

reviewer_targets:
  review_time: "<10 minutes for complex review"
  context_usage: "<10000 tokens (smart loading)"
  report_length: "<2000 tokens"
```

## Report Format

### Code-QA Report (Fast)
```markdown
**CODE-QA REPORT**
Scope: [X files, Y lines]
Time: [Xms]
Status: [PASS/CONDITIONAL/FAIL]

Issues: [count by severity]
- CRITICAL: X
- MAJOR: Y
- MINOR: Z

Action: [Next step]
```

### Reviewer Report (Deep)
```markdown
**REVIEWER REPORT**
Scope: [comprehensive]
Quality Score: [X/10]

Detailed Analysis:
- Security: [findings]
- Performance: [findings]
- Maintainability: [findings]

Recommendations: [prioritised list]
```

## Metrics Tracked

```yaml
quality_metrics:
  - Review pass rate
  - Average review time
  - Issues caught per review
  - Escalation frequency
  - False positive rate
  - Developer satisfaction

archive_location: "/.claude/memory/reports/qa/"
retention: "30 days"
```

## Best Practices

### For Developers
- Keep commits small and focused
- Include context in commit messages
- Flag known issues for review focus
- Respond to minor issues promptly

### For PM
- Always include @code-qa after @developer
- Escalate to @reviewer for critical code
- Track quality metrics over time
- Adjust gates based on project phase

### For Code-QA
- Scope first, review second
- Report concisely
- Escalate appropriately
- Don't block on minor issues
