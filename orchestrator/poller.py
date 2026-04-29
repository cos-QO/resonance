"""
Main orchestration loop.
Polls Linear for eligible issues, enforces concurrency limits,
launches workers, and drives the run state machine.

Two execution modes:
  plan      — issue has 'plan' label; Planning Agent decomposes into phase issues
  execution — all other task types; normal run → Human Review cycle
"""
import logging
import time
from pathlib import Path
from typing import Optional

from .classifier import classify
from .config import Config
from .events import write as write_event
from .linear_client import LinearClient
from .planner import build_pep_reader_prompt, build_planning_prompt, is_pep_issue, is_plan_issue
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
        if task_type == "pep":
            prompt = build_pep_reader_prompt(issue, self._config)
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

        # Post start comment for pep/plan issues
        if task_type == "pep":
            try:
                self._linear.post_comment(
                    issue["id"],
                    f"▶️ PEP Reader Agent started — analysing PEP and creating Plan issues.\n\n"
                    f"Plan issues will appear in **Todo** for your review. "
                    f"I'll post a summary here when all plans are ready.",
                )
            except Exception:
                logger.warning("failed to post pep start comment issue=%s", issue_id)
        elif task_type == "plan":
            try:
                self._linear.post_comment(
                    issue["id"],
                    f"▶️ Planning Agent started — analysing plan and creating phase issues.\n\n"
                    f"I'll post a summary comment here when all phases are ready.",
                )
            except Exception:
                logger.warning("failed to post plan start comment issue=%s", issue_id)

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

        # PEP Reader Agent completed decomposition
        if signal and signal.get("type") == "pep_decomposed":
            self._finish_pep_decomposed(issue_id, issue, signal)
            return

        # Planning Agent completed decomposition
        if signal and signal.get("type") == "plan_decomposed":
            self._finish_plan_decomposed(issue_id, issue, signal)
            return

        # Agent signalled ready for review
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
                        issue["id"], issue["team"]["id"], self._config.state_feedback
                    )
                    self._linear.post_comment(
                        issue["id"],
                        f"⏸ Agent paused — needs your input:\n\n"
                        f"{signal.get('question', '')}\n\n"
                        f"**To continue:** add a comment with your answer or instructions, "
                        f"then move this issue to **Agent Feedback Needed**.",
                    )
                except Exception:
                    logger.exception("failed to update Linear for human_input_needed issue=%s", issue_id)
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

        # Plan issues always get the planning prompt — even on retry
        if task_type == "plan":
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

    # ── PEP decomposition ─────────────────────────────────────────────────────

    def _finish_pep_decomposed(
        self,
        issue_id: str,
        issue: Optional[dict],
        signal: dict,
    ) -> None:
        """PEP decomposition complete.

        1. Persists plan metadata to local memory.
        2. Sets Linear blocking relations between plan issues (based on signal data).
        3. Marks PEP issue Done.
        4. Updates local run state to complete.
        """
        plans = signal.get("plans", [])
        run_state.update_run(issue_id, status="complete")
        issue_memory.update_context(issue_id, status="complete", plans_count=len(plans))

        if plans:
            issue_memory.write_plans(issue_id, plans)

        # Build a UUID → plan dict map for relation wiring
        uuid_to_plan = {p["id"]: p for p in plans}

        for plan in plans:
            blocked_by_ids = plan.get("blocked_by_ids", [])
            for blocker_uuid in blocked_by_ids:
                if blocker_uuid not in uuid_to_plan:
                    continue
                # blocker_uuid blocks plan["id"]
                try:
                    self._linear.create_issue_relation(
                        issue_id=blocker_uuid,
                        related_issue_id=plan["id"],
                        relation_type="blocks",
                    )
                    blocker_id = uuid_to_plan[blocker_uuid].get("identifier", blocker_uuid[:8])
                    logger.info(
                        "relation set: %s blocks %s",
                        blocker_id,
                        plan.get("identifier", plan["id"][:8]),
                    )
                except Exception:
                    logger.warning(
                        "could not set blocking relation %s→%s",
                        blocker_uuid[:8],
                        plan["id"][:8],
                    )

        if issue:
            try:
                self._linear.set_issue_state(issue["id"], issue["team"]["id"], "Done")
            except Exception:
                logger.warning("could not mark PEP issue Done issue=%s", issue_id)

        write_event(issue_id, "pep_decomposed", plans=len(plans))
        logger.info("pep decomposed issue=%s plans=%d", issue_id, len(plans))

    # ── Dependency management ─────────────────────────────────────────────────

    def _check_active_blockers(self, issue: dict) -> list[dict]:
        """Return blocking issues that are not yet Done/Cancelled.

        Uses inverseRelations (type='blocks') fetched by get_issue().
        """
        blockers = []
        inverse = (issue.get("inverseRelations") or {}).get("nodes", [])
        for rel in inverse:
            if rel.get("type") != "blocks":
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
