# Claude Worker Adapter

## Purpose

The Claude worker adapter translates a Linear issue and its context into a headless
Claude Code execution. It is the only component that knows how Claude is launched,
what goes into the prompt, and how to interpret Claude's output.

The orchestrator calls it. The TUI observes it via the event stream.
Neither the orchestrator nor the TUI contain any Claude-specific logic.

---

## V1 vs V2 Decision

**V1: `claude -p` (CLI print mode)**
- Launch via subprocess
- Capture stdout as `stream-json`
- Parse events from the stream
- Simple, debuggable, proven path

**V2: Claude Agent SDK (planned migration)**
- Programmatic session control
- Structured event callbacks
- Better resumption and retry
- More robust for long-running orchestration

This document covers V1. The interface is designed so switching to V2 requires
changing only this adapter — not the orchestrator or TUI.

---

## Launch Command

Full CLI invocation for an orchestrated worker run:

```bash
claude -p "{assembled_prompt}" \
  --output-format stream-json \
  --permission-mode acceptEdits \
  --plugin-dir ../../.claude/cc-pipeline \
  --plugin-dir ../../.claude/cc-qo-skills \
  --mcp-config ../../.mcp.json \
  --session-name "agent-{issue_id}-iter{n}" \
  --max-turns 50
```

All paths are relative to the worktree root (`workspaces/QO/QO-123/`).

### Flags explained

| Flag | Value | Reason |
|---|---|---|
| `--output-format stream-json` | always | Structured events for TUI and hooks |
| `--permission-mode acceptEdits` | always | Non-interactive file writes allowed |
| `--plugin-dir` (x2) | cc-pipeline, cc-qo-skills | Policy and execution skills |
| `--mcp-config` | repo root .mcp.json | Linear + Figma MCP access |
| `--session-name` | `agent-{issue_id}-iter{n}` | Enables session resumption |
| `--max-turns` | 50 | Safety cap on unbounded loops |

### MCP loading by task type

The `--mcp-config` file loaded depends on the task type, controlled by WORKFLOW.md:

| Task type | MCPs loaded |
|---|---|
| `design_to_code` | Linear + Figma |
| `frontend_feature` | Linear + Figma (if Figma link present) |
| `frontend_bug` | Linear only |

The worker adapter generates a task-specific mcp config file in the workspace
`workspaces/QO/QO-123/.claude/mcp.json` before launching Claude. This avoids
modifying the repo root `.mcp.json`.

---

## Prompt Assembly

The prompt passed to `claude -p` is assembled from multiple sources in this order:

```
1. System context block
   - Issue ID, title, description
   - Task type from WORKFLOW.md
   - Applicable skills and rules for this task type
   - Iteration number and max iterations

2. Plan document
   - Full approved plan from .claude/memory/pd/plans/
   - Summary of what phases are complete (if iteration > 1)

3. Context pack (if broad awareness was run)
   - Impact map, adjacent team context, blockers
   - Loaded from .claude/memory/pd/context/

4. Prior iteration feedback (if iteration > 1)
   - Human feedback collected via TUI or resonance feedback command
   - Prepended as: "Human feedback from previous iteration: ..."

5. Signal protocol instructions
   - Explicit instructions on how to emit structured signals
   - See Signal Protocol section below

6. Task-specific instructions
   - For design_to_code: Figma reference URL, design system reminder,
     instruction to start dev server and post preview URL
   - For frontend_bug: reproduction steps, before/after expectation
```

### Prompt template (simplified)

```
You are a Claude Code agent working on Linear issue {issue_id}: "{title}".

Task type: {task_type}
Iteration: {n} of max {max_iterations}
Worktree: workspaces/{team_prefix}/{issue_id}

== APPROVED PLAN ==
{plan_content}

{if iteration > 1}
== HUMAN FEEDBACK FROM ITERATION {n-1} ==
{feedback}
{endif}

{if context_pack_exists}
== CONTEXT PACK ==
{context_pack_summary}
{endif}

== YOUR TASK ==
{task_specific_instructions}

== SIGNAL PROTOCOL ==
When you are uncertain about a decision that meaningfully affects the output,
emit this exact line and pause:
  AGENT_SIGNAL: {"type": "human_input_needed", "question": "...", "options": [...]}

When you believe the current iteration is ready for human review, emit:
  AGENT_SIGNAL: {"type": "ready_for_review", "summary": "...", "artifacts": {"preview_url": "..."}}

Do not mark work complete in Linear. The human approves via the TUI.
The plan gate is enforced by pd-guardrail — do not bypass it.
```

---

## Output Stream Parsing

Claude with `--output-format stream-json` emits one JSON object per line on stdout.

```jsonl
{"type":"text","content":"Reading ConnectUI design standards..."}
{"type":"tool_use","name":"Read","input":{"file_path":"src/components/Hero.tsx"}}
{"type":"tool_result","content":"...file content..."}
{"type":"text","content":"AGENT_SIGNAL: {\"type\":\"ready_for_review\",\"summary\":\"...\"}"}
{"type":"done","stop_reason":"end_turn"}
```

The worker adapter reads this stream line by line:

```python
for line in claude_process.stdout:
    event = json.loads(line)

    if event["type"] == "text":
        # Check for AGENT_SIGNAL prefix
        if "AGENT_SIGNAL:" in event["content"]:
            signal = extract_signal(event["content"])
            handle_signal(signal, issue_id)

        # Write to log file
        log_file.write(event["content"])

        # Write raw event to events.jsonl for TUI
        write_event(issue_id, "agent_text", content=event["content"])

    elif event["type"] == "tool_use":
        write_event(issue_id, "tool_called", tool=event["name"])

    elif event["type"] == "done":
        handle_completion(issue_id, event["stop_reason"])
```

