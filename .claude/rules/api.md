---
paths:
  - "src/api/**"
  - "**/routes/**"
  - "**/controllers/**"
  - "**/endpoints/**"
  - "**/*.router.*"
---
# API Rules

## REST Conventions
- Use HTTP methods correctly (GET=read, POST=create, PUT=replace, PATCH=update, DELETE=remove)
- Consistent URL patterns (/resources, /resources/:id)
- API versioning via URL prefix (/api/v1/)
- Pagination for list endpoints

## Error Handling
- Consistent error response format: `{ error: { code, message, details? } }`
- Appropriate HTTP status codes (400 client, 500 server)
- Never expose stack traces or internal details in production

## Validation
- Input validation with schema library (Zod, Joi)
- Validate at controller/route handler level
- Type-safe request/response with TypeScript

## Performance
- Database queries: avoid N+1, use joins/includes
- Pagination: cursor-based for large datasets
- Caching headers for GET endpoints where appropriate
