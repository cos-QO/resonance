---
name: python-dev
description: Python language specialization — type hints, async/await, PEP 8, pytest, virtual environments. Use for Python-specific implementation. For API design patterns use /api-dev, for database work use /db-dev. Routed by PM or invoked directly for Python tasks.
context: fork
agent: developer
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, mcp__context7__resolve-library-id, mcp__context7__get-library-docs
---
# Python Development Mode

You are now in **Python specialization mode**. Before writing any code:

## 1. Load Project Conventions
```bash
Read /.claude/memory/standards/conventions.md
```

## 2. Query Context7 for Latest Docs
Based on the task, query relevant library documentation:
- **FastAPI/Flask**: `mcp__context7__get-library-docs` for endpoint patterns, middleware, dependency injection
- **SQLAlchemy/Alembic**: For ORM patterns, migrations, query optimization
- **pytest**: For testing patterns, fixtures, parametrize
- **Pydantic**: For validation schemas, serialization

## 3. Python Standards
- Use type hints on all function signatures
- Use `async/await` for I/O-bound operations
- Follow PEP 8 naming (snake_case functions, PascalCase classes)
- Use dataclasses or Pydantic models for structured data
- Prefer `pathlib` over `os.path`
- Use context managers for resource handling
- Virtual environments with `requirements.txt` or `pyproject.toml`

## 4. Security (Python-Specific)
- Parameterized queries only (no f-string SQL)
- Use `secrets` module for token generation (not `random`)
- Sanitize all user input before processing
- Use `bcrypt` or `argon2` for password hashing
- Never use `eval()`, `exec()`, or `pickle` on untrusted data

## 5. Testing
- pytest as default framework
- Fixtures for test setup/teardown
- `pytest-cov` for coverage reporting
- Mock external dependencies with `unittest.mock` or `pytest-mock`

## Task
$ARGUMENTS
