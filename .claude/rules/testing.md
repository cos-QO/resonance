---
paths:
  - "**/*.test.*"
  - "**/*.spec.*"
  - "**/tests/**"
  - "**/__tests__/**"
---
# Testing Rules

## Test Standards
- Unit tests for business logic and utilities
- Integration tests for API endpoints and database operations
- E2E tests for critical user flows
- Mock external services, not internal modules
- Test error paths, not just happy paths

## Test Structure
- Arrange-Act-Assert pattern
- Descriptive test names that explain the scenario
- One assertion concept per test
- Shared setup in beforeEach/beforeAll, not duplicated

## Coverage
- New features: must include tests
- Bug fixes: must include regression test
- Refactors: existing tests must still pass

## TDD Iron Law

**No production code without a failing test first.**

The cycle is non-negotiable:
1. **RED** — Write a failing test that defines expected behavior
2. **GREEN** — Write the minimum production code to make the test pass
3. **REFACTOR** — Clean up both test and production code while keeping tests green

If you find yourself writing production code first, STOP and write the test. Code written before tests is confirmation-biased and misses edge cases.

**Applies to**: new features, bug fixes, behavior changes, refactors that alter behavior.
**Exceptions**: config-only changes, generated code, throwaway spikes (must be marked as such).

## Rationalization Rejection Table

These excuses for skipping tests are NEVER valid:

| Rationalization | Why it's wrong | What to do instead |
|---|---|---|
| "It's too simple to test" | Simple code breaks when dependencies change | Write a one-liner assertion — fast and cheap |
| "I'll write tests after" | Tests-after are confirmation-biased, miss edge cases | Write the test NOW, before the code |
| "It's just a refactor" | Refactors introduce regressions; tests catch them | Run existing tests first, add tests for uncovered paths |
| "The types guarantee correctness" | Types don't catch logic errors, off-by-ones, or integration bugs | Types + tests, never types instead of tests |
| "It's a prototype / spike" | Prototypes without tests become production code with no safety net | At minimum, write characterization tests for key behaviors |
| "Time pressure — we'll add later" | Untested code slows future work; debt compounds | A failing test takes 2 minutes; debugging without one takes 20 |

## Enforcement

- Reject changes where production code was added without corresponding tests
- Flag tests that assert implementation details instead of behavior
- Every bug fix MUST include a regression test that would have caught the original bug
- Coverage of new code: >80% line coverage minimum
