---
paths:
  - "**/auth/**"
  - "**/api/**"
  - "**/middleware/**"
  - "**/*payment*"
  - "**/*session*"
  - "**/*token*"
  - "**/*crypto*"
---
# Security Rules

## Authentication & Authorization
- Passwords: bcrypt or Argon2 only (never MD5/SHA for passwords)
- JWT: short expiry, refresh token rotation, secure storage
- Sessions: httpOnly, secure, sameSite cookies
- Always validate authorization on server side (never trust client)

## Input Validation
- Validate ALL user input at system boundaries
- SQL: parameterized queries only (never string concatenation)
- XSS: sanitize output, use framework escaping
- CSRF: tokens for all state-changing operations

## API Security
- Rate limiting on authentication endpoints
- Input validation with schema (Zod, Joi, etc.)
- Consistent error responses (don't leak internals)
- CORS: restrict to known origins

## Risk-Based Review
- HIGH: auth, payments, admin → comprehensive threat modeling
- MEDIUM: user data, API endpoints → standard security checklist
- LOW: static content, read-only → basic pattern verification

## Agent → Security Handoff
When these patterns appear, Security agent must be involved:
- Authentication/authorization implementation
- Database queries (SQL injection prevention)
- File upload functionality
- Cryptographic operations
- Session management
- Third-party integrations with sensitive data

Other agents discovering security issues should escalate immediately:
- Tester: report vulnerabilities found during testing
- Reviewer: escalate security concerns beyond basic patterns
- Developer: delegate security review after implementing auth/payments