---

## Signal Protocol

Agents emit structured signals as a special text prefix. Hooks detect and route them.

### `human_input_needed`

Emitted when the agent is uncertain about a decision that affects output quality.

```
AGENT_SIGNAL: {"type": "human_input_needed", "question": "Which button variant should I use for the CTA?", "options": ["primary", "secondary", "ghost"], "context": "The Figma spec shows primary but the ConnectUI docs mark it deprecated."}
```

**Effect:**
1. `uncertainty_detector` hook captures the signal
2. Writes `human_input_needed` event to `events.jsonl`
3. Orchestrator pauses the run, sets status to `waiting_human`
4. Linear issue moved to `Agent Feedback Needed`
5. TUI shows ⚠ indicator for the issue

### `ready_for_review`

Emitted when the agent believes the current iteration is complete and ready for human eyes.

```
AGENT_SIGNAL: {"type": "ready_for_review", "summary": "Implemented Hero section. Mobile breakpoints added. Preview at http://localhost:3001. Used shadow-sm per ConnectUI spec.", "artifacts": {"preview_url": "http://localhost:3001"}}
```

**Effect:**
1. `uncertainty_detector` hook captures the signal
2. Writes `ready_for_review` event to `events.jsonl`
3. Orchestrator verifies required artifacts are present
4. If artifacts missing: run continues (agent prompted to generate them)
5. If artifacts present: run paused, Linear issue moved to `Agent Feedback Needed`
6. TUI shows "Ready for review" status, human can approve or send feedback

### Artifact verification

Before accepting a `ready_for_review` signal, the orchestrator checks that all
`artifacts_required` from the WORKFLOW.md task type definition are present in the signal.

If `preview_url` is required but absent:
```
Orchestrator injects into next Claude turn:
"Your ready_for_review signal is missing a required artifact: preview_url.
Please start the dev server and include the URL before signalling ready."
```

---

## Artifact Generation

### Preview URL (required for design_to_code, frontend_feature, frontend_bug)

The agent is explicitly instructed to:
1. Run the dev server inside the worktree (`npm run dev` or equivalent)
2. Capture the local URL (e.g. `http://localhost:3001`)
3. Post the URL as a comment to the Linear issue via the Linear MCP
4. Include the URL in the `ready_for_review` signal

The dev server runs as a background process in the worktree.
The orchestrator does not manage it — the agent starts it, the human accesses it.
Port conflicts are avoided by assigning a deterministic port per issue:
`base_port + hash(issue_id) % 1000` (e.g. 3001, 3002, 3003...).

### Before/after evidence (required for frontend_bug)

The agent is instructed to:
1. Capture a description or screenshot of the bug before fixing
2. Capture a description or screenshot of the fixed state
3. Post both to Linear as a comment

Screenshot tooling is out of scope for V1. Description-based evidence is sufficient.

---

## Permission Mode

`--permission-mode acceptEdits` allows the agent to read and write files without
prompting. This is required for non-interactive runs.

The agent cannot:
- Execute arbitrary shell commands without tool confirmation (Bash tool still prompts)
- Push to remote git (no push permissions configured)
- Modify `.claude/hooks/` or `.claude/settings.json` (denied in workspace config)

For higher-trust runs, `bypassPermissions` can be set in WORKFLOW.md per task type.
Default is `acceptEdits` for all V1 task types.

---

## Session Naming and Resumption

Each iteration is named: `agent-{issue_id}-iter{n}` (e.g. `agent-QO-123-iter2`).

If a run crashes mid-iteration, the orchestrator can attempt resumption:
```bash
claude --resume agent-QO-123-iter2 \
  --output-format stream-json \
  --permission-mode acceptEdits \
  ...same flags...
```

Resumption re-enters the conversation at the last checkpoint.
If resumption fails (session expired or corrupted), the orchestrator starts a fresh
iteration with the context prepended to the prompt instead.

Session data is stored by Claude Code in its own session cache.
The orchestrator does not manage session storage directly.

---

## Iteration Context Injection

When iteration > 1, human feedback from the previous iteration is prepended to the prompt:

```python
def build_prompt(issue, plan, iteration, feedback=None, context_pack=None):
    parts = [system_context(issue, iteration)]

    if plan:
        parts.append(f"== APPROVED PLAN ==\n{plan}")

    if iteration > 1 and feedback:
        parts.append(f"== HUMAN FEEDBACK FROM ITERATION {iteration - 1} ==\n{feedback}")

    if context_pack:
        parts.append(f"== CONTEXT PACK ==\n{context_pack}")

    parts.append(task_instructions(issue.task_type))
    parts.append(SIGNAL_PROTOCOL_INSTRUCTIONS)

    return "\n\n".join(parts)
```

Feedback is stored in `runs/state.json` under the issue's `feedback_history` field
and accumulated across iterations for full context.

---

## Timeout and Stall Detection

Handled by the orchestrator, not the adapter. The adapter writes events to the stream;
the orchestrator monitors event recency. If no event is written for `retry.on_stall_minutes`,
the orchestrator kills the process (SIGTERM) and retries.

The `--max-turns 50` flag provides an additional safety cap — Claude will stop after
50 conversation turns regardless of completion state. The orchestrator detects this
as a `stop_reason: max_turns` in the `done` event and handles it as a partial completion.
