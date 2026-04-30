"""
Claude CLI runner.
Launches `claude -p` in a worktree, parses stream-json output, detects AGENT_SIGNALs.
The orchestrator calls Runner.start() then polls Runner.poll() in its main loop.
"""
import json
import logging
import os
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .config import Config
from .events import write as write_event
from . import state as run_state

logger = logging.getLogger(__name__)

SIGNAL_PATTERN = re.compile(r"AGENT_SIGNAL:\s*(\{.*\})")


def _describe_tool_call(tool_name: str, tool_input: dict) -> tuple[str, str]:
    """Return (short_label, detail) for a tool call — used in the event stream."""
    if tool_name == "mcp__linear__linear_create_issue":
        return "Linear  create issue", tool_input.get("title", "")[:70]
    if tool_name == "mcp__linear__linear_create_issues":
        n = len(tool_input.get("issues", []))
        return "Linear  create issues", f"{n} issue(s)"
    if tool_name == "mcp__linear__linear_create_comment":
        body = (tool_input.get("body", "") or "").strip()
        return "Linear  post comment", body.split("\n")[0][:70]
    if tool_name == "mcp__linear__linear_bulk_update_issues":
        ids = tool_input.get("ids", [])
        return "Linear  update issue", ", ".join(ids[:3])
    if tool_name == "mcp__linear__linear_search_issues_by_identifier":
        ids = tool_input.get("identifiers", [])
        return "Linear  read issue", ", ".join(str(i) for i in ids[:3])
    if tool_name == "mcp__linear__linear_get_project":
        return "Linear  get project", tool_input.get("projectId", "")[:40]
    if tool_name == "mcp__linear__linear_list_projects":
        return "Linear  list projects", ""
    if tool_name.startswith("mcp__linear__linear_"):
        action = tool_name[len("mcp__linear__linear_"):].replace("_", " ")
        return f"Linear  {action}", ""
    if tool_name.startswith("mcp__figma__"):
        action = tool_name[len("mcp__figma__"):].replace("_", " ")
        return f"Figma   {action}", ""
    if tool_name == "Bash":
        desc = tool_input.get("description", "") or tool_input.get("command", "")
        return "Bash", str(desc)[:70]
    if tool_name == "Read":
        path = tool_input.get("file_path", "")
        return "Read", path[-60:] if len(path) > 60 else path
    if tool_name in ("Write", "Edit", "MultiEdit"):
        path = tool_input.get("file_path", "")
        return tool_name, path[-60:] if len(path) > 60 else path
    if tool_name == "WebFetch":
        return "WebFetch", tool_input.get("url", "")[:70]
    if tool_name == "WebSearch":
        return "WebSearch", tool_input.get("query", "")[:70]
    if tool_name == "Glob":
        return "Glob", tool_input.get("pattern", "")[:70]
    if tool_name == "Grep":
        return "Grep", tool_input.get("pattern", "")[:70]
    return tool_name[:35], ""


@dataclass
class RunResult:
    issue_id: str
    exit_code: int
    signal: Optional[dict] = None   # last AGENT_SIGNAL if any
    artifacts: dict = field(default_factory=dict)
    error: Optional[str] = None


