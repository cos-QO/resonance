---
name: review
description: Human-judgment code review — standards compliance, security patterns, performance analysis, and architectural feedback. Triggers when user asks for code review, quality audit, or PR review. NOT for running automated tests (use /verify).
argument-hint: [scope]
context: fork
agent: reviewer
skills: [universal-testing-mindset, universal-security-patterns, universal-performance-patterns]
---
# /review — Code Quality Review

Run a comprehensive review of recent changes or specified scope.

## Review Phases
1. **Context** — Load project standards and understand scope
2. **Completion check** — Verify all planned work is done
3. **Code quality** — Standards, patterns, best practices
4. **Security** — Vulnerability patterns, input validation, auth
5. **Performance** — N+1 queries, caching, optimization opportunities
6. **Testing** — Test coverage, edge cases, test quality
7. **Documentation** — API docs, comments where needed
8. **Summary** — Findings report with severity ratings

## Output
- Findings categorized by severity (critical/high/medium/low)
- Specific file:line references for each finding
- Suggested fixes

## Arguments
- `$ARGUMENTS` — Optional scope (e.g., "frontend", "api", specific files)
