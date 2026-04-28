# Claude Code Orchestration System (v3.2)

Multi-agent development environment with PM coordination, automated quality pipelines, and persistent agent memory.

## Components

| Component | Count | Location |
|-----------|-------|----------|
| Agents | 14 | `agents/*.md` |
| Skills | 24 | `skills/*/SKILL.md` |
| Rules | 7 | `rules/*.md` |
| Hooks | 8 scripts, 7 events | `hooks/*.py` |
| Agent memories | 3 | `agent-memory/` (pm, developer, tester) |
| MCP servers | 2 | Context7, Chrome DevTools |

## How It Works

```
User Request
    ├── Simple → Main Claude executes directly
    └── Complex → PM agent → TODO + execution tracker
                              → Main Claude reads tracker
                              → Runs agent chain (phase by phase)
                              → /commit checkpoint after each phase
```

**Routing**: Simple tasks (edits, git, tests) run directly. Complex tasks (multi-file, multi-agent) go through PM for planning and delegation.

**Quality gates**: Developer always paired with tester. Security keywords add security agent. Every plan includes documenter.

**Skill routing**: PM sets `"skill": "python-dev"` in tracker → Main Claude invokes `/python-dev` instead of raw `Agent(developer)`.

## Key Directories

```
.claude/
├── agents/           # 15 agent definitions (frontmatter + prompt)
├── skills/           # 32 skills (auto-invoke + manual)
├── rules/            # 7 rules (3 global + 4 path-specific)
├── hooks/            # 12 hook scripts for automation
├── memory/           # Shared project memory
│   ├── standards/    # Project conventions (read before work)
│   ├── templates/    # Plan, TODO, report templates
│   ├── active/       # Runtime: execution tracker, skill drafts
│   └── reports/      # Output from verify, heartbeat, skill-eval
├── agent-memory/     # Persistent per-agent memory (pm, dev, tester)
├── .claude-plugin/   # Plugin manifest for portable installation
└── settings.json     # Permissions, hooks, environment
```

## Plugin Installation

Install on any project:
```bash
claude --plugin-dir <path-to-this-claude-dir>
```

## Architecture Details

See `CLAUDE.md` for complete architecture, agent reference, execution orchestration, and memory system documentation.
