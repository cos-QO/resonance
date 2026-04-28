---
name: init-extend
description: After /init, inject the agentic system brief into root CLAUDE.md so agents know to check .claude/CLAUDE.md for full architecture.
allowed-tools: Bash, Read, Edit, Write
disable-model-invocation: true
---
# /init-extend — Restore Agentic Brief in CLAUDE.md

After running `/init`, the root `CLAUDE.md` gets overwritten with project-specific content. This skill injects a brief agentic system overview at the top, pointing agents to `.claude/CLAUDE.md` for full architecture details.

## Why this exists
- `.claude/CLAUDE.md` has the full architecture (routing, orchestration, memory, hooks, etc.)
- Root `CLAUDE.md` is what `/init` generates — project-specific content
- Agents need a breadcrumb in root `CLAUDE.md` to know the agentic system exists and where to find details
- Both files are loaded by Claude Code, but the brief ensures agents always see the pointer

## Workflow

1. **Read** the agentic brief template (embedded below)
2. **Read** root `CLAUDE.md` (project content from /init)
3. **Check idempotency**: If `<!-- AGENTIC:START -->` marker already exists, replace only that block
4. **Merge**: Prepend the agentic brief at the top, then a `---` separator, then the project content
5. **Write** the combined result back to root `CLAUDE.md`
6. **Confirm** to user with line counts

## Agentic Brief Template

```markdown
<!-- AGENTIC:START -->
# Multi-Agent System

This project uses a multi-agent orchestration system. Full architecture is in `.claude/CLAUDE.md` — **read it before any complex task**.

## Quick Reference

- **15 agents** — PM (opus) coordinates; developer, tester, security, reviewer, etc. execute
- **32 skills** — auto-triggered (`/debug`, `/research`, `/planning`) and manual (`/verify`, `/commit`, `/train`)
- **7 rules** — guardrails, memory-protocol, file-organization + path-specific (security, testing, api, frontend)
- **12 hook scripts** — enforce quality gates, track execution, sync TODOs automatically

## Routing

| Request type | What happens |
|---|---|
| Simple (edit, git, test) | Execute directly — no overhead |
| Complex (multi-file, feature) | PM agent plans → agent chain executes → hooks enforce quality |
| Auto-detected | Skills trigger automatically: errors→`/debug`, reviews→`/review`, research→`/research` |

## Key Files

| File | Purpose |
|---|---|
| `.claude/CLAUDE.md` | **Full architecture** — routing, orchestration, memory system, all details |
| `.claude/agents/*.md` | Agent definitions (15 agents) |
| `.claude/skills/*/SKILL.md` | Skill definitions (32 skills) |
| `.claude/rules/*.md` | Auto-loaded rules (7 rules) |
| `.claude/hooks/*.py` | Hook automation scripts |
| `.claude/memory/` | Shared project memory (standards, plans, reports) |
| `.claude/agent-memory/` | Per-agent persistent memory (PM, developer, tester) |
| `.claude/settings.json` | Permissions and hook configuration |

## Essential Rules

1. **Developer always paired with tester** — no exceptions
2. **Memory before assumptions** — check `.claude/memory/standards/` before decisions
3. **PM plans, agents execute** — PM never implements directly
4. **Hooks enforce quality** — don't bypass; they track execution and validate output
<!-- AGENTIC:END -->
```

## Rules
- If `<!-- AGENTIC:START -->` exists in root CLAUDE.md, replace only that block (idempotent)
- If not, prepend the brief + `---` separator before existing content
- Never modify `.claude/CLAUDE.md` — it's the full source of truth
- Safe to run multiple times

## Implementation Steps
```
1. brief = the agentic brief template above
2. root_content = read CLAUDE.md
3. if root_content contains "<!-- AGENTIC:START -->":
     replace everything between AGENTIC:START and AGENTIC:END (inclusive) with brief
   else:
     combined = brief + "\n\n---\n\n" + root_content
4. write combined to CLAUDE.md
5. print "Agentic brief injected: agents will now check .claude/CLAUDE.md for full architecture"
```
