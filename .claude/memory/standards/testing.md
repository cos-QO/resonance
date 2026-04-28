# Testing Standards

**Status**: Ready for analysis
**Last Updated**: Not analyzed yet
**Analyzed by**: `/prepare` command

> ⚠️ Stub file. Populated by `/prepare` in each target project — do not edit in cc-ready source.

## Auto-Analysis Process

When `/prepare` runs, it will:
1. Detect the project's test framework(s) and runner
2. Map the test directory structure and naming conventions
3. Identify coverage tooling and thresholds
4. Populate the sections below

## Sections `/prepare` Will Populate

### Test Framework & Runner
- Primary framework (pytest, vitest, jest, XCTest, etc.)
- Test runner command (`npm test`, `pytest`, `swift test`, etc.)

### Test Organization
- Location (`tests/`, co-located, `__tests__/`, etc.)
- File and function naming patterns

### Test Types
- Unit, integration, end-to-end expectations
- When each type is required

### Coverage
- Minimum coverage thresholds
- Excluded paths (generated code, migrations, etc.)

### TDD Iron Law (applies to ALL projects)
All changes must follow RED → GREEN → REFACTOR:
1. **RED**: Write a failing test first
2. **GREEN**: Write the minimum code to pass the test
3. **REFACTOR**: Clean up while keeping tests green

See `.claude/rules/testing.md` for the full rationalization-rejection table.

---
*Project-specific fields populated automatically by the `/prepare` command. The TDD iron law above is universal and does not change per project.*
