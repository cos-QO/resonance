"""
Main orchestration loop.
Polls Linear for eligible issues, enforces concurrency limits,
launches workers, and drives the run state machine.
"""
import logging
import time
from pathlib import Path
from typing import Optional

from .classifier import classify
from .config import Config
from .events import write as write_event
from .linear_client import LinearClient
from .runner import Runner, RunResult, build_prompt, make_log_path
from .workspace import WorkspaceManager
from . import state as run_state

logger = logging.getLogger(__name__)


class Poller:
    def __init__(self, config: Config):
        self._config = config
        self._linear = LinearClient(config.linear_api_key)
        self._workspace = WorkspaceManager(config)
        # issue_id → active Runner
        self._runners: dict[str, Runner] = {}

    # ── Entry point ───────────────────────────────────────────────────────────

    def run_forever(self) -> None:
        """Blocking loop. Call this from main.py in a thread."""
        logger.info("orchestrator started poll_interval=%ds", self._config.poll_interval)
        write_event("system", "orchestrator_started")

        reconcile_counter = 0
        reconcile_every = max(
            1,
            self._config.workflow["polling"]["reconcile_interval_seconds"]
            // self._config.poll_interval,
        )

        while True:
            try:
                self._tick()
                reconcile_counter += 1
                if reconcile_counter >= reconcile_every:
                    self._reconcile()
                    reconcile_counter = 0
            except Exception:
                logger.exception("unhandled error in poller tick")

            time.sleep(self._config.poll_interval)

    # ── Poll tick ─────────────────────────────────────────────────────────────

    def _tick(self) -> None:
        # Step 1: advance existing runs
        finished = self._advance_runners()
        for result in finished:
            self._handle_result(result)

        # Step 2: handle CLI commands (pause, abort, feedback)
        self._process_commands()

        # Step 3: pick up new eligible issues
        slots = self._config.max_parallel_runs - len(self._runners)
        if slots <= 0:
            return

        try:
            issues = self._linear.get_eligible_issues(
                self._config.linear_team_id,
                self._config.eligibility_state,
            )
        except Exception:
            logger.exception("failed to fetch eligible issues from Linear")
            return

        for issue in issues:
            if slots <= 0:
                break
            issue_id = issue["identifier"]
            if issue_id in self._runners:
                continue
            if run_state.get_run(issue_id) and run_state.get_run(issue_id)["status"] in {"running", "paused", "waiting_human"}:
                continue
            if self._start_run(issue):
                slots -= 1

    # ── Runner management ─────────────────────────────────────────────────────

    def _advance_runners(self) -> list[RunResult]:
        """Poll all active runners. Return results for finished ones."""
        finished = []
        stall_seconds = self._config.stall_minutes * 60

        for issue_id, runner in list(self._runners.items()):
            # Check for stall
            if runner.is_stalled(stall_seconds):
                logger.warning("stalled worker issue=%s — killing", issue_id)
                write_event(issue_id, "worker_stalled")
                runner.kill()

            result = runner.poll()
            if result is not None:
                del self._runners[issue_id]
                finished.append(result)

        return finished

    def _start_run(self, issue: dict) -> bool:
        """
        Classify, validate, and launch a worker for an issue.
        Returns True if a worker was started.
        """
        issue_id = issue["identifier"]

        # Classify task type
        try:
            task_type, task_cfg = classify(issue, self._config)
        except ValueError as e:
            logger.warning("unsupported task type issue=%s: %s", issue_id, e)
            self._handle_unsupported(issue)
            return False

        # Fail-closed: verify plan approval state hasn't changed
        current = self._linear.get_issue(issue["id"])
        if not current or current["state"]["name"] != self._config.eligibility_state:
            logger.info("issue no longer eligible issue=%s", issue_id)
            return False

        # Worktree
        try:
            worktree = self._workspace.create(issue_id)
        except Exception:
            logger.exception("workspace creation failed issue=%s", issue_id)
            return False

        # Run state — store both the display identifier and the Linear UUID
        log_file = make_log_path(issue_id)
        run_state.create_run(
            issue_id=issue_id,
            task_type=task_type,
            worker=task_cfg.get("worker", self._config.workflow["worker"]["default"]),
            worktree=str(worktree),
            branch=f"agent/{issue_id}",
            log_file=log_file,
            linear_uuid=issue["id"],
        )

        # Build prompt
        prompt = build_prompt(issue, task_cfg, iteration=1)

        # Update Linear state → In Progress
        try:
            self._linear.set_issue_state(issue["id"], issue["team"]["id"], "In Progress")
        except Exception:
            logger.exception("failed to set In Progress issue=%s", issue_id)
            run_state.update_run(issue_id, status="failed", error="linear state update failed")
            return False

        # Launch
        runner = Runner(self._config, issue_id, worktree, prompt, log_file)
        runner.start(iteration=1)
        self._runners[issue_id] = runner

        write_event(issue_id, "run_started", task_type=task_type)
        logger.info("started run issue=%s task_type=%s", issue_id, task_type)
        return True

    # ── Result handling ───────────────────────────────────────────────────────

    def _handle_result(self, result: RunResult) -> None:
        issue_id = result.issue_id
        current_state = run_state.get_run(issue_id)
        if not current_state:
            return

        linear_uuid = current_state.get("linear_uuid", "")
        issue = self._linear.get_issue(linear_uuid) if linear_uuid else None

        signal = result.signal

        # Agent signalled ready for review
        if signal and signal.get("type") == "ready_for_review":
            self._finish_success(issue_id, issue, result)
            return

        # Agent signalled needs human input
        if signal and signal.get("type") == "human_input_needed":
            run_state.update_run(issue_id, status="waiting_human")
            if issue:
                try:
                    self._linear.set_issue_state(
                        issue["id"], issue["team"]["id"], "Agent Feedback Needed"
                    )
                    self._linear.post_comment(
                        issue["id"],
                        f"⏸ Agent paused — needs input:\n\n{signal.get('question', '')}",
                    )
                except Exception:
                    logger.exception("failed to update Linear for human_input_needed issue=%s", issue_id)
            return

        # Worker exited without a signal
        if result.exit_code != 0:
            self._handle_failure(issue_id, issue, result)
        else:
            # Clean exit without signal: treat as stale/incomplete, retry
            self._handle_failure(issue_id, issue, result, reason="no signal on clean exit")

    def _finish_success(self, issue_id: str, issue: Optional[dict], result: RunResult) -> None:
        run_state.update_run(issue_id, status="complete", artifacts=result.artifacts)
        if issue:
            try:
                self._linear.set_issue_state(
                    issue["id"], issue["team"]["id"], "Human Review"
                )
                summary = result.signal.get("summary", "") if result.signal else ""
                artifacts = result.artifacts
                comment_lines = ["✅ Agent completed. Ready for your review.", ""]
                if summary:
                    comment_lines += [summary, ""]
                if artifacts.get("preview_url"):
                    comment_lines.append(f"Preview: {artifacts['preview_url']}")
                self._linear.post_comment(issue["id"], "\n".join(comment_lines))
            except Exception:
                logger.exception("failed to post success to Linear issue=%s", issue_id)
        write_event(issue_id, "run_complete", artifacts=result.artifacts)

    def _handle_failure(
        self,
        issue_id: str,
        issue: Optional[dict],
        result: RunResult,
        reason: str = "",
    ) -> None:
        current = run_state.get_run(issue_id)
        attempt = current["attempt"] if current else 1
        max_attempts = self._config.max_attempts
        backoff = self._config.backoff_seconds

        if attempt < max_attempts:
            backoff_s = backoff[min(attempt - 1, len(backoff) - 1)]
            run_state.update_run(issue_id, status="running", attempt=attempt + 1)
            write_event(issue_id, "run_retry", attempt=attempt + 1, backoff=backoff_s)
            logger.info("scheduling retry issue=%s attempt=%d in %ds", issue_id, attempt + 1, backoff_s)
            time.sleep(backoff_s)
            self._retry_run(issue_id)
        else:
            run_state.update_run(issue_id, status="failed", error=reason or result.error)
            write_event(issue_id, "run_failed", attempts=attempt, error=reason or result.error)
            if issue:
                try:
                    self._linear.set_issue_state(
                        issue["id"], issue["team"]["id"], "Todo"
                    )
                    self._linear.post_comment(
                        issue["id"],
                        f"❌ Orchestrator gave up after {attempt} attempts.\n\nError: {reason or result.error or 'unknown'}",
                    )
                except Exception:
                    logger.exception("failed to post failure to Linear issue=%s", issue_id)

    def _retry_run(self, issue_id: str) -> None:
        current = run_state.get_run(issue_id)
        if not current:
            return

        worktree = Path(current["worktree"])
        if not worktree.exists():
            try:
                worktree = self._workspace.create(issue_id)
            except Exception:
                logger.exception("workspace re-creation failed issue=%s", issue_id)
                return

        # Rebuild prompt with feedback history
        feedback_history = current.get("feedback_history", [])
        linear_uuid = current.get("linear_uuid", "")
        issue_data = self._linear.get_issue(linear_uuid) if linear_uuid else None
        if not issue_data:
            return

        try:
            _, task_cfg = classify(issue_data, self._config)
        except ValueError:
            return

        log_file = make_log_path(issue_id)
        run_state.update_run(issue_id, log_file=log_file)
        prompt = build_prompt(
            issue_data,
            task_cfg,
            iteration=current["iteration"] + 1,
            prior_feedback=feedback_history,
        )
        runner = Runner(self._config, issue_id, worktree, prompt, log_file)
        runner.start(iteration=current["iteration"] + 1)
        run_state.update_run(issue_id, iteration=current["iteration"] + 1)
        self._runners[issue_id] = runner

    # ── Unsupported task type ─────────────────────────────────────────────────

    def _handle_unsupported(self, issue: dict) -> None:
        issue_id = issue["identifier"]
        cfg = self._config.unsupported_config()
        write_event(issue_id, "unsupported_task_type")
        try:
            self._linear.post_comment(issue["id"], cfg["comment"])
            self._linear.set_issue_state(
                issue["id"], issue["team"]["id"], cfg["return_state"]
            )
        except Exception:
            logger.exception("failed to handle unsupported task type issue=%s", issue_id)

    # ── CLI command processing ─────────────────────────────────────────────────

    def _process_commands(self) -> None:
        active = run_state.get_active_runs()
        for issue_id, run in active.items():
            pos = run.get("_cmd_pos", 0)
            commands, new_pos = run_state.read_commands(issue_id, after_position=pos)
            if new_pos != pos:
                run_state.update_run(issue_id, _cmd_pos=new_pos)

            for cmd in commands:
                self._dispatch_command(issue_id, cmd)

    def _dispatch_command(self, issue_id: str, cmd: dict) -> None:
        action = cmd.get("action")
        logger.info("command issue=%s action=%s", issue_id, action)

        if action == "pause":
            runner = self._runners.get(issue_id)
            if runner:
                runner.kill()
                del self._runners[issue_id]
            run_state.update_run(issue_id, status="paused")
            write_event(issue_id, "run_paused")

        elif action == "abort":
            runner = self._runners.get(issue_id)
            if runner:
                runner.kill()
                del self._runners[issue_id]
            run_state.update_run(issue_id, status="failed", error="aborted by operator")
            write_event(issue_id, "run_aborted")

        elif action == "feedback":
            text = cmd.get("text", "")
            run = run_state.get_run(issue_id)
            if run:
                history = run.get("feedback_history", [])
                history.append(text)
                run_state.update_run(issue_id, feedback_history=history)
            write_event(issue_id, "feedback_received", text=text)

        elif action == "approve":
            # Resume a waiting_human run
            run = run_state.get_run(issue_id)
            if run and run["status"] == "waiting_human" and issue_id not in self._runners:
                self._retry_run(issue_id)
            write_event(issue_id, "run_approved")

    # ── Reconciliation ─────────────────────────────────────────────────────────

    def _reconcile(self) -> None:
        """Check that active local runs still correspond to eligible Linear state."""
        active = run_state.get_active_runs()
        for issue_id, run in active.items():
            linear_uuid = run.get("linear_uuid", "")
            if not linear_uuid:
                continue
            try:
                issue = self._linear.get_issue(linear_uuid)
            except Exception:
                continue
            if not issue:
                continue

            linear_state = issue["state"]["name"]
            # If Linear moved the issue out of active states, stop locally
            if linear_state in {"Done", "Cancelled", "Todo"}:
                logger.info("reconcile: Linear state=%s, stopping local run issue=%s", linear_state, issue_id)
                runner = self._runners.pop(issue_id, None)
                if runner:
                    runner.kill()
                run_state.update_run(issue_id, status="archived")
                write_event(issue_id, "run_reconciled_stopped", linear_state=linear_state)

    def shutdown(self) -> None:
        write_event("system", "orchestrator_stopping")
        for issue_id, runner in self._runners.items():
            runner.kill()
            run_state.update_run(issue_id, status="paused")
        self._linear.close()
