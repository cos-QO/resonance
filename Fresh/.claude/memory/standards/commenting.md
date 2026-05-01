# Commenting & Documentation

**Status**: Ready for analysis
**Last Updated**: Not analyzed yet
**Analyzed by**: `/prepare` command

> ⚠️ Stub file. Populated by `/prepare` in each target project — do not edit in cc-ready source.

## Auto-Analysis Process

When `/prepare` runs, it will:
1. Detect the project's documentation style (docstrings, JSDoc, DocC, etc.)
2. Identify where comments are used heavily vs. sparingly
3. Document conventions for inline comments, function docs, and module headers
4. Populate the sections below

## Sections `/prepare` Will Populate

### Inline Comments
- When to comment (non-obvious logic, constraints, workarounds)
- When NOT to comment (restating what the code obviously does)

### Function / API Documentation
- Docstring format (Google, NumPy, JSDoc, DocC, etc.)
- Required fields (parameters, returns, raises/throws, examples)

### Module & File Headers
- Whether file-level doc blocks are expected
- Required metadata (author, license, etc. — usually none)

### TODO / FIXME Conventions
- Format, ownership, tracking
