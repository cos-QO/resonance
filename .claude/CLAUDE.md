# Claude Code Architecture

## Routing

### Direct execution (no PM needed)
- Single-file edits, typo fixes, small refactors
- Git operations (commit, status, diff, branch)
- Running existing tests
- Reading/explaining code
- Simple questions about the codebase
- File organization and cleanup

### PM-coordinated (invoke PM agent first)
- Multi-file features or architectural changes
- New feature implementation requiring planning
- Architecture decisions and system design
- Multi-agent workflows (3+ agents)
- Project initialization or full codebase analysis
- Anything requiring discovery, planning, and multiple execution steps

### Auto-triggered skills
Skills auto-invoke based on context — no manual routing needed:
- Error reports / debugging → `debug` skill → troubleshooter agent
- "Research X" → `research` skill → researcher agent
- Project descriptions → `planning` skill → PM agent
- Code review requests → `review` skill → reviewer agent
- Unfamiliar codebase → `scope` skill → researcher agent
- Ambiguous/creative requests → `brainstorm` skill → PM agent (design before plan)

## Quality Gates

```yaml
mandatory_pairings:
  developer_invoked: [developer, tester]  # ALWAYS — no exceptions

keyword_triggers:
  security: [auth, password, token, encryption, session, admin, payment] → add security agent
  api_docs: [API, endpoint, REST, GraphQL] → add documenter agent
  production: [production, release, deploy, critical] → add reviewer agent
  architecture: [system, architecture, design, infrastructure] → prepend architect agent
```

## Agent Reference

| Agent | Role | Model |
|---|---|---|
| `pm` | Strategic coordinator, planning, delegation | opus |
| `developer` | Full-stack implementation, DevOps | sonnet |
| `tester` | QA, test automation, CI/CD | sonnet |
| `security` | Vulnerability scanning, threat modeling | sonnet |
| `reviewer` | Code quality, standards, performance | sonnet |
| `troubleshooter` | Error investigation, root cause analysis | sonnet |
| `mini-troubleshooter` | Fast data gathering for investigations | haiku |
| `watchdog` | Progressive quality validation (L1/L2/L3) | haiku |
| `documenter` | Technical writing, API docs, knowledge | sonnet |
| `architect` | System design, technology decisions | opus |
| `researcher` | Web research, library evaluation | opus |
| `ux-designer` | Interface design, user flows, accessibility | sonnet |
| `data` | ML/AI, data engineering, DB optimization | sonnet |
| `skill-creator` | Designs project-specific skills from patterns | opus |
| `trainer` | Autonomous skill/rule/agent improvement loop (autoresearch-inspired) | sonnet |

## Execution Orchestration (Enforced by Hooks)

### How agent chains work
1. **PM creates** a TODO + execution tracker (`.claude/memory/active/execution-tracker.json`)
2. **SubagentStop hook on PM** validates both files exist — warns if missing
3. **You (Main Claude) read** the tracker to determine phase order and agent assignments
4. **SubagentStart hook** injects each agent's tasks and previous agent outputs automatically
5. **SubagentStop hook** marks progress, identifies next agents, suggests parallel opportunities
6. **After each phase**: run `/commit` as a checkpoint before continuing

### Executing the chain
```yaml
step_1: Read .claude/memory/active/execution-tracker.json
step_1b: Create native tasks from tracker for terminal UI (Ctrl+T):
         - For each task in tracker → TaskCreate(subject: "[Phase N] task title", status: "pending")
         - Set dependencies via TaskUpdate(addBlockedBy) to mirror phase depends_on
         - Skip if tasks already exist for this plan_id
step_2: Find phases with status "pending" whose depends_on are all "completed"
step_3: For each task, check fields:
         - "skill" → use Skill tool (e.g., /python-dev, /verify L2) instead of Agent tool
         - "skill_args" → pass as skill arguments
         - "isolation": "worktree" → use Agent(isolation="worktree") for safe execution
         - If no skill → use Agent tool directly (e.g., Agent(developer, "..."))
step_4: If multiple phases ready AND marked parallel → invoke in SAME message
step_5: If single phase ready → invoke agent(s) sequentially
step_6: After agent completes:
         - TaskUpdate(taskId, status: "completed") for finished tasks
         - TaskUpdate(next_taskId, status: "in_progress") for next task
         - Run /commit as checkpoint (auto-detects plan context, includes next-steps)
step_7: Repeat until all phases completed
```

### Native Task UI (Terminal Checkboxes)
Native tasks (`TaskCreate`/`TaskUpdate`) provide interactive checkboxes visible via `Ctrl+T` in the terminal. They run **alongside** the file-based tracker, not replacing it.

- **When**: Create all native tasks after reading the tracker (step_1b), before first agent invocation
- **Format**: `[Phase N] Task title` for visual grouping by phase
- **Authority**: The execution tracker remains authoritative for orchestration; native tasks are best-effort UI
- **Skip for direct execution**: Don't create native tasks for simple edits routed without PM

### Parallel execution
When the tracker shows multiple phases with `"parallel": true` and satisfied dependencies, launch them simultaneously:
```
Agent(security, "Phase 3: Security audit of auth implementation...")
Agent(documenter, "Phase 4: Write API documentation for auth endpoints...")
```

### Agent handoff
When an agent produces output files, record them in the tracker's `handoff_files` field. The SubagentStart hook injects these paths into the next agent's context so it knows what to read first.

## Agent Collaboration Patterns

```yaml
standard_development: [architect, developer, tester, reviewer, documenter]
security_critical: [architect, developer, tester, security, reviewer, documenter]
error_investigation: developer error → troubleshooter (spawns team) → developer fixes
parallel_example: [security + documenter] in parallel after [developer + tester] sequential
design_to_execution: brainstorm → PM creates plan → agents execute
```

