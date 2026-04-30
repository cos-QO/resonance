"""
Post/update the Resonance overview document in the Cross-Team Agentic Delivery Linear project.

Usage:
  python3 scripts/post_linear_overview.py          # update existing doc; create if missing
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from orchestrator.linear_client import LinearClient

PROJECT_ID = "bb7f1966-7582-4550-9388-04cd2df8a41b"
DOCUMENT_TITLE = "Resonance — Pipeline Overview"

DOCUMENT_CONTENT = """\
# Resonance — Supervised Agentic Delivery

Resonance is a supervised agentic delivery pipeline built from scratch and designed for scale, multi-agent parallelism, and human-in-the-loop approval at every gate.

A human writes a product brief. Resonance decomposes it into an executable plan. Claude agents implement each piece of work in isolated git worktrees — with humans approving at every stage before any code is merged.

---

## How It Works

The pipeline moves through three tiers, each requiring explicit human approval before progressing:

```mermaid
flowchart TD
  P["📋 PEP Issue\\nlabel: pep"] --> PA1["✅ Human Gate 1\\nMove to Plan Approved"]
  PA1 --> PEP["🤖 PEP Reader Agent\\nclaude-opus · 3–7 min\\nDecomposes brief into structured Core Plan"]
  PEP --> CP["📄 Core Plan Issue\\nlabel: core-plan"]
  CP --> HR1["👀 Human Review\\nEdit titles, tasks, acceptance criteria"]
  HR1 --> PA2["✅ Human Gate 2\\nMove to Plan Approved"]
  PA2 --> BD["🤖 Block Decomposer\\nclaude-opus\\nCreates Block sub-issues with dependency ordering"]
  BD --> B1["⚙️ Block B1\\nExecution Agent · claude-sonnet"]
  BD --> B2["⚙️ Block B2\\nExecution Agent · claude-sonnet"]
  BD --> B3["⚙️ Block B3\\nExecution Agent · claude-sonnet"]
  B1 -->|"B2 blocked by B1"| B2
  B2 -->|"B3 blocked by B2"| B3
  B1 & B2 & B3 --> GH["🌿 GitHub\\nbranch agent/project-slug\\nPRs created automatically"]
  GH --> HR2["👀 Human Gate 3\\nReview · Merge · Done"]
```

---

## Three-Plane Architecture

| Plane | Tool | Role |
|---|---|---|
| **Intent & Approval** | Linear | Issues, plans, approval state, human review gates |
| **Execution** | Claude Code CLI | Planning, implementation in isolated git worktrees |
| **Enforcement** | GitHub | PR review, CI checks, merge restrictions |

**Operating rule:** Linear defines the work → Resonance executes in a worktree → human reviews before merge.

---

## Key Design Principles

**Supervised, not autonomous.** Every stage requires human approval before progressing. Agents cannot self-approve, skip gates, or merge without review.

**Isolated execution.** Each block runs in its own git worktree on a dedicated branch. No shared mutable state between concurrent agents. If an agent crashes or produces bad output, the worktree is discarded without affecting anything else.

**Signal protocol.** Agents communicate state transitions via structured `AGENT_SIGNAL` lines (`ready_for_review`, `human_input_needed`, `block_complete`), not free-form text. The orchestrator responds to signals — not polling logs.

**Human-in-the-loop at any point.** The `/reso-takeover` command pauses an agent mid-execution and hands the worktree to a human. `/reso-handback` resumes from there. Any comment posted on a Linear issue while an agent is working is injected into the agent's context on the next iteration.

**Dependency-aware scheduling.** Block dependencies are declared as Linear issue relations. The orchestrator enforces ordering — Block B2 won't start until B1 is in Done state, even across concurrent runs.

---

## Frontend Execution — Multi-Repo Workspace

Frontend and design-to-code tasks run inside the **connect-ui repository** rather than the Resonance repo. When `target_repo` is set to `connect-ui` in `WORKFLOW.md`, the orchestrator:

1. Resolves the connect-ui path from `CONNECT_UI_PATH` in `.env`
2. Creates a git worktree **inside connect-ui** at `workspaces/{project-slug}/issues/{issue_id}` on branch `agent/{issue_id}`
3. Writes `.claude/settings.json` into that worktree, pointing at the shared plugin dirs and MCP config
4. Injects `ISSUE_ID` and `TARGET_REPO=connect-ui` into the agent's environment

This means frontend agents work directly in the application codebase — no file copying or cross-repo patches.

### Firebase Read-Only Proxy Sidecar

Frontend tasks need live data to test against. When a task type specifies `sidecar: firebase-readonly-proxy`, the orchestrator auto-starts a lightweight HTTP proxy alongside the agent. The proxy:

- Intercepts all Firestore read operations and forwards them to the real Firebase project
- Blocks all write operations (returns `PERMISSION_DENIED`)
- Binds to `localhost:5174` so the Vite dev server can proxy through it without a real service account

The sidecar is terminated automatically when the agent finishes or is aborted.

### Design System Context Injection

Execution prompts for frontend tasks automatically include:

