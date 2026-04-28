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
            stdin=subprocess.PIPE,
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
            "--permission-mode", "acceptEdits",
            "--name", session_name,   # display name for session picker; flag is --name / -n
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
                status="waiting_human",
                pending_question=signal.get("question"),
            )


def build_prompt(
    issue: dict,
    task_config: dict,
    iteration: int = 1,
    prior_feedback: Optional[list[str]] = None,
) -> str:
    """Assemble the prompt sent to Claude for a given issue + iteration."""
    issue_id = issue.get("identifier", issue["id"])
    title = issue.get("title", "")
    description = issue.get("description", "") or ""
    task_type = _task_type_label(task_config)

    lines = [
        f"# Task: {issue_id} — {title}",
        "",
        f"**Task type**: {task_type}",
        f"**Iteration**: {iteration}",
        "",
        "## Issue Description",
        description,
        "",
    ]

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

    lines += [
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


def make_log_path(issue_id: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"runs/logs/{issue_id}-{ts}.log"
