---
name: create-skill
description: Create project-specific skills. Analyzes patterns and designs custom SKILL.md files. Use when you need a new skill, want to discover automation opportunities, or see repeated workflows that should be automated.
argument-hint: ["design <description>" | "discover" | "optimize"]
context: fork
agent: skill-creator
disable-model-invocation: true
---
# /create-skill — Project Skill Creator

Create, discover, or optimize project-specific skills.

## Commands

### `/create-skill design <description>`
Design a specific skill based on your description.
Example: `/create-skill design a pre-commit linting check that runs eslint, prettier, and tsc`

### `/create-skill discover`
Analyze the project for repetitive patterns and suggest skills to create.
Scans: git history, TODOs, project scripts, CI/CD config, test patterns.

### `/create-skill optimize`
Review existing project-specific skills and suggest improvements.

## How It Works
1. Skill-creator agent analyzes your request and project context
2. Designs well-formed SKILL.md following established conventions
3. Stages drafts in `/.claude/memory/active/skill-drafts/`
4. Reports back with installation instructions
5. You review and approve — Main Claude installs to `/.claude/skills/`

## After Installation
Run `/skill-eval <new-skill-name>` to validate trigger accuracy and quality.

## Task
$ARGUMENTS
