# Architecture Standards

**Status**: Ready for analysis
**Last Updated**: Not analyzed yet
**Analyzed by**: `/prepare` command

> ⚠️ Stub file. Populated by `/prepare` in each target project — do not edit in cc-ready source.

## Auto-Analysis Process

When `/prepare` runs, it will:
1. Identify architectural patterns (monolith, modular monolith, microservices, event-driven)
2. Map service boundaries, module dependencies, and data flow
3. Document system components and integration points
4. Populate the sections below

## Sections `/prepare` Will Populate

### High-Level Architecture
- System pattern (monolith / microservices / serverless / hybrid)
- Primary components and their responsibilities

### Data Flow
- How requests flow through the system
- Storage patterns (write path, read path, caching)

### Integration Points
- External APIs, webhooks, third-party services
- Internal service-to-service communication

### Key Architectural Decisions
- Decisions made and their rationale (ADR-style)
- Constraints and non-goals