- **Existing code context** — files from `src/features/`, `src/components/`, `src/routes/`, `src/hooks/` that keyword-match the issue title and description (capped at 60 KB total). This lets agents see the real code they're editing, not just abstract instructions.
- **Design system reference** — `.claude/memory/standards/connectui-design-system.md` is symlinked into every worktree, giving agents access to the current Queen One color palette, typography variants, spacing scale, and Orion component list without re-fetching.

To refresh the design system reference after connect-ui changes:
```bash
python3 scripts/sync-design-system.py --local-path /path/to/connect-ui
```

---

## Scalability

Resonance is designed to scale across teams and projects:

- **Multi-project** — Each project gets its own isolated workspace. The orchestrator polls all active projects simultaneously.
- **Parallel blocks** — Multiple execution agents run concurrently in separate worktrees, bounded by `concurrency.max_parallel_runs` in the workflow config.
- **Pluggable workers** — Worker specialization is configured in `WORKFLOW.md` — add new task types (design-to-code, backend feature, infrastructure) without changing orchestrator code.
- **MCP integration** — Workers have access to Linear (issue management), Figma (design tokens), GitHub (PR creation), and Context7 (live documentation) via the Model Context Protocol.
- **Debug tracing** — Full observability: MCP call/response pairs, Linear API calls with timing, agent reasoning, and pipeline decisions are captured to `runs/traces/` and browsable in the TUI trace viewer.

---

## Entry Point — The PEP

The unit of work is a **PEP** (Product Execution Prompt) — a structured brief written in a Linear issue inside a `[PEP] Title` project:

1. Human writes a PEP and moves the issue to **Plan Approved** → Resonance picks it up within 15 seconds
2. **PEP Reader Agent** (claude-opus) reads the brief and decomposes it into a Core Plan issue with block/task breakdown
3. Human reviews and edits the Core Plan → moves to **Plan Approved**
4. **Block Decomposer** creates atomic Block sub-issues with dependency ordering → all set to Plan Approved
5. **Execution Agents** (claude-sonnet) implement each block in sequence: check off tasks, commit code, push branch, open PR, signal done
6. Human reviews the PR on GitHub, merges, moves Linear block to Done

When all blocks are done, the Core Plan moves to Human Review. Human moves it to Done. The project is complete.

---

## Human Interface

The `resonance` CLI and TUI dashboard (`resonance watch`) give operators full visibility and control:

| Command | Purpose |
|---|---|
| `./onair.sh` | Start orchestrator + TUI dashboard |
| `resonance status` | All active runs |
| `resonance attach QO-123` | Print worktree + log paths for an issue |
| `/reso QO-123` | Load full issue context into any Claude session |
| `/reso-takeover QO-123` | Pause agent, take over the worktree |
| `/reso-handback` | Commit work, post handback comment, resume Resonance |

### Opening a Waiting Run in Claude Code (TUI shortcut)

When the TUI shows a run in **Human Review** or **Agent Feedback Needed**, press **`o`** to open it directly in Claude Code:

1. The TUI shows a modal with the issue ID, branch, worktree path, and a prompt for an optional opening message
2. A new terminal window opens, `cd`'d to the worktree, with a hint to run `/reso {issue_id}` to load full context
3. Any message you typed in the modal is copied to the clipboard so you can paste it as your first prompt to Claude

This is the recommended way to take over a waiting issue without leaving the dashboard.

The TUI shows active runs, the full Linear pipeline, event stream, and a trace viewer for debugging agent decisions.
"""


def main():
    api_key = os.environ.get("LINEAR_API_KEY")
    if not api_key:
        print("ERROR: LINEAR_API_KEY not set in .env")
        sys.exit(1)

    client = LinearClient(api_key)

    project = client.get_project(PROJECT_ID)
    if not project:
        print(f"ERROR: project {PROJECT_ID} not found")
        sys.exit(1)
    print(f"Project: {project['name']}")

    # Find existing document to update
    docs = client.get_project_documents(PROJECT_ID)
    existing = next((d for d in docs if d.get("title") == DOCUMENT_TITLE), None)

    if existing:
        doc_id = existing["id"]
        print(f"Updating existing document (id={doc_id})...")
        result = client.update_document(doc_id, DOCUMENT_TITLE, DOCUMENT_CONTENT)
        if result.get("success"):
            doc = result.get("document", {})
            print(f"✓ Document updated: {doc.get('title')} — {doc.get('url', '(no url)')}")
        else:
            print(f"✗ documentUpdate failed: {result}")
            sys.exit(1)
    else:
        print("No existing document found — creating...")
        result = client.create_document(
            title=DOCUMENT_TITLE,
            content=DOCUMENT_CONTENT,
            project_id=PROJECT_ID,
        )
        if result.get("success"):
            doc = result.get("document", {})
            print(f"✓ Document created: {doc.get('title')} — {doc.get('url', '(no url)')}")
        else:
            print(f"✗ documentCreate failed: {result}")
            sys.exit(1)


if __name__ == "__main__":
    main()