class Runner:
    def __init__(self, config: Config, issue_id: str, worktree: Path, prompt: str, log_file: str):
        self._config = config
        self._issue_id = issue_id
        self._worktree = worktree
        self._prompt = prompt
        self._log_path = Path(log_file)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

        self._proc: Optional[subprocess.Popen] = None
        self._last_signal: Optional[dict] = None
        self._artifacts: dict = {}
        self._last_output_at: float = time.monotonic()
        self._stdout_thread: Optional[threading.Thread] = None
        self._done = threading.Event()
        self._output_tail: list[str] = []  # last 30 lines for error diagnosis

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self, iteration: int = 1) -> None:
        """Launch claude -p in the worktree. Non-blocking."""
        cmd = self._build_command(iteration)
        run_state.update_run(self._issue_id, pid=None)

        logger.info("launching worker issue=%s cmd=%s", self._issue_id, " ".join(cmd))
        # Build subprocess env: inherit current env and add LINEAR_ACCESS_TOKEN so the
        # linear-mcp server (which reads that var) authenticates correctly. Claude CLI
        # does NOT expand ${VAR} syntax in .mcp.json env fields, so we inject it here.
        proc_env = os.environ.copy()
        if "LINEAR_API_KEY" in proc_env:
            proc_env.setdefault("LINEAR_ACCESS_TOKEN", proc_env["LINEAR_API_KEY"])
        self._proc = subprocess.Popen(
            cmd,
            cwd=str(self._worktree),
            env=proc_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        run_state.update_run(self._issue_id, pid=self._proc.pid)
        write_event(self._issue_id, "worker_started", pid=self._proc.pid, iteration=iteration)

        self._stdout_thread = threading.Thread(
            target=self._consume_stdout, daemon=True, name=f"runner-{self._issue_id}"
        )
        self._stdout_thread.start()

    def poll(self) -> Optional[RunResult]:
        """
        Check if the worker has finished.
        Returns RunResult on completion, None if still running.
        """
        if self._proc is None:
            return None
        if not self._done.is_set():
            return None

        exit_code = self._proc.returncode
        write_event(
            self._issue_id,
            "worker_finished",
            exit_code=exit_code,
            signal=self._last_signal,
            artifacts=self._artifacts,
        )
        error = None
        if exit_code != 0:
            error = _extract_error(self._output_tail) or f"exit code {exit_code}"
            write_event(self._issue_id, "run_error_detail", error=error)

        return RunResult(
            issue_id=self._issue_id,
            exit_code=exit_code,
            signal=self._last_signal,
            artifacts=self._artifacts,
            error=error,
        )

    def is_stalled(self, stall_seconds: int) -> bool:
        elapsed = time.monotonic() - self._last_output_at
        return elapsed > stall_seconds

    def kill(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.kill()
            logger.info("killed worker pid=%s issue=%s", self._proc.pid, self._issue_id)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _build_command(self, iteration: int) -> list[str]:
        issue_id = self._issue_id
        session_name = f"agent-{issue_id}-iter{iteration}"

        cmd = [
            "claude",
            "-p", self._prompt,
            "--output-format", "stream-json",
            "--verbose",              # required for stream-json in print mode (claude >= 2.1)
            "--permission-mode", "bypassPermissions",
            "--name", session_name,
        ]

        # Resolve plugin dirs and mcp-config to absolute paths from repo root.
        # WORKFLOW.md stores repo-root-relative paths; the command runs inside the
        # worktree, so relative paths would resolve against the wrong directory.
        repo_root = Path.cwd().resolve()
        agent_cfg = self._config.workflow["workspace"]["agent_config"]
        for plugin_dir in agent_cfg["plugin_dirs"]:
            cmd += ["--plugin-dir", str(repo_root / plugin_dir)]
        cmd += ["--mcp-config", str(repo_root / agent_cfg["mcp_config"])]
        return cmd

    def _consume_stdout(self) -> None:
        """Read lines from the subprocess, parse stream-json, write to log."""
        assert self._proc is not None
        with open(self._log_path, "a") as log_f:
            for raw_line in self._proc.stdout:  # type: ignore[union-attr]
                self._last_output_at = time.monotonic()
                log_f.write(raw_line)
                log_f.flush()
                self._process_line(raw_line.rstrip())

        self._proc.wait()
        self._done.set()

    def _process_line(self, line: str) -> None:
        if not line:
            return

        # Maintain rolling tail for error diagnosis
        self._output_tail.append(line)
        if len(self._output_tail) > 30:
            self._output_tail.pop(0)

        # Try stream-json parse first
        try:
            event = json.loads(line)
            self._handle_stream_event(event)
            return
        except json.JSONDecodeError:
            pass

        # Plain text fallback — scan for AGENT_SIGNAL
        self._scan_for_signal(line)
        write_event(self._issue_id, "worker_output", text=line[:500])

    def _handle_stream_event(self, event: dict) -> None:
        event_type = event.get("type", "")

        if event_type == "assistant":
            # Tool calls and text are nested in message.content[]
            for item in event.get("message", {}).get("content", []):
                ctype = item.get("type", "")
                if ctype == "text":
                    text = item.get("text", "")
                    if text:
                        self._scan_for_signal(text)
                        # Emit first meaningful line as a brief thinking note
                        first = text.strip().split("\n")[0][:120]
                        if first:
                            write_event(self._issue_id, "agent_thinking", text=first)
                elif ctype == "tool_use":
                    tool_name = item.get("name", "")
                    tool_input = item.get("input", {})
                    label, detail = _describe_tool_call(tool_name, tool_input)
                    write_event(self._issue_id, "agent_action", label=label, detail=detail)

        elif event_type == "result":
            # Final result event — signal may live in the "result" text field
            result_text = event.get("result", "")
            if result_text:
                self._scan_for_signal(result_text)

        elif event_type == "usage":
            write_event(
                self._issue_id,
                "usage",
                input_tokens=event.get("input_tokens", 0),
                output_tokens=event.get("output_tokens", 0),
            )

    def _scan_for_signal(self, text: str) -> None:
        for match in SIGNAL_PATTERN.finditer(text):
            try:
                signal = json.loads(match.group(1))
                self._last_signal = signal
                self._handle_signal(signal)
            except json.JSONDecodeError:
                logger.warning("malformed AGENT_SIGNAL in output")

    def _handle_signal(self, signal: dict) -> None:
        sig_type = signal.get("type")
        logger.info("AGENT_SIGNAL issue=%s type=%s", self._issue_id, sig_type)
        write_event(self._issue_id, "agent_signal", signal=signal)

        if sig_type == "ready_for_review":
            artifacts = signal.get("artifacts", {})
            self._artifacts.update(artifacts)
            run_state.update_run(
                self._issue_id,
                status="waiting_human",
                artifacts=self._artifacts,
            )
        elif sig_type == "human_input_needed":
            run_state.update_run(
                self._issue_id,
                status="needs_input",
                pending_question=signal.get("question"),
            )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_error(tail: list) -> Optional[str]:
    """
    Distil a human-readable error from the last lines of agent output.
    Priority: lines containing 'error' keyword → last 3 plain-text lines.
    Returns None if the tail is empty.
    """
    if not tail:
        return None

    # Prefer explicit error lines (strip stream-json wrapper if present)
    error_lines = []
    for raw in tail:
        text = raw
        try:
            ev = json.loads(raw)
            text = ev.get("text") or ev.get("content") or ev.get("error") or raw
        except Exception:
            pass
        if re.search(r"\berror\b", str(text), re.I):
            error_lines.append(str(text).strip())

    if error_lines:
        return " | ".join(error_lines[-3:])[:400]

    # Fallback: last 3 non-empty lines
    plain = [l.strip() for l in tail if l.strip()][-3:]
    return " | ".join(plain)[:400] if plain else None


def build_prompt(
    issue: dict,
    task_config: dict,
    iteration: int = 1,
    prior_feedback: Optional[list[str]] = None,
    memory_brief: Optional[str] = None,
) -> str:
    """Assemble the prompt sent to Claude for a given issue + iteration."""
    from datetime import datetime, timezone
    issue_id  = issue.get("identifier", issue["id"])
    title     = issue.get("title", "")
    description = issue.get("description", "") or ""
    task_type = _task_type_label(task_config)
    started_at = datetime.now(timezone.utc).strftime("%H:%M UTC")

    lines = [
        _build_persona_header(task_config),
        "",
        f"# Task: {issue_id} — {title}",
        "",
        f"**Task type**: {task_type}",
        f"**Iteration**: {iteration}",
        f"**Started**: {started_at}",
        "",
    ]

    # Inject local memory context before the issue description on iteration > 1
    if memory_brief:
        lines += [memory_brief, ""]

    lines += [
        "## Issue Description",
        description,
        "",
    ]

    skills_section = _build_skills_section(task_config)
    if skills_section:
        lines += [skills_section, ""]

    if prior_feedback:
        lines += ["## Prior Feedback", ""]
        for i, fb in enumerate(prior_feedback, 1):
            lines.append(f"{i}. {fb}")
        lines.append("")

    lines += [
        "## Required Artifacts",
        "",
    ]
    for artifact in task_config.get("artifacts_required", []):
        lines.append(f"- `{artifact}`")
    lines.append("")

    issue_linear_id = issue.get("id", "")

    lines += [
        "## Handoff Protocol",
        "",
        "At the end of your session, write a handoff note to:",
        f"`runs/memory/{issue_id}/handoffs/iter-{iteration}.md`",
        "",
        "The handoff must contain:",
        "- What was done this iteration (specific files, decisions, commands)",
        "- What is still outstanding",
        "- What the next iteration should start with",
        "- Any blockers or caveats",
        "",
        "## Before Signalling — Required Updates",
        "",
        "Before emitting any signal, complete BOTH of these steps using your Linear MCP tools:",
        "",
        "### 1. Update the Linear issue description",
        f"Use `mcp__linear__linear_search_issues_by_identifier` to fetch issue `{issue_id}`.",
        f"Then call `mcp__linear__linear_update_issue` with `id: \"{issue_linear_id}\"` to update `description`:",
        "- Change every completed acceptance criterion: `- [ ]` → `- [x]`",
        "- Append a `## Work Summary` section with: files changed (with paths), key decisions, commands run",
        "",
        "### 2. Post a structured review comment",
        f"Call `mcp__linear__linear_create_comment` with `issueId: \"{issue_linear_id}\"` and this body:",
        "",
        "```markdown",
        f"## Review Ready  · started {started_at}, <current time> elapsed",
        "",
        "### What was done",
        "[Bulleted list — specific files, components, APIs changed]",
        "",
        "### Acceptance Criteria",
        "- [x] [criterion] — [how it was verified]",
        "- [ ] [criterion] — [reason not completed, if any]",
        "",
        "### Insights",
        "[Observations, trade-offs, edge cases discovered during implementation]",
        "",
        "### Recommendations",
        "[Suggested next steps, follow-ups, or improvements worth considering]",
        "```",
        "",
        "## Diagrams",
        "",
        "When a diagram would clarify architecture, flows, or relationships — in a Linear",
        "comment or in a documentation file — write a Mermaid code block directly:",
        "",
        "````markdown",
        "```mermaid",
        "graph TD",
        "  A[Start] --> B[Step]",
        "```",
        "````",
        "",
        "Linear renders Mermaid natively. For docs, Mermaid is standard markdown.",
        "If you need a rendered image URL, fetch from kroki.io:",
        "`POST https://kroki.io/mermaid/svg` with the diagram as plain text body.",
        "",
        "## Figma references",
        "",
        "If the issue contains a Figma URL, use the figma MCP to inspect the design —",
        "extract colours, spacing, component names, and layout, then implement to match.",
        "You cannot write to Figma; it is read-only reference material.",
        "",
        "## Signal Protocol",
        "",
        "When you need a genuine **human decision** (not a tool failure), output exactly:",
        '`AGENT_SIGNAL: {"type": "human_input_needed", "question": "<your question>", "context": "<brief context>"}`',
        "",
        "Do NOT use `human_input_needed` for infrastructure problems (MCP errors, network failures, missing files).",
        "If a tool fails, retry once, then note the failure in your review summary and continue.",
        "",
        "When work is ready for human review, output exactly:",
        '`AGENT_SIGNAL: {"type": "ready_for_review", "summary": "<what was done>", "artifacts": {"preview_url": "<url>"}}`',
        "",
        "Do not end the session without emitting one of these signals.",
    ]

    return "\n".join(lines)


def _task_type_label(task_config: dict) -> str:
    detection = task_config.get("detection", {})
    labels = detection.get("labels", [])
    return "+".join(labels) if labels else "unknown"


_PERSONAS = {
    "plan":             "QO Project Manager / Planning Agent",
    "design_to_code":   "QO Frontend Engineer (Design-to-Code)",
    "frontend_feature": "QO Frontend Engineer",
    "frontend_bug":     "QO Frontend Engineer (Bug Investigation)",
    "backend_feature":  "QO Backend Engineer",
    "backend_bug":      "QO Backend Engineer (Bug Investigation)",
}

_SKILL_DESCRIPTIONS = {
    "connectui-dev":   "prime yourself with ConnectUI design system + code standards",
    "verify":          "run build / lint / tests at the specified level (L1/L2/L3)",
    "qo-pr":           "generate a ConnectUI-standard PR description from git diff",
    "qo-prototype":    "Figma-to-code: fetch design via MCP, map to Orion components, generate code",
    "qo-component":    "scaffold a new Orion/MUI component with Storybook story",
    "qo-bug":          "structured bug investigation workflow",
    "pd-pep":          "extract structured requirements from the Linear issue",
    "pd-context-pack": "gather broad project awareness before starting work",
    "pd-plan-post":    "post implementation plan to Linear for human approval",
    "pd-report-post":  "post execution report to Linear on completion",
    "pd-github-pr":    "open a GitHub PR linked to this Linear issue",
    "review":          "deep code review: correctness, style, security, performance",
}


def _build_persona_header(task_config: dict) -> str:
    task_name = task_config.get("_name", "")
    persona = _PERSONAS.get(task_name, "QO Agent")
    return f"You are a **{persona}** working in the Queen One agentic delivery pipeline."


def _build_skills_section(task_config: dict) -> str:
    skills = task_config.get("skills", [])
    if not skills:
        return ""
    lines = [
        "## Skills Available",
        "",
        "The following slash-command skills are loaded and ready. Invoke them in the order shown:",
        "",
    ]
    for i, skill in enumerate(skills, 1):
        desc = _SKILL_DESCRIPTIONS.get(skill, "")
        desc_part = f" — {desc}" if desc else ""
        lines.append(f"{i}. `/{skill}`{desc_part}")
    lines += [
        "",
        "**Recommended workflow for this task type**:",
    ]
    # Build workflow hint per task type
    task_name = task_config.get("_name", "")
    if task_name in ("design_to_code", "frontend_feature"):
        lines += [
            "1. `/pd-pep` — read and structure requirements from the issue",
            "2. `/connectui-dev <task>` — start implementation in ConnectUI mode",
            "3. `/verify L2` — run build + lint + tests",
            "4. `/qo-pr` — generate PR description",
            "5. `/pd-report-post` — post execution report to Linear",
        ]
    elif task_name == "frontend_bug":
        lines += [
            "1. `/pd-pep` — structure the bug report",
            "2. `/connectui-dev <fix description>` — investigate and fix in ConnectUI mode",
            "3. `/verify L2` — confirm the fix",
            "4. `/pd-report-post` — post execution report",
        ]
    elif task_name in ("backend_feature", "backend_bug"):
        lines += [
            "1. `/pd-pep` — structure requirements",
            "2. Implement the feature/fix",
            "3. `/verify L2` — run tests",
            "4. `/pd-report-post` — post execution report",
        ]
    return "\n".join(lines)


def make_log_path(issue_id: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"runs/logs/{issue_id}-{ts}.log"
