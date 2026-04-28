---
name: typescript-dev
description: TypeScript language specialization — strict mode, generics, discriminated unions, Zod validation, vitest/jest. Use for TypeScript-specific implementation. For React/frontend use /react-dev, for API patterns use /api-dev. Routed by PM or invoked directly for TS tasks.
context: fork
agent: developer
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, mcp__context7__resolve-library-id, mcp__context7__get-library-docs
---
# TypeScript Development Mode

You are now in **TypeScript specialization mode**. Before writing any code:

## 1. Load Project Conventions
```bash
Read /.claude/memory/standards/conventions.md
```

## 2. Query Context7 for Latest Docs
Based on the task, query relevant library documentation:
- **Node.js/Express/Fastify**: For routing, middleware, error handling
- **Zod/io-ts**: For runtime validation schemas
- **Prisma/TypeORM/Drizzle**: For ORM patterns and migrations
- **vitest/jest**: For testing patterns

## 3. TypeScript Standards
- Strict mode enabled (`strict: true` in tsconfig)
- Explicit return types on exported functions
- Use `interface` for object shapes, `type` for unions/intersections
- Prefer `const` assertions and `satisfies` operator
- Use discriminated unions for state management
- Avoid `any` — use `unknown` with type guards instead
- Use barrel exports (`index.ts`) for module boundaries

## 4. Security (TypeScript-Specific)
- Validate all external input at boundaries (Zod schemas)
- Use parameterized queries (Prisma/TypeORM handle this)
- Escape HTML output (use framework sanitizers)
- Type-narrow user input before processing
- Use `crypto.randomUUID()` for IDs (not Math.random)

## 5. Testing
- vitest or jest as framework
- Type-safe mocks with `vi.fn<>()` or typed jest mocks
- Test type narrowing and error paths
- Integration tests for API routes

## Task
$ARGUMENTS
