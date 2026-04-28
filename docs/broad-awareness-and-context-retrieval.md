# Broad Awareness and Context Retrieval

## Definition

Broad awareness means the agent should not reason from the current issue alone.

For non-trivial work, the agent should gather relevant context across:

- the current issue
- the parent project
- linked documents
- comments and blockers
- related issues in adjacent teams
- recently completed relevant issues
- externally linked resources

## Why Broad Awareness Is Required

Many tickets look local but are not local.

A frontend or design task may still depend on:

- backend or API behavior
- analytics events
- infrastructure or rollout constraints
- content or brand dependencies
- data model assumptions

Without cross-team awareness, agents produce brittle plans.

## Broad Awareness Scope

Broad awareness should span all relevant team projects, not just the team that owns the current issue.

Likely relevant teams include:

- Product Design
- Engineering
- Frontend Org
- Integrations
- DevOps
- Data/Analytics
- Brand
- Marketing

The exact set should be narrowed by issue type, project, labels, and known dependencies.

## Context Pack

Before drafting a plan, the agent should generate a context pack with:

- issue summary
- project summary
- linked document summary
- related issue references
- adjacent team impact notes
- blockers and unknowns
- assumptions
- confidence level
- recommended reviewers

## Impact Map

The context pass should produce an impact map covering:

- upstream dependencies
- downstream consumers
- related teams
- risks
- unknowns
- review recommendations

## Retrieval Quality Requirement

Broad awareness only works if teams write issues and documents consistently.

That means templates should capture:

- outcome
- scope
- dependencies
- systems involved
- acceptance criteria
- success metrics
- references

## Practical Rule

For any task above a simple threshold, the agent should:

1. inspect the current issue
2. inspect the parent project
3. inspect linked docs and comments
4. inspect related issues in adjacent teams
5. produce a context pack before drafting the plan

## Main Risk

If retrieval is too broad, the agent gets noise instead of awareness.

The broad-awareness layer must rank and filter results instead of dumping everything into context.
