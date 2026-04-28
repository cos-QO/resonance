---
name: debug
description: "Use when encountering errors, crashes, test failures, stack traces, or unexpected behavior that needs root cause analysis. Delegates to troubleshooter agent's multi-tier system. NOT for researching technologies (use /research) or reviewing code quality (use /review)."
argument-hint: [error-description]
context: fork
agent: troubleshooter
---
# /debug — Systematic Debugging

Investigate errors using the troubleshooter agent's multi-tier system with structured root cause analysis.

## Iron Law

**NO FIXES WITHOUT ROOT CAUSE.** Never apply a fix based on a guess. Every fix must trace back to a confirmed root cause with evidence. "I think it might be X" is not a root cause — "The stack trace shows X fails at line Y because Z" is.

## 4-Phase Process

### Phase 1: Root Cause Investigation
- Read error messages, stack traces, and logs carefully and completely
- Reproduce the issue consistently before investigating
- For complex issues: spawn mini-troubleshooters for parallel data gathering
- Check recent changes (`git log`, `git diff`) for likely culprits
- **Gate**: Must identify root cause with evidence before proceeding to Phase 3

### Phase 2: Pattern Analysis
- Search `/.claude/memory/reports/troubleshooting/` for prior occurrences
- Find working examples of the same pattern elsewhere in the codebase
- Compare working vs broken code — identify the actual difference
- Understand the full dependency chain, not just the immediate error site

### Phase 3: Hypothesis Testing
- Formulate a single hypothesis tied to the confirmed root cause
- Test one variable at a time — never apply multiple changes simultaneously
- **Gate**: Hypothesis must explain ALL observed symptoms, not just the primary one

### Phase 4: Implementation Recommendation
- Synthesize findings into TS-ID report with root cause analysis
- Provide prioritized solution recommendations
- Recommend fix agent (usually developer) after diagnosis
- Save report to `/.claude/memory/reports/troubleshooting/`

## Team Scaling
- Simple error: 1 troubleshooter alone (30-60 sec)
- Medium complexity: 1 troubleshooter + 2-4 mini-troubleshooters (60-120 sec)
- Complex investigation: Multiple troubleshooters + 4-6 minis (90-180 sec)

## Failure Circuit Breaker

| Failed Fixes | Action |
|---|---|
| 1st fix fails | Re-investigate with escalated team size |
| 2nd fix fails | Full team investigation, question ALL assumptions |
| 3rd fix fails | **STOP.** Escalate to @architect. This is likely an architectural issue, not a code bug. |

After 3 failed fixes, do not attempt more fixes without architectural review. The problem is almost certainly not where you think it is.

## Red Flags (escalate to full team immediately)
- Error moves when you add logging (Heisenbug)
- Fix works locally but fails in CI/test environment
- Multiple unrelated tests break after a "simple" change
- Error message doesn't match the actual failure point
- Same error returns after being "fixed" in a previous session

## Rules
- Track previously attempted solutions to avoid repeating them
- Generate TS-ID report for every investigation
- Reference previous TS-ID reports when investigating recurring issues
- Never skip Phase 1 — even for "obvious" bugs

## Arguments
- `$ARGUMENTS` — Error description, stack trace, or unexpected behavior
