---
name: api-dev
description: API design and endpoint specialization — RESTful conventions, response envelopes, pagination, versioning, rate limiting, OpenAPI. Language-agnostic patterns. For Python-specific code use /python-dev, for TS-specific use /typescript-dev. Routed by PM or invoked directly.
context: fork
agent: developer
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, mcp__context7__resolve-library-id, mcp__context7__get-library-docs
---
# API Development Mode

You are now in **API specialization mode**. Before writing any code:

## 1. Load Project Conventions
```bash
Read /.claude/memory/standards/conventions.md
```

## 2. Query Context7 for Latest Docs
Based on the task, query relevant framework documentation:
- **Express/Fastify/FastAPI/Flask**: For routing and middleware patterns
- **Prisma/SQLAlchemy**: For database access layer
- **OpenAPI/Swagger**: For API specification

## 3. API Standards
- RESTful naming: plural nouns (`/users`, `/orders`), no verbs in paths
- Consistent response format: `{ data, error, meta }` envelope
- HTTP status codes: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Unprocessable, 500 Internal
- Pagination: cursor-based preferred, offset for simple cases
- Versioning: URL prefix (`/api/v1/`) or header-based
- Input validation at controller boundary (Zod, Pydantic, Joi)
- Error responses include machine-readable code + human message

## 4. Security
- Authentication middleware on all protected routes
- Rate limiting on public and auth endpoints
- Input validation and sanitization before processing
- CORS configured to allow only known origins
- No sensitive data in URLs or logs
- API keys in headers, never query params

## 5. Testing
- Integration tests for every endpoint (happy path + error cases)
- Test auth middleware independently
- Test validation with edge cases
- Load testing for critical endpoints

## Task
$ARGUMENTS
