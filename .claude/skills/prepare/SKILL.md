---
name: prepare
description: Analyze existing project and populate Claude memory with conventions, patterns, tech stack, and structure. Use when starting work on a new or unfamiliar codebase, or when user says prepare, analyze project, or setup.
argument-hint: [focus-area]
model: opus
context: fork
agent: pm
disable-model-invocation: true
---
# /prepare — Project Analysis & Memory Setup

Analyze an existing project and populate `.claude/memory/standards/` with discovered patterns.

## Workflow
1. Scan project structure (package.json, config files, directory layout)
2. Detect tech stack, frameworks, and tools
3. Analyze coding conventions (formatting, naming, patterns)
4. Create/update standards files:
   - `conventions.md` — Coding patterns and style
   - `stack.md` — Technology stack details
   - `tree.md` — File structure map
   - `folder-structure.md` — Organization rules
   - `security-standards.md` — Security patterns (if applicable)
   - `database.md` — Database patterns (if applicable)
5. Validate agent readiness

## Arguments
- `$ARGUMENTS` — Optional focus area (frontend, backend, database, docs, llm)
