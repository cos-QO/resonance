---
name: scope
description: Deep codebase discovery and structural analysis. Use when exploring unfamiliar code, onboarding to a new project, or assessing technical debt before major changes. NOT for researching external technologies (use /research) or reviewing code quality (use /review).
argument-hint: [area-to-investigate]
context: fork
agent: researcher
disable-model-invocation: true
---
# /scope — Codebase Discovery

Run a comprehensive investigation to understand a codebase area.

## Workflow
1. Researcher coordinates parallel investigation:
   - Codebase structure and dependency analysis
   - Architecture pattern identification
   - Test coverage gap assessment
   - Technical debt inventory
2. Synthesize findings into discovery report
3. Produce prioritized recommendations

## Output
- Discovery report in `.claude/memory/discovery/`
- Identified patterns, risks, and technical debt
- Recommendations for next steps

## Arguments
- `$ARGUMENTS` — Area, system, or codebase section to investigate
