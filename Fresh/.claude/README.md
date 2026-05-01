# `.claude` Setup

This project uses Claude Code's standard project structure.

## Structure

- `.claude/settings.json`
  Shared project settings
- `.claude/commands/`
  Project slash commands
- `.claude/agents/`
  Project subagents
- `.claude/memory/`
  Shared project memory and standards
- `.claude/rules/`
  Shared project rules

## Relevant Claude Code conventions

Based on Anthropic's Claude Code docs:

- `CLAUDE.md` at the repo root is the official project memory file and is auto-loaded
- `.claude/settings.json` is the official shared project settings file
- `.claude/commands/` contains project-specific slash commands
- `.claude/agents/` contains project subagents with YAML frontmatter
- hooks belong in settings configuration, not as an ad hoc parallel system

## What this project keeps

- standards and memory for Queen One UI work
- small command surface for supervised UI implementation
- three focused subagents for analysis, build, and QA

## What this project no longer centers

- a large standalone runtime
- a dedicated dashboard UI
- broad PM-led multi-agent orchestration by default