## Memory System

### Shared Project Memory (`.claude/memory/`)
- **Standards** (authoritative): `standards/` — consult before ALL decisions
- **Active work**: `active/` — current plans, tasks, TODOs, skill drafts
- **Discovery**: `discovery/` — research findings, analysis
- **Reports**: `reports/` — verify, skill-eval, heartbeat, errors
- **Archive**: `archive/` — completed work reference

### Agent-Specific Memory (`.claude/agent-memory/<name>/`)
PM, developer, and tester have persistent cross-session memory. Auto-loaded on start. Agents update after each task with learnings, patterns, and preferences.

**Rules**: Memory takes precedence over assumptions. Always read standards before starting work. Update memory with new learnings.

## TODO + Tracker System (Hook-Enforced)
- PM creates **both**: TODO file + `execution-tracker.json` (validated by SubagentStop hook)
- TODO format: phases with titles, tasks with descriptions, agents assigned per task
- Tracker: JSON with phase dependencies, parallel flags, completion status
- Agents receive their tasks automatically via SubagentStart hook injection
- After each phase: `/commit` to checkpoint progress
- Tracker location: `.claude/memory/active/execution-tracker.json`

## Developer Specialization Skills
PM routes developer through domain-specific skills for focused context:
- `/python-dev`, `/typescript-dev`, `/react-dev`, `/swift-dev` — language/framework specialization (swift-dev covers Swift 5.9+, SwiftUI, SwiftPM, XCTest, macOS)
- `/api-dev`, `/db-dev`, `/devops-dev` — domain specialization
- Each skill primes developer with patterns + Context7 MCP for live docs

## MCP Servers
- **Context7**: Live framework documentation (auto-queried by specialization skills)
- **Figma**: Design file access via Figma Developer MCP (requires `FIGMA_API_KEY` env var)

## Rules (auto-loaded)
- @.claude/rules/guardrails.md
- @.claude/rules/file-organization.md
- @.claude/rules/memory-protocol.md
- Path-specific: security.md, frontend.md, api.md, testing.md

## cc-pipeline (delivery pipeline plugin)
Lives at `.claude/cc-pipeline/`. Loaded automatically for all pipeline and delivery work.

**Rules (auto-loaded when Linear project present):**
- @.claude/cc-pipeline/rules/pd-guardrail.md — blocks execution without approved plan
- @.claude/cc-pipeline/rules/pd-linear-sync.md — enforces Linear updates at phase transitions
- @.claude/cc-pipeline/rules/pd-issue-standard.md — validates issue fields before planning

**Commands:** `/pd-start`, `/pd-scope`, `/pd-plan`, `/pd-pep`, `/pd-report`, `/pd-status`

**Skills:** `pd-linear-scope`, `pd-context-pack`, `pd-pep`, `pd-plan-post`, `pd-report-post`, `pd-github-pr`

**cc-qo-skills** (execution skills — install separately):
Expected at `.claude/cc-qo-skills/`. Provides `connectui-dev`, `verify`, `qo-pr`, `qo-prototype`.
See `.claude/cc-qo-skills/README.md` for installation instructions.

## System Capabilities

### Quality Pipeline
- `/verify L1|L2|L3` — automated build, test, lint, security checks (worktree-isolated)
- `/review` — human-judgment code review by reviewer agent
- `Stop` agent hook — haiku verifier checks tracker/TODO consistency after every response

### Codex Integration (OpenAI)
Codex is available as a second-opinion engine via the `codex-plugin-cc` plugin (user-scoped, always available).

| Command | When to use |
|---|---|
| `/codex:review` | Get Codex code review on git diffs — use alongside `/verify` for dual-model coverage |
| `/codex:adversarial-review` | Challenge design decisions, find edge cases before shipping |
| `/codex:rescue <task>` | Delegate complex debugging/analysis to Codex when stuck |
| `/codex:status` / `/codex:result` | Track and retrieve background Codex jobs |

**Agent usage guidelines:**
- **troubleshooter**: Use `/codex:rescue` for a second opinion on complex bugs
- **reviewer**: Use `/codex:review` alongside native review for dual-model validation
- **PM**: Can include `/codex:review` as a quality gate phase in execution plans
- Codex sends git diffs to OpenAI — do not use on repos with secrets in diffs
- Prefer `--readonly` flag when analysis-only (no file modifications needed)

### Skill Lifecycle
- `/create-skill design|discover|optimize` — creates project-specific skills (staged in memory/)
- `/skill-eval <name>|all|benchmark|optimize` — evaluates skill triggering and value
- `/train <target>|discover|all-skills` — autonomous improvement loop for skills/agents/rules (autoresearch-inspired)
- `/heartbeat quick|full|schedule` — system health monitoring and maintenance

### Scheduling (session-scoped)
- `/heartbeat schedule` — sets up recurring cron jobs for health monitoring
- Manual: `CronCreate("23 */1 * * *", "/heartbeat quick")` for custom schedules
- Cron jobs are session-only, auto-expire after 3 days

### Plugin Distribution
- Setup packaged as plugin at `.claude/.claude-plugin/`
- Install on new project: `claude --plugin-dir <path-to-claude-dir>`
- After install: run `/setup` to fix paths, validate MCP, check hooks
- Then: `/prepare` to analyze project and populate standards
- Includes: all agents, skills, rules, hooks, MCP config

## Troubleshooting
- **Post-install issues**: `/setup check` to diagnose, `/setup fix` to repair
- **Hook permission fix**: `python3 .claude/scripts/hooks-permission.py`

## LLM Integration (new projects)
- Primary: OpenRouter (model diversity, cost optimization)
- Models: Claude Sonnet, GPT-4o, GPT-4o-mini via OpenRouter
- Focus: Smart automation with centralized prompt management

