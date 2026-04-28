# Indexing and Knowledge Model

## Key Question

Should the system maintain a separate index page, or can Linear act as the index?

## Recommendation

Use Linear as the canonical navigational index, but add a thin LLM-oriented catalog on top of it.

Do not build a giant parallel wiki that humans and agents must keep in sync manually.

## What Linear Already Does Well

Linear already gives useful discovery surfaces:

- team and workspace project lists
- issue search and filters
- project views
- project documents
- references between issues, projects, and docs
- project resources

This is enough for humans to browse and for agents to query raw records.

## What Is Missing

Linear does not automatically maintain a compact agent-optimized map of:

- canonical project summaries
- system ownership boundaries
- reusable implementation patterns
- cross-team dependency maps
- project entry points for new agents

## Thin Context Catalog

The recommended addition is a thin derived catalog that contains routing metadata only.

Possible fields:

- project name
- owning teams
- short summary
- key systems touched
- canonical docs
- common dependency teams
- important labels or search patterns
- last validated date

## What The Catalog Is Not

The catalog is not:

- a replacement for Linear issues
- a replacement for project documents
- a full knowledge base
- a manually curated wiki for everything

It should stay small and help agents route quickly to the right sources.

## Location Options

### Option 1: Repo-local catalog

Pros:

- easy to version
- easy to shape for agents
- works well with Claude Code memory

Cons:

- can drift if not refreshed from Linear
- less visible to non-technical stakeholders

### Option 2: Linear document catalog

Pros:

- visible to everyone already using Linear
- lives near the canonical project data

Cons:

- less convenient for structured machine use
- can become verbose and hard to maintain

### Option 3: Dual-layer model

Use:

- Linear for canonical records
- a repo-local thin catalog for agent routing

This is the current best recommendation.

## Maintenance Rule

If a catalog exists, it should be refreshed from Linear on a schedule or during planning, not maintained by ad hoc manual edits alone.
