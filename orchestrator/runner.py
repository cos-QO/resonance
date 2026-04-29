"""
Claude CLI runner.
Launches `claude -p` in a worktree, parses stream-json output, detects AGENT_SIGNALs.
The orchestrator calls Runner.start() then polls Runner.poll() in its main loop.
"""
import json
import logging
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

# Stream-json event types we care about
_TEXT_TYPES = {"assistant", "text"}
_TOOL_TYPES = {"tool_use", "tool_result"}


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

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self, iteration: int = 1) -> None:
        """Launch claude -p in the worktree. Non-blocking."""
        cmd = self._build_command(iteration)
        run_state.update_run(self._issue_id, pid=None)

        logger.info("launching worker issue=%s cmd=%s", self._issue_id, " ".join(cmd))
        self._proc = subprocess.Popen(
            cmd,
            cwd=str(self._worktree),
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
        return RunResult(
            issue_id=self._issue_id,
            exit_code=exit_code,
            signal=self._last_signal,
            artifacts=self._artifacts,
            error=None if exit_code == 0 else f"exit code {exit_code}",
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
        cfg = self._config.workflow["worker"]
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

        # Plugin dirs from workspace agent_config
        agent_cfg = self._config.workflow["workspace"]["agent_config"]
        for plugin_dir in agent_cfg["plugin_dirs"]:
            cmd += ["--plugin-dir", plugin_dir]

        cmd += ["--mcp-config", agent_cfg["mcp_config"]]
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

        if event_type in _TEXT_TYPES:
            text = event.get("text") or event.get("content", "")
            if text:
                self._scan_for_signal(text)
                write_event(self._issue_id, "worker_output", text=str(text)[:500])

        elif event_type in _TOOL_TYPES:
            tool_name = event.get("name", "")
            write_event(self._issue_id, "tool_use", tool=tool_name)

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


def build_prompt(
    issue: dict,
    task_config: dict,
    iteration: int = 1,
    prior_feedback: Optional[list[str]] = None,
    memory_brief: Optional[str] = None,
) -> str:
    """Assemble the prompt sent to Claude for a given issue + iteration."""
    issue_id  = issue.get("identifier", issue["id"])
    title     = issue.get("title", "")
    description = issue.get("description", "") or ""
    task_type = _task_type_label(task_config)

    lines = [
        _build_persona_header(task_config),
        "",
        f"# Task: {issue_id} — {title}",
        "",
        f"**Task type**: {task_type}",
        f"**Iteration**: {iteration}",
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
        "## Review Ready",
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
        "## Signal Protocol",
        "",
        "When you need human input, output exactly:",
        '`AGENT_SIGNAL: {"type": "human_input_needed", "question": "<your question>", "context": "<brief context>"}`',
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
