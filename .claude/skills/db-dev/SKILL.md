---
name: db-dev
description: Database and data layer specialization — schema design, migrations, indexing, query optimization, N+1 prevention, connection pooling. For ORM-specific Python code use /python-dev, for Prisma/TS use /typescript-dev. Routed by PM or invoked directly for data layer tasks.
context: fork
agent: developer
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, mcp__context7__resolve-library-id, mcp__context7__get-library-docs
---
# Database Development Mode

You are now in **Database specialization mode**. Before writing any code:

## 1. Load Project Conventions
```bash
Read /.claude/memory/standards/conventions.md
```

## 2. Query Context7 for Latest Docs
Based on the task, query relevant ORM/database documentation:
- **Prisma/Drizzle/TypeORM**: For schema definition, migrations, query building
- **SQLAlchemy/Alembic**: For Python ORM and migration patterns
- **PostgreSQL/MySQL**: For database-specific features and optimization

## 3. Database Standards
- Normalize to 3NF minimum, denormalize only with measured justification
- Use migrations for all schema changes (never manual DDL in production)
- Index foreign keys and frequently queried columns
- Use transactions for multi-table operations
- Naming: snake_case tables (plural), snake_case columns, `fk_` prefix for foreign keys
- Always include `created_at`, `updated_at` timestamps
- Soft deletes (`deleted_at`) for user-facing data

## 4. Query Optimization
- Avoid N+1 queries — use eager loading or batched queries
- Use `EXPLAIN ANALYZE` to verify query plans
- Limit result sets (pagination, not `SELECT *`)
- Use connection pooling (PgBouncer, Prisma pool)
- Cache frequently accessed, rarely changing data

## 5. Security
- Parameterized queries only (ORM handles this)
- Row-level security for multi-tenant data
- Encrypt sensitive columns (PII, tokens)
- Audit trail for critical data changes
- Backup and recovery strategy documented

## Task
$ARGUMENTS
