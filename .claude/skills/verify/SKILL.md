---
name: verify
description: Automated test and quality pipeline. Runs build validation, linting, unit tests, integration tests, security scans, and smoke tests. Invoked by PM/tester after implementation — NOT for manual code review (use /review). Accepts L1 (fast), L2 (standard), or L3 (thorough) level.
context: fork
agent: tester
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
disable-model-invocation: true
---
# Post-Task Verification Pipeline

You are running the **verification pipeline** on recently implemented code. This pipeline is adaptive — detect what's available and skip what's not.

## Step 1: Detect Project Environment

Before running any checks, detect what's available:

```bash
# Detect project type and tools — run these checks
ls package.json pyproject.toml setup.py Makefile Dockerfile docker-compose.yml 2>/dev/null
ls .eslintrc* .prettierrc* ruff.toml pyproject.toml tox.ini 2>/dev/null
ls jest.config* vitest.config* pytest.ini conftest.py 2>/dev/null
ls playwright.config* cypress.config* 2>/dev/null
ls k6* locust* 2>/dev/null
```

Build a checklist of which phases apply based on what exists. Skip phases where no tooling is configured.

## Step 2: Determine Verification Level

Check if a level was specified in $ARGUMENTS. If not, default to L2.

| Level | When | Phases |
|-------|------|--------|
| **L1** (fast) | Quick fix, typo, small change | 1 → 3 → 10 |
| **L2** (standard) | Feature, bug fix, refactor | 1 → 2 → 3 → 4 → 6 → 9 → 10 |
| **L3** (thorough) | Security-sensitive, release, critical | All 10 phases |

## Step 3: Run Applicable Phases

### Phase 1 — Build Validation (ALWAYS)

Ensure code compiles and dependencies resolve.

| Project Type | Commands |
|---|---|
| Python | `python -m py_compile <changed_files>`, `pip check` |
| Node | `npm run build` or `npx tsc --noEmit` |
| Docker | `docker build --check .` (if Dockerfile exists) |

**Stop on failure.** Nothing else matters if it doesn't build.

### Phase 2 — Static Analysis (L2+)

Run configured linters only. Skip unconfigured ones.

| Tool | Detect By | Command |
|---|---|---|
| ESLint | `.eslintrc*` or `eslint` in package.json | `npx eslint <changed_files>` |
| Prettier | `.prettierrc*` or `prettier` in package.json | `npx prettier --check <changed_files>` |
| Ruff | `ruff.toml` or `[tool.ruff]` in pyproject.toml | `ruff check <changed_files>` |
| Pylint | `pylintrc` or `pylint` in requirements | `pylint <changed_files>` |
| Black | `[tool.black]` in pyproject.toml | `black --check <changed_files>` |

**Threshold**: Zero errors. Warnings are informational only.

### Phase 3 — Unit Tests (ALWAYS)

Run the project's existing test suite.

| Framework | Detect By | Command |
|---|---|---|
| pytest | `conftest.py` or `pytest.ini` or `[tool.pytest]` | `pytest -x --tb=short` |
| vitest | `vitest.config.*` | `npx vitest run` |
| jest | `jest.config.*` or `jest` in package.json | `npx jest` |

If no test framework detected, report "No test framework found" as a warning (not a failure).

**Stop on failure.** Broken tests must be fixed before continuing.

### Phase 4 — Integration Tests (L2+)

Only if integration test directory exists (`tests/integration/`, `__tests__/integration/`, `test/integration/`).

```bash
# Detect and run
find . -path "*/integration*" -name "test_*" -o -name "*.test.*" 2>/dev/null | head -5
```

Run with the same framework as unit tests but targeting integration directory.

### Phase 5 — E2E Tests (L3 only)

Only if E2E tooling is configured.

| Tool | Detect By | Command |
|---|---|---|
| Playwright | `playwright.config.*` | `npx playwright test` |
| Cypress | `cypress.config.*` | `npx cypress run` |

Skip entirely if no E2E config found.

### Phase 6 — Regression Check (L2+)

Run the full test suite (not just changed files) to catch breakage.

```bash
# Same test runner as Phase 3, but without -x flag (run all)
pytest --tb=short    # or npx vitest run / npx jest
```

Compare pass count against any recorded baseline in the project.

### Phase 7 — Performance Check (L3 only)

Only if performance tooling exists.

| Tool | Detect By | Command |
|---|---|---|
| k6 | `k6` binary or `*.k6.js` files | `k6 run <script>` |
| Locust | `locustfile.py` | `locust --headless -t 30s` |
| autocannon | `autocannon` in package.json | `npx autocannon <endpoint>` |

Skip entirely if no performance tools configured.

### Phase 8 — Security Check (L3 only)

Run available security scanners.

| Tool | Detect By | Command |
|---|---|---|
| npm audit | `package-lock.json` | `npm audit --audit-level=critical` |
| pip-audit | Python project | `pip-audit` (if installed) |
| bandit | Python project | `bandit -r <src_dir> -ll` (if installed) |
| trivy | `trivy` binary | `trivy fs --severity CRITICAL .` |

Report findings but only fail on CRITICAL severity.

### Phase 9 — Code Quality Metrics (L2+)

Collect metrics if tools are available.

| Metric | Tool | Command |
|---|---|---|
| Test coverage | pytest-cov / c8 / istanbul | `pytest --cov` or `npx vitest run --coverage` |
| Complexity | radon / eslint-complexity | `radon cc <src> -a` or ESLint complexity rule |

**Thresholds**: Coverage >= 80% for new code. Complexity score reported (not blocking).

### Phase 10 — Smoke Test (ALWAYS for server projects)

Only if the project has a runnable server.

```bash
# Start server in background, wait, check health, kill
# Detect: Dockerfile, package.json "start" script, manage.py, app.py
```

Check: `GET /health` or `GET /` returns 2xx. If no server detected, skip.

## Worktree Awareness

If running in a worktree (isolated copy of the repo):
- Tests run safely against the worktree copy — no risk to working state
- **Reports MUST be written to the main repo's memory**, not the worktree:
  - Use absolute path: `$CLAUDE_PROJECT_DIR/.claude/memory/reports/verify/`
  - If `$CLAUDE_PROJECT_DIR` unavailable, find `.claude/memory/` relative to git root
- The worktree is auto-cleaned after completion — only memory/ files persist

## Step 4: Report Results

Write results to `/.claude/memory/reports/verify/VERIFY-<timestamp>.md`:

```markdown
# Verification Report
**Date**: [timestamp]
**Level**: L1/L2/L3
**Project Type**: [detected]
**Trigger**: [task/plan that was verified]

## Results Summary
| Phase | Status | Details |
|-------|--------|---------|
| 1. Build | PASS/FAIL/SKIP | [details] |
| 2. Static Analysis | PASS/FAIL/SKIP | [details] |
| ... | ... | ... |

## Overall: PASS / FAIL

## Failures (if any)
[Phase, error output, suggested fix]

## Recommendations
[Improvements, missing tooling suggestions]
```

## Step 5: Return to PM

```markdown
**VERIFY REPORT TO PM**
From: @tester via /verify
Level: L1/L2/L3
Result: PASS / FAIL

## Summary
[1-3 lines: what passed, what failed]

## Blocking Issues
[Must fix before continuing]

## Warnings
[Non-blocking observations]
```

If FAIL: the agent that produced the code must fix issues and /verify must run again.

## Task
$ARGUMENTS
