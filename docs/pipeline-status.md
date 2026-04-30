# Resonance Pipeline — Current State & Roadmap

*Last updated: 2026-04-30 (session 3)*

---

## What we have

Resonance is a supervised agentic delivery pipeline. A human writes a product brief, Resonance decomposes it into an executable plan, and Claude Code agents implement each piece of work in isolated git worktrees — with humans approving at every gate.

### The full flow (implemented)

```
[PEP] issue (pep label) → Plan Approved
         ↓  PEP Reader Agent (claude-opus)
         ↓  reads PEP + comments, creates Core Plan issue
Core Plan issue (core-plan label) → Human Review → Plan Approved
         ↓  Block Decomposer Agent
         ↓  reads Core Plan, creates Block sub-issues, sets dependencies
Block issues (block label) → Plan Approved
         ↓  Block Execution Agent (claude-sonnet)
         ↓  implements tasks, checks off boxes, commits, opens PR
         ↓  signals ready_for_review
Human Review → Done
```

### Components

| Component | Status | Notes |
|---|---|---|
| Orchestrator (`orchestrator/`) | ✅ Working | Polls Linear every 15s, manages run lifecycle |
| PEP Reader Agent | ✅ Working | Creates Core Plan with correct project/parent/labels |
| Block Decomposer Agent | ✅ Working | Creates Block sub-issues, sets `Plan Approved` state |
| Block Execution Agent | ✅ Working | Implements tasks, checks off checklist, signals done |
| TUI dashboard (`tui/`) | ✅ Working | Shows active runs, Linear pipeline, event stream |
| `wizard.sh` | ✅ Working | Setup, check (8 steps, auto-fix), test (4 live checks) |
| `resonance doctor` | ✅ Working | Health check + readiness report |
| Linear MCP in workers | ✅ Fixed | Agents can create/update Linear issues from within worktree |
| Signal protocol | ✅ Working | `pep_decomposed`, `blocks_created`, `block_complete`, `human_input_needed`, `ready_for_review` |
| Human-in-the-loop plugin | ✅ Working | `/reso`, `/reso-takeover`, `/reso-handback` |
| ET timestamps in agent comments | ✅ Working | All agent-posted times use New York timezone (%-I:%M %p ET) |
| Auto-push to GitHub on block done | ✅ Working | `git push -u origin agent/<id>` when `GITHUB_TOKEN` is set |
| GitHub branch links in Linear comments | ✅ Working | Block Done + final "all blocks complete" comments include branch URLs |
| Haiku log agent (`RUNLOG.md`) | ✅ Working | Lightweight Haiku subprocess writes handoff log per block/plan run |
| Project-grouped workspaces | ✅ Working | `workspaces/{project-slug}/issues/{issue-id}` when project is scoped |

### What was built across sessions

**Session 2 — MCP fixes + wizard.sh**

| Bug | Root cause | Fix |
|---|---|---|
| Linear MCP auth failed in workers | `@linear/sdk` adds `Bearer` prefix to PATs; Linear now rejects it | Patched `linear-mcp/build/auth.js` to use `apiKey` (raw token, no Bearer) |
| MCP env vars not reaching server | Claude CLI doesn't expand `${VAR}` in MCP `env` fields | Removed `env` fields; `runner.py` injects `LINEAR_ACCESS_TOKEN` into subprocess env |
| Core Plan created without project/parent/labels | `linear_create_issue` MCP schema missing `projectId`, `parentId`, `stateId`, `labelIds` | Patched `tool.types.js` to expose all fields |
| `bulk_update_issues` call format wrong | Prompt used `ids`/flat `stateId`; tool expects `issueIds`/`update.stateId` | Fixed both `build_core_plan_prompt` and `build_planning_prompt` |
| Core Plan not in project after creation | Agent couldn't set `projectId` (schema gap) | Poller now patches `projectId` + `parentId` post-creation as safety net |
| `.env` multi-word values unquoted | `source .env` fails on `Plan Approved` | Values now properly quoted |
| `wizard.sh` missing (replaced `setup.sh`) | `setup.sh` was monolithic, no menu | `wizard.sh` with interactive menu + check + test commands |

**Session 3 — Post-demo improvements**

| Feature | What changed |
|---|---|
| ET timestamps | Agent comments now show `%-I:%M %p ET` (New York) instead of UTC |
| Auto-push to GitHub | `_finish_block_done` runs `git push -u origin agent/<id>` when `GITHUB_TOKEN` is set |
| GitHub branch links | Block Done comment and "all blocks complete" comment include branch URLs |
| Haiku log agent | `_spawn_log_agent()` spawns `claude-haiku` after each block/plan run; writes `RUNLOG.md` |
| Project-grouped workspaces | `WorkspaceManager` now groups worktrees as `workspaces/{project-slug}/issues/{id}` |
| Shared main/ workspace for blocks | All block agents now work in a single `main/` worktree (`$MAIN_PATH`); `issues/` folders hold per-block metadata (`$ISSUE_PATH`) |

### Verified working (live tests)

