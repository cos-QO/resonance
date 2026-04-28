---
name: research
description: External technology research — comparing libraries, evaluating frameworks, best practices analysis, architecture options. Triggers when user needs to research technologies or gather information before making decisions. NOT for debugging errors (use /debug) or exploring existing code (use /scope).
argument-hint: [research-topic]
context: fork
agent: researcher
---
# /research — Research & Analysis

Conduct thorough research using web search and codebase analysis.

## Workflow
1. Understand research scope and questions
2. Gather information via web search, documentation, codebase analysis
3. Compare options with pros/cons analysis
4. Create comprehensive research report in `.claude/memory/discovery/`

## Deliverables
- Technology comparison matrix (if comparing options)
- Best practices summary
- Feasibility assessment
- Recommendations with rationale

## Arguments
- `$ARGUMENTS` — Research topic or questions to investigate
