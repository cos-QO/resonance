# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

---

# Project Context

This repository is the design and specification home for a **supervised agentic delivery pipeline** — a structured process for moving work from idea to shipped implementation using Linear, Claude Code (or Cursor), and GitHub.

The project is currently in **design/discovery phase**. There is no application source code yet — the deliverables are structured documentation, workflow definitions, and the Claude Code multi-agent system that will eventually execute the pipeline.

**Linear project (official planning & documentation):** [Cross-Team Agentic Delivery](https://linear.app/queen-one/project/cross-team-agentic-delivery-f191c3f28ffa/overview) — shared project; treat it as the source of truth for intent, decisions, and status.

Key design decisions and architecture docs live in `docs/`. Read `docs/project-overview.md` and `docs/system-architecture.md` first when orienting to the project.

## Three-Plane Architecture

| Plane | Tool | Responsibility |
|---|---|---|
| Intent & approval | Linear | Issues, PRDs, ownership, approval state, final reports |
| Execution | Claude Code / Cursor | Planning, context packs, implementation, verification |
| Enforcement | GitHub | PR review, CI, merge restrictions, deploy gates |

The operating rule: **Linear defines the work → agent executes → GitHub enforces merge quality**.

## Workflow (14 steps)

1. Create/refine a Linear project document
2. Create an execution issue from a structured template
3. Agent gathers broad awareness context from Linear (cross-team, not just the current issue)
4. Generate a context pack (issue summary, impact map, assumptions, confidence)
5. Draft implementation plan
6. **Human approves plan** ← first mandatory gate
7. Execute in Claude Code or Cursor
8. Run tests and verification
9. Open GitHub PR linked to Linear issue
10. **Human PR review** ← second mandatory gate
11. Merge
12. Deploy (with human approval if protected environment)
13. Agent posts execution report to Linear
14. Close issue / update project state

## Human Gates

Mandatory: plan approval, PR review, deployment approval for protected environments.
The plan gate is the critical one — by PR time, architecture and assumptions have already solidified.

---

# Environment Setup

## Hook dependencies (Python)

```bash
pip install -r requirements.txt
python3 .claude/scripts/hooks-permission.py   # fix hook execute permissions after clone
```

## MCP servers

Configured in `.mcp.json`:
- **linear** — query Linear issues, projects, and docs via `mcp__linear__*` tools
- **context7** — live library/framework documentation
- **figma** — design file access (requires `FIGMA_API_KEY` env var)
