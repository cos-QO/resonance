"""
Main orchestration loop.
Polls Linear for eligible issues, enforces concurrency limits,
launches workers, and drives the run state machine.

Two execution modes:
  plan      — issue has 'plan' label; Planning Agent decomposes into phase issues
  execution — all other task types; normal run → Human Review cycle
"""
import logging
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .classifier import classify
from .config import Config
from .events import write as write_event
from .linear_client import LinearClient
from .planner import (
    build_pep_reader_prompt,
    build_planning_prompt,
    build_core_plan_prompt,
    build_block_execution_prompt,
    is_pep_issue,
    is_plan_issue,
)
from .runner import Runner, RunResult, build_prompt, make_log_path
from .workspace import WorkspaceManager
from . import memory as issue_memory
from . import state as run_state

# Linear states that mean "this issue is complete" — used for dependency checks
_DONE_STATES = {"Done", "Cancelled"}

logger = logging.getLogger(__name__)


class Poller:
    def __init__(self, config: Config):
        self._config = config
        self._linear = LinearClient(config.linear_api_key)
        self._workspace = WorkspaceManager(config)
        # issue_id → active Runner
        self._runners: dict[str, Runner] = {}
        # issue identifiers we've already posted a "blocked" [PM] comment on
        # (reset on orchestrator restart — duplicate comments on restart are acceptable)
        self._blocked_notified: set[str] = set()
        # GitHub remote URL (without .git suffix) — used for branch link generation
        try:
            _remote = subprocess.check_output(
                ["git", "remote", "get-url", "origin"], text=True
            ).strip().removesuffix(".git")
        except Exception:
            _remote = ""
        self._github_remote = _remote

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

        # Step 3: detect Human Review / Needs Input resumes
        self._check_human_feedback_resumes()

        # Step 4: pick up new eligible issues
        slots = self._config.max_parallel_runs - len(self._runners)
        if slots <= 0:
            return

        try:
            issues = self._linear.get_eligible_issues(
                self._config.linear_team_id,
                self._config.eligibility_state,
                project_id=self._config.linear_project_id,
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
            if run_state.get_run(issue_id) and run_state.get_run(issue_id)["status"] in {"running", "paused", "waiting_human", "needs_input"}:
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
        PEP issues → PEP Reader prompt.
        Plan issues → Planning Agent prompt.
        All others → execution prompt.
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

        # Fail-closed: verify plan approval state hasn't changed.
        # Also fetches inverseRelations for the dependency check below.
        current = self._linear.get_issue(issue["id"])
        if not current or current["state"]["name"] != self._config.eligibility_state:
            logger.info("issue no longer eligible issue=%s", issue_id)
            return False

        # Dependency check — skip if any blocking issue is not Done/Cancelled
        blockers = self._check_active_blockers(current)
        if blockers:
            self._handle_blocked(issue_id, current, blockers)
            return False

        # Clear blocked notification now that we're proceeding (unblocked)
        if issue_id in self._blocked_notified:
            self._blocked_notified.discard(issue_id)
            try:
                blocker_ids = ", ".join(b["identifier"] for b in blockers)
                self._linear.post_comment(
                    current["id"],
                    f"[PM] ▶️ All dependencies resolved. Starting execution now.\n"
                    f"Previously waiting on: {blocker_ids}",
                )
            except Exception:
                pass

        # Worktree
        try:
            worktree = self._workspace.create(issue_id)
        except Exception:
            logger.exception("workspace creation failed issue=%s", issue_id)
            return False

        # Run state
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

        # Initialise local memory context
        issue_memory.update_context(
            issue_id,
            task_type=task_type,
            status="running",
            iteration=1,
            linear_url=issue.get("url", ""),
        )

        # Build prompt — route by task type
        run = run_state.get_run(issue_id)
        phase = run.get("phase", "execution") if run else "execution"

        if task_type == "pep":
            prompt = build_pep_reader_prompt(issue, self._config)
        elif task_type == "core_plan":
            prompt = build_core_plan_prompt(issue, self._config)
        elif task_type == "block":
            prompt = build_block_execution_prompt(issue, task_cfg)
        elif task_type == "plan":
            prompt = build_planning_prompt(issue, self._config)
        else:
            prompt = build_prompt(issue, task_cfg, iteration=1)

        # Update Linear state → In Progress and stamp with RES label
        try:
            self._linear.set_issue_state(issue["id"], issue["team"]["id"], self._config.state_in_progress)
        except Exception:
            logger.exception("failed to set In Progress issue=%s", issue_id)
            run_state.update_run(issue_id, status="failed", error="linear state update failed")
            return False

        try:
            self._linear.add_issue_label(issue["id"], issue["team"]["id"], "RES")
        except Exception:
            logger.warning("could not add RES label to issue=%s (continuing)", issue_id)

        # Post start comment per task type (with timestamp + estimate)
        now_str = datetime.now(timezone.utc).strftime("%H:%M UTC")
        _estimates = {
            "pep":              "3–7 min",
            "core_plan":        "5–12 min",
            "block":            "10–30 min",
            "plan":             "5–10 min",
            "design_to_code":   "15–45 min",
            "frontend_feature": "10–30 min",
            "frontend_bug":     "5–15 min",
            "backend_feature":  "10–30 min",
            "backend_bug":      "5–15 min",
        }
        estimate = _estimates.get(task_type, "unknown")
        _timing = f"\n\n**Started:** {now_str}  ·  **Estimate:** {estimate}"
        start_comments = {
            "pep": (
                "▶️ PEP Reader Agent started — analysing PEP and creating the Core Plan.\n\n"
                "I'll create one Core Plan issue with all plans, blocks, and tasks, "
                "then move it to **Human Review** for your approval."
                + _timing
            ),
            "core_plan": (
                "▶️ Block Decomposer Agent started — creating Block sub-issues from the approved plan.\n\n"
                "I'll post a summary here when all blocks are created and queued for execution."
                + _timing
            ),
            "plan": (
                "▶️ Planning Agent started — analysing plan and creating phase issues.\n\n"
                "I'll post a summary comment here when all phases are ready."
                + _timing
            ),
        }
        comment = start_comments.get(task_type)
        if comment:
            try:
                self._linear.post_comment(issue["id"], comment)
            except Exception:
                logger.warning("failed to post start comment issue=%s task_type=%s", issue_id, task_type)

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

        # PEP Reader Agent completed — Core Plan created
        if signal and signal.get("type") == "pep_decomposed":
            self._finish_pep_decomposed(issue_id, issue, signal)
            return

        # Block Decomposer Agent completed — Block sub-issues created
        if signal and signal.get("type") == "blocks_created":
            self._finish_blocks_created(issue_id, issue, signal)
            return

        # Block Execution Agent completed and self-verified
        if signal and signal.get("type") == "block_complete":
            self._finish_block_done(issue_id, issue, result)
            return

        # Legacy Planning Agent completed
        if signal and signal.get("type") == "plan_decomposed":
            self._finish_plan_decomposed(issue_id, issue, signal)
            return

        # QA Agent (or execution agent) ready for human review
        if signal and signal.get("type") == "ready_for_review":
            self._finish_success(issue_id, issue, result)
            return

        # Agent signalled needs human input
        if signal and signal.get("type") == "human_input_needed":
            run_state.update_run(issue_id, status="needs_input")
            issue_memory.update_context(issue_id, status="needs_input")
            if issue:
                try:
                    self._linear.set_issue_state(
                        issue["id"], issue["team"]["id"], self._config.state_needs_input
                    )
                except Exception:
                    logger.exception("failed to set Needs Input state issue=%s", issue_id)
            return

        # Worker exited without a signal
        if result.exit_code != 0:
            self._handle_failure(issue_id, issue, result)
        else:
            self._handle_failure(issue_id, issue, result, reason="no signal on clean exit")

    def _finish_plan_decomposed(
        self,
        issue_id: str,
        issue: Optional[dict],
        signal: dict,
    ) -> None:
        """Plan decomposition complete — move plan issue to Done and write memory."""
        phases = signal.get("phases", [])
        run_state.update_run(issue_id, status="complete")
        issue_memory.update_context(issue_id, status="complete", phases_count=len(phases))
        if phases:
            issue_memory.write_phases(issue_id, phases)

        if issue:
            try:
                self._linear.set_issue_state(
                    issue["id"], issue["team"]["id"], "Done"
                )
            except Exception:
                logger.warning("could not mark plan issue Done issue=%s", issue_id)

        write_event(issue_id, "plan_decomposed", phases=len(phases))
        logger.info("plan decomposed issue=%s phases=%d", issue_id, len(phases))

    def _finish_success(self, issue_id: str, issue: Optional[dict], result: RunResult) -> None:
        # Keep "waiting_human" so the TUI still shows this run (Human Review state)
        run_state.update_run(issue_id, status="waiting_human", artifacts=result.artifacts)

        # Persist artifacts to local memory
        if result.artifacts:
            issue_memory.update_artifacts(issue_id, result.artifacts)
        issue_memory.update_context(issue_id, status="waiting_human")

        if issue:
            try:
                self._linear.set_issue_state(
                    issue["id"], issue["team"]["id"], self._config.state_review
                )
                summary   = result.signal.get("summary", "") if result.signal else ""
                artifacts = result.artifacts
                lines = ["✅ **Work complete — ready for your review.**", ""]
                if summary:
                    lines += [summary, ""]
                if artifacts.get("preview_url"):
                    lines.append(f"🔗 **Preview:** {artifacts['preview_url']}")
                lines += [
                    "",
                    "---",
                    "_To continue with feedback:_ add a comment with your instructions, "
                    "then move this issue to **Agent Feedback Needed**.",
                    "_To accept:_ move to **Done**.",
                ]
                self._linear.post_comment(issue["id"], "\n".join(lines))
            except Exception:
                logger.exception("failed to post success to Linear issue=%s", issue_id)

        write_event(issue_id, "run_complete", artifacts=result.artifacts)
        self._write_checkpoint(issue_id, "human_review")
        self._spawn_log_agent(issue_id)

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
            issue_memory.update_context(issue_id, status="running", attempt=attempt + 1)
            write_event(issue_id, "run_retry", attempt=attempt + 1, backoff=backoff_s)
            logger.info("scheduling retry issue=%s attempt=%d in %ds", issue_id, attempt + 1, backoff_s)
            if issue:
                try:
                    self._linear.post_comment(
                        issue["id"],
                        f"🔄 Attempt {attempt} failed — retrying in {backoff_s}s "
                        f"(attempt {attempt + 1}/{max_attempts}).\n\n"
                        f"Error: {reason or result.error or 'unknown'}",
                    )
                except Exception:
                    pass
            time.sleep(backoff_s)
            self._retry_run(issue_id)
        else:
            run_state.update_run(issue_id, status="failed", error=reason or result.error)
            issue_memory.update_context(issue_id, status="failed", error=reason or result.error)
            write_event(issue_id, "run_failed", attempts=attempt, error=reason or result.error)
            if issue:
                try:
                    self._linear.set_issue_state(
                        issue["id"], issue["team"]["id"], self._config.state_return
                    )
                    self._linear.post_comment(
                        issue["id"],
                        f"❌ **Orchestrator gave up** after {attempt} attempt{'s' if attempt != 1 else ''}.\n\n"
                        f"**Error:** {reason or result.error or 'unknown'}\n\n"
                        f"Check `runs/memory/{issue_id}/` for context from previous iterations.\n"
                        f"Fix the issue and move back to **Plan Approved** to retry.",
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

        linear_uuid = current.get("linear_uuid", "")
        issue_data = self._linear.get_issue(linear_uuid) if linear_uuid else None
        if not issue_data:
            return

        try:
            task_type, task_cfg = classify(issue_data, self._config)
        except ValueError:
            return

        next_iter = current["iteration"] + 1
        feedback_history = current.get("feedback_history", [])

        # Build memory brief for context injection
        memory_brief = issue_memory.build_context_brief(issue_id)

        log_file = make_log_path(issue_id)
        run_state.update_run(issue_id, log_file=log_file)
        issue_memory.update_context(issue_id, status="running", iteration=next_iter)

        # Route prompt by task type
        if task_type == "pep":
            prompt = build_pep_reader_prompt(issue_data, self._config)
        elif task_type == "core_plan":
            prompt = build_core_plan_prompt(issue_data, self._config)
        elif task_type == "block":
            prompt = build_block_execution_prompt(issue_data, task_cfg)
        elif task_type == "plan":
            prompt = build_planning_prompt(issue_data, self._config)
        else:
            prompt = build_prompt(
                issue_data,
                task_cfg,
                iteration=next_iter,
                prior_feedback=feedback_history,
                memory_brief=memory_brief,
            )
        runner = Runner(self._config, issue_id, worktree, prompt, log_file)
        runner.start(iteration=next_iter)
        run_state.update_run(issue_id, iteration=next_iter)
        self._runners[issue_id] = runner

    # ── Human Review → Agent Feedback Needed detection ───────────────────────

    def _check_human_feedback_resumes(self) -> None:
        """
        Detect issues a human has moved from Human Review → Agent Feedback Needed.
        Reads new comments as feedback, stores them in local memory, then resumes.
        """
        waiting = {
            iid: run
            for iid, run in run_state.get_active_runs().items()
            if run.get("status") in ("waiting_human", "needs_input") and iid not in self._runners
        }
        if not waiting:
            return

        for issue_id, run in waiting.items():
            linear_uuid = run.get("linear_uuid", "")
            if not linear_uuid:
                continue
            try:
                issue = self._linear.get_issue_with_comments(linear_uuid)
            except Exception:
                continue
            if not issue:
                continue

            current_linear_state = issue["state"]["name"]
            if current_linear_state != self._config.state_feedback:
                continue

            # Human moved to Agent Feedback Needed — extract new comments
            comments = issue.get("comments", {}).get("nodes", [])
            new_feedback = self._extract_human_comments(issue_id, comments)

            for text in new_feedback:
                issue_memory.write_feedback(issue_id, text, source="human_review")
                existing = run.get("feedback_history", [])
                existing.append(text)
                run_state.update_run(issue_id, feedback_history=existing)

            # Reset block phase to execution when human provides feedback
            if run.get("task_type") == "block":
                run_state.update_run(issue_id, phase="execution")
                logger.info("block phase reset to execution after human feedback issue=%s", issue_id)

            write_event(issue_id, "human_feedback_received", comments=len(new_feedback))
            logger.info("resuming after human review issue=%s new_comments=%d", issue_id, len(new_feedback))

            # Post acknowledgement comment
            try:
                self._linear.post_comment(
                    issue["id"],
                    f"↩️ Agent resuming with your feedback "
                    f"({len(new_feedback)} comment{'s' if len(new_feedback) != 1 else ''} received).",
                )
            except Exception:
                pass

            self._retry_run(issue_id)

    def _extract_human_comments(self, issue_id: str, comments: list[dict]) -> list[str]:
        """Return comment bodies written after the last time we checked."""
        ctx = issue_memory.get_context(issue_id)
        last_checked = ctx.get("last_comments_checked_at", "")
        new_texts: list[str] = []
        for c in comments:
            created = c.get("createdAt", "")
            if last_checked and created <= last_checked:
                continue
            body = (c.get("body") or "").strip()
            if body:
                new_texts.append(body)
        issue_memory.update_context(
            issue_id,
            last_comments_checked_at=comments[-1]["createdAt"] if comments else last_checked,
        )
        return new_texts

    # ── PEP → Core Plan ───────────────────────────────────────────────────────

    def _finish_pep_decomposed(
        self,
        issue_id: str,
        issue: Optional[dict],
        signal: dict,
    ) -> None:
        """PEP Reader Agent complete.

        Moves the Core Plan issue to Human Review and marks the PEP Done.
        """
        core_uuid       = signal.get("core_issue_uuid", "")
        core_identifier = signal.get("core_issue_identifier", "")

        run_state.update_run(issue_id, status="complete")
        issue_memory.update_context(issue_id, status="complete", core_issue=core_identifier)

        # Move Core Plan → Human Review; also fix project/parent if agent couldn't set them
        if core_uuid:
            try:
                core_issue = self._linear.get_issue(core_uuid)
                if core_issue:
                    self._linear.set_issue_state(
                        core_uuid, core_issue["team"]["id"], self._config.state_review
                    )
                    logger.info("core plan moved to Human Review core=%s", core_identifier)

                    # Ensure project + parent are set (agent may have omitted them if
                    # MCP schema didn't expose projectId/parentId)
                    patch: dict = {}
                    if self._config.linear_project_id and not core_issue.get("project"):
                        patch["project_id"] = self._config.linear_project_id
                    if issue and not core_issue.get("parent"):
                        patch["parent_id"] = issue["id"]
                    if patch:
                        self._linear.update_issue(core_uuid, **patch)
                        logger.info("core plan patched project/parent core=%s patch=%s", core_identifier, list(patch))
            except Exception:
                logger.warning("could not move core plan to Human Review core=%s", core_identifier)

        # Mark PEP Done
        if issue:
            try:
                self._linear.set_issue_state(issue["id"], issue["team"]["id"], "Done")
            except Exception:
                logger.warning("could not mark PEP Done issue=%s", issue_id)

        write_event(issue_id, "pep_decomposed", core_issue=core_identifier)
        logger.info("pep decomposed issue=%s core_issue=%s", issue_id, core_identifier)

    # ── Core Plan → Blocks ────────────────────────────────────────────────────

    def _finish_blocks_created(
        self,
        issue_id: str,
        issue: Optional[dict],
        signal: dict,
    ) -> None:
        blocks = signal.get("blocks", [])
        block_ids = [b.get("identifier", "") for b in blocks if b.get("identifier")]

        run_state.update_run(issue_id, status="monitoring", block_ids=block_ids)
        issue_memory.update_context(issue_id, status="monitoring", blocks_count=len(blocks))

        if blocks:
            issue_memory.write_phases(issue_id, blocks)

        uuid_to_block = {b["id"]: b for b in blocks}
        for block in blocks:
            for blocker_uuid in block.get("blocked_by_ids", []):
                if blocker_uuid not in uuid_to_block:
                    continue
                try:
                    self._linear.create_issue_relation(
                        issue_id=blocker_uuid,
                        related_issue_id=block["id"],
                        relation_type="blocks",
                    )
                except Exception:
                    logger.warning("could not set blocking relation %s→%s", blocker_uuid[:8], block["id"][:8])

        if issue:
            try:
                self._linear.set_issue_state(
                    issue["id"], issue["team"]["id"], self._config.state_in_progress
                )
            except Exception:
                logger.warning("could not set core plan In Progress issue=%s", issue_id)

        write_event(issue_id, "blocks_created", blocks=len(blocks))
        logger.info("blocks created issue=%s blocks=%d", issue_id, len(blocks))

    # ── Block complete (self-verified) ────────────────────────────────────────

    def _finish_block_done(self, issue_id: str, issue: Optional[dict], result: RunResult) -> None:
        """Block execution complete and self-verified. Mark block Done."""
        summary = (result.signal or {}).get("summary", "")

        run_state.update_run(issue_id, status="complete", artifacts=result.artifacts)
        issue_memory.update_context(issue_id, status="complete")

        if issue:
            try:
                self._linear.mark_all_tasks_done(issue["id"])
            except Exception:
                logger.warning("could not update description tasks issue=%s", issue_id)

            try:
                self._linear.set_issue_state(issue["id"], issue["team"]["id"], "Done")
                branch = f"agent/{issue_id.lower()}"
                github_url = f"{self._github_remote}/tree/{branch}" if self._github_remote else ""
                github_line = f"\n🔗 [View branch on GitHub]({github_url})" if github_url else ""
                lines = ["✅ Block complete and verified.", ""]
                if summary:
                    lines += [summary, ""]
                lines.append(f"Branch: `{branch}`{github_line}")
                lines.append("\n_This block is Done. The parent plan will move to Human Review when all blocks are complete._")
                self._linear.post_comment(issue["id"], "\n".join(lines))
            except Exception:
                logger.exception("failed to mark block Done issue=%s", issue_id)

        # Push branch to GitHub
        current_run = run_state.get_run(issue_id)
        worktree_path = current_run.get("worktree", "") if current_run else ""
        branch = f"agent/{issue_id.lower()}"
        if worktree_path and self._config.github_token:
            try:
                push_result = subprocess.run(
                    ["git", "push", "-u", "origin", branch],
                    cwd=worktree_path,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if push_result.returncode == 0:
                    logger.info("pushed branch issue=%s branch=%s", issue_id, branch)
                    write_event(issue_id, "branch_pushed", branch=branch)
                else:
                    logger.warning("git push failed issue=%s: %s", issue_id, push_result.stderr[:200])
            except Exception:
                logger.exception("git push failed issue=%s", issue_id)

        write_event(issue_id, "block_done")
        logger.info("block done issue=%s", issue_id)
        self._spawn_log_agent(issue_id)

    # ── Dependency management ─────────────────────────────────────────────────

    def _check_active_blockers(self, issue: dict) -> list[dict]:
        """Return blocking issues that are not yet Done/Cancelled.

        Uses relations (type='blocked_by') fetched by get_issue().
        Linear creates a 'blocked_by' relation on the blocked issue with
        relatedIssue pointing to the blocker — so this is the correct field.
        (inverseRelations.relatedIssue points to the issue itself, not the blocker.)
        """
        blockers = []
        for rel in (issue.get("relations") or {}).get("nodes", []):
            if rel.get("type") != "blocked_by":
                continue
            related = rel.get("relatedIssue", {})
            state_name = (related.get("state") or {}).get("name", "")
            if state_name not in _DONE_STATES:
                blockers.append(related)
        return blockers

    def _handle_blocked(self, issue_id: str, issue: dict, blockers: list[dict]) -> None:
        """Log and (once) post a [PM] comment when a plan is held for dependencies."""
        blocker_ids = ", ".join(b.get("identifier", b["id"][:8]) for b in blockers)
        logger.info("issue=%s blocked by %s — skipping this tick", issue_id, blocker_ids)

        # Emit run_blocked event only when the blocker set changes (suppress per-tick spam)
        prev_key = f"_blocked_key_{issue_id}"
        if getattr(self, prev_key, None) != blocker_ids:
            setattr(self, prev_key, blocker_ids)
            write_event(issue_id, "run_blocked", blocked_by=blocker_ids)

        if issue_id not in self._blocked_notified:
            self._blocked_notified.add(issue_id)
            try:
                self._linear.post_comment(
                    issue["id"],
                    f"[PM] ⏸ This plan is waiting for dependencies to complete before it can start.\n\n"
                    f"**Blocked by:** {blocker_ids}\n\n"
                    f"Resonance will start this plan automatically once all blockers reach **Done**. "
                    f"No manual action needed.",
                )
            except Exception:
                logger.warning("could not post blocked comment issue=%s", issue_id)

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
            self._write_checkpoint(issue_id, "paused")

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

    # ── Log agent (Haiku) ─────────────────────────────────────────────────────

    def _spawn_log_agent(self, issue_id: str) -> None:
        """Spawn a lightweight Haiku agent to write RUNLOG.md for handoff."""
        import shutil
        import json as _json
        if not shutil.which("claude"):
            return

        memory_dir = Path(f"runs/memory/{issue_id}")
        context_file = memory_dir / "context.json"
        log_out = memory_dir / "RUNLOG.md"
        memory_dir.mkdir(parents=True, exist_ok=True)

        # Collect events for this issue from runs/events.jsonl
        events_summary = ""
        try:
            events_path = Path("runs/events.jsonl")
            if events_path.exists():
                lines = []
                for raw in events_path.read_text().splitlines():
                    try:
                        ev = _json.loads(raw)
                        if ev.get("issue_id") == issue_id:
                            ts = ev.get("timestamp", "")[:16]
                            etype = ev.get("event_type", "")
                            extra = {k: v for k, v in ev.items() if k not in ("issue_id", "event_type", "timestamp")}
                            lines.append(f"{ts}  {etype}  {extra}" if extra else f"{ts}  {etype}")
                    except Exception:
                        pass
                events_summary = "\n".join(lines[-60:])  # last 60 events
        except Exception:
            pass

        context_summary = ""
        try:
            if context_file.exists():
                context_summary = context_file.read_text()
        except Exception:
            pass

        prompt = f"""You are a log agent. Write a concise RUNLOG.md for issue {issue_id}.

## Run Context
{context_summary}

## Events (most recent 60)
{events_summary}

## Your task
Write a markdown file to `{log_out}` with these sections:
- **Summary**: 2-3 sentences — what was built, what signals were emitted, final state
- **Timeline**: key events with timestamps (workspace ready → worker start → signals → done)
- **Artifacts**: any preview_url, branch, or output paths mentioned in context
- **Handoff notes**: what the next agent or human needs to know to continue this work

Keep it under 50 lines. Write only the file — no other output."""

        try:
            subprocess.Popen(
                [
                    "claude", "-p", prompt,
                    "--model", "claude-haiku-4-5-20251001",
                    "--output-format", "text",
                    "--permission-mode", "bypassPermissions",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("log agent spawned issue=%s output=%s", issue_id, log_out)
        except Exception:
            logger.warning("could not spawn log agent issue=%s", issue_id)

    # ── RESONANCE.md checkpoint ────────────────────────────────────────────────

    def _write_checkpoint(self, issue_id: str, status: str) -> None:
        """Write RESONANCE.md to the issue's worktree. Silently skips if no worktree."""
        run = run_state.get_run(issue_id)
        if not run:
            return
        worktree = run.get("worktree", "")
        branch = run.get("branch", f"agent/{issue_id}")
        linear_uuid = run.get("linear_uuid", "")

        issue_url = ""
        issue_title = issue_id
        if linear_uuid:
            try:
                issue = self._linear.get_issue(linear_uuid)
                if issue:
                    issue_url = issue.get("url", "")
                    issue_title = issue.get("title", issue_id)
            except Exception:
                pass

        try:
            dest = issue_memory.write_resonance_checkpoint(
                issue_id=issue_id,
                worktree_path=worktree,
                issue_url=issue_url,
                issue_title=issue_title,
                branch=branch,
                by="resonance",
                status=status,
            )
            if dest:
                logger.info("RESONANCE.md written issue=%s path=%s", issue_id, dest)
        except Exception:
            logger.exception("failed to write RESONANCE.md issue=%s", issue_id)

    # ── Plan completion monitoring ────────────────────────────────────────────

    def _check_plan_completions(self) -> None:
        """For core_plan runs in 'monitoring' status, check if all blocks are Done.
        If so, move the plan issue to Human Review with a handoff comment.
        """
        all_runs = run_state.get_active_runs()
        monitoring = {
            iid: run for iid, run in all_runs.items()
            if run.get("status") == "monitoring" and run.get("task_type") == "core_plan"
        }

        for issue_id, run in monitoring.items():
            linear_uuid = run.get("linear_uuid", "")
            if not linear_uuid:
                continue

            try:
                issue = self._linear.get_issue(linear_uuid)
            except Exception:
                continue
            if not issue:
                continue

            if issue["state"]["name"] != self._config.state_in_progress:
                continue

            try:
                children = self._linear.get_issue_children(linear_uuid)
            except Exception:
                logger.warning("could not fetch children for plan issue=%s", issue_id)
                continue

            block_children = [
                c for c in children
                if any(lbl["name"].lower() == "block" for lbl in c.get("labels", {}).get("nodes", []))
            ]

            if not block_children:
                continue

            all_done = all(c["state"]["name"] in {"Done"} for c in block_children)
            if not all_done:
                pending = [c["identifier"] for c in block_children if c["state"]["name"] not in {"Done", "Cancelled"}]
                logger.debug("plan=%s waiting on blocks: %s", issue_id, pending)
                continue

            logger.info("all blocks done for plan=%s — moving to Human Review", issue_id)
            run_state.update_run(issue_id, status="complete")

            try:
                self._linear.set_issue_state(
                    issue["id"], issue["team"]["id"], self._config.state_review
                )
                block_lines = "\n".join(
                    f"  - {c['identifier']}: {c['title']}" for c in block_children
                )
                branch_links = "\n".join(
                    f"  - [{c['identifier']} branch]({self._github_remote}/tree/agent/{c['identifier'].lower()})"
                    for c in block_children
                ) if self._github_remote else ""

                worktree_cmds = "\n".join(
                    f"  resonance attach {c['identifier']}" for c in block_children
                )

                github_section = (
                    f"\n**Review on GitHub:**\n{branch_links}\n"
                ) if branch_links else ""

                comment = (
                    f"✅ **All blocks complete — ready for your review.**\n\n"
                    f"**Blocks delivered:**\n{block_lines}\n"
                    f"{github_section}\n"
                    f"**To review or take control of any block:**\n"
                    f"```\n{worktree_cmds}\n```\n\n"
                    f"Each block has a branch `agent/<identifier>`. Open PRs from those branches for code review.\n\n"
                    f"_To approve: move to **Done**. To request changes: add a comment and move to **Agent Feedback Needed**._"
                )
                self._linear.post_comment(issue["id"], comment)
            except Exception:
                logger.exception("failed to move plan to Human Review issue=%s", issue_id)

            write_event(issue_id, "plan_complete_human_review")

    # ── Reconciliation ─────────────────────────────────────────────────────────

    def _reconcile(self) -> None:
        """Check that active local runs still correspond to eligible Linear state."""
        self._check_plan_completions()
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
                # Issue was deleted from Linear — stop and archive
                logger.info("reconcile: issue deleted from Linear, archiving run issue=%s", issue_id)
                runner = self._runners.pop(issue_id, None)
                if runner:
                    runner.kill()
                run_state.update_run(issue_id, status="archived")
                write_event(issue_id, "run_archived", reason="issue_deleted_from_linear")
                try:
                    self._workspace.remove(issue_id)
                except Exception:
                    logger.warning("workspace cleanup failed issue=%s", issue_id)
                continue

            linear_state = issue["state"]["name"]
            # If Linear moved the issue out of active states, stop locally
            cleanup_states = set(self._config.workflow.get("workspace", {}).get("cleanup_on", ["Done", "Cancelled"]))
            if linear_state in cleanup_states or linear_state == self._config.state_return:
                logger.info("reconcile: Linear state=%s, stopping local run issue=%s", linear_state, issue_id)
                runner = self._runners.pop(issue_id, None)
                if runner:
                    runner.kill()
                run_state.update_run(issue_id, status="archived")
                write_event(issue_id, "run_reconciled_stopped", linear_state=linear_state)
                # Clean up worktree per WORKFLOW.md cleanup_on policy
                if linear_state in cleanup_states:
                    try:
                        self._workspace.remove(issue_id)
                    except Exception:
                        logger.warning("workspace cleanup failed issue=%s", issue_id)

    def shutdown(self) -> None:
        write_event("system", "orchestrator_stopping")
        for issue_id, runner in self._runners.items():
            runner.kill()
            run_state.update_run(issue_id, status="paused")
        self._linear.close()