```
./wizard.sh test

[1/4]  Python Linear client        ✓  cos@queen.one (18 teams)
[2/4]  linear-mcp MCP server auth  ✓  cos@queen.one (no Bearer prefix)
[3/4]  Worker env injection         ✓  LINEAR_ACCESS_TOKEN in subprocess
       linear_create_issue schema   ✓  projectId/parentId/stateId/labelIds present
[4/4]  MCP config files             ✓  .mcp.json, cc-pipeline, settings.json clean
```

---

## Running a demo

### Prerequisites

```bash
./wizard.sh check     # must pass all 8 steps
./wizard.sh test      # must pass all 4 tests
./onair.sh            # start orchestrator + TUI
```

### Step 1 — Create a PEP

In Linear, inside the **D2D Demo-gorgon** project:

1. Create an issue with label `pep` and `RES`
2. Title: `[PEP] <your feature name>`
3. Description: use the PEP template (see `docs/pep-template.md`) or write a plain brief — the PEP Reader will structure it
4. Leave it in **Todo**

### Step 2 — Authorize the PEP

Move the PEP issue to **Plan Approved**.

Resonance picks it up within 15 seconds. In the TUI you'll see:
- `workspace ready`
- `worker started`
- `run started` with `task_type=pep`
- A stream of `Linear read/create/comment` events

### Step 3 — Review the Core Plan

Within 3–7 minutes, the PEP Reader finishes. It:
- Creates one Core Plan issue (label: `core-plan`, parent: PEP issue, project: D2D Demo-gorgon)
- Posts a summary comment on the PEP issue listing all plans and blocks
- Moves the PEP issue to **Done**
- Moves the Core Plan to **Human Review**

You'll see the Core Plan in Linear. Review it — edit any block titles, tasks, or acceptance criteria. When satisfied, move it to **Plan Approved**.

### Step 4 — Block Decomposer runs

Resonance picks up the Core Plan. The Block Decomposer:
- Creates one Block sub-issue per block
- Sets blocking relations (B2 blocked by B1 if sequential)
- Moves all blocks to **Plan Approved**
- Posts a summary comment on the Core Plan

### Step 5 — Blocks execute

Each Block Execution Agent:
- Implements tasks one by one
- Checks off task checkboxes in the Linear issue description as it goes
- Posts a comment per task: `✅ Task done: <name> · <elapsed>`
- Opens a PR on `agent/<issue-id>` branch
- Signals `ready_for_review`
- Linear moves block to **Human Review**

### Step 6 — Review and approve

Review the branch in your worktree. With a project scoped, all block agents work in the shared
worktree at `workspaces/<project-slug>/main/` (`$MAIN_PATH`). Per-block scratch data is stored
in `workspaces/<project-slug>/issues/<issue-id>/` (`$ISSUE_PATH`). The block Done comment
includes a direct GitHub branch link.

```bash
resonance attach RND-47    # prints exact worktree path + log file
```

Merge when satisfied. Move the block to **Done**. When all blocks are Done, the Core Plan moves to Human Review. Move that to Done when satisfied.

---

## What we want to do next

### Short term (next session)

| Item | Why | Notes |
|---|---|---|
| Validate block execution end-to-end | PEP → Core Plan → Blocks is working; need to confirm a Block agent actually commits real code | Requires a real implementation task |
| GitHub MCP for PR creation | Branch is auto-pushed; PR creation is still manual | `gh` CLI in worker, or `mcp__github__*` tools |
| MCP health indicators in TUI | Can't tell if Linear/Figma/GitHub MCP is reachable without running a test | Header-bar colored dots, background check every 2 min |

### Medium term

| Item | Why |
|---|---|
| Auto-patch `linear-mcp` on npm update | Auth patch lives in `node_modules`; `wizard.sh check` will re-apply it, but user needs to remember to run it |
| Block-level parallelism in TUI | Currently shows runs sequentially in event stream; parallel blocks need clearer visual grouping |
| Figma → Component prototype flow | `/qo-prototype` skill exists but hasn't been tested with the new MCP auth fix |
| PEP template interactive creator (`/create-pep`) | Currently humans write PEPs manually; skill-assisted creation reduces friction |

### Known limitations to work around

| Limitation | Workaround |
|---|---|
| `linear-mcp` schema patch lives in global npm install | Run `./wizard.sh check` after any `npm update`; patch is auto-applied |
| Workers can't update Linear issue state directly via MCP | Orchestrator handles state transitions; workers only create comments and sub-issues |
| Block execution happens sequentially per run slot | `WORKFLOW.md` `concurrency.max_parallel_runs` controls how many blocks run simultaneously across issues |
| No automated merge | Human reviews and merges PRs; Linear issue → Done triggers worktree cleanup |

---

## System health check

```bash
./wizard.sh check   # full 8-step diagnostic with auto-fix
./wizard.sh test    # quick 4-test live validation
resonance doctor    # credential + Linear state check
```

The `wizard.sh check` command auto-patches:
- `linear-mcp/build/auth.js` — Bearer prefix fix
- `linear-mcp/build/core/types/tool.types.js` — schema completeness
- `~/.claude/settings.json` — correct env key name
- `.mcp.json` — removes broken `${...}` env fields
