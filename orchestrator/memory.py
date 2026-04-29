"""
Per-issue local memory: plan, context, decisions, artifacts, handoffs, feedback.

Directory structure per issue:
  runs/memory/{issue_id}/
    plan.md              — approved plan (written once by Planning Agent)
    context.json         — current state: iteration, status, what's next
    decisions.md         — key decisions + rationale (append-only)
    artifacts.json       — all produced artifacts with URLs and paths
    phases.json          — phase registry (plan issues only)
    completion-report.md — final report written when issue reaches Done
    handoffs/
      iter-{n}.md        — handoff document written at end of each iteration
    feedback/
      {ts}.md            — human feedback entries with timestamps
"""
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

MEMORY_ROOT = Path("runs/memory")
_lock = threading.Lock()


def _dir(issue_id: str) -> Path:
    d = MEMORY_ROOT / issue_id
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Plan ──────────────────────────────────────────────────────────────────────

def write_plan(issue_id: str, content: str) -> None:
    """Write the approved plan. No-op if plan.md already exists."""
    p = _dir(issue_id) / "plan.md"
    if not p.exists():
        p.write_text(content)


def get_plan(issue_id: str) -> Optional[str]:
    p = _dir(issue_id) / "plan.md"
    return p.read_text() if p.exists() else None


# ── Context ───────────────────────────────────────────────────────────────────

def update_context(issue_id: str, **kwargs) -> None:
    p = _dir(issue_id) / "context.json"
    with _lock:
        ctx: dict = {}
        if p.exists():
            try:
                ctx = json.loads(p.read_text())
            except Exception:
                pass
        ctx.update(kwargs)
        ctx["updated_at"] = datetime.now(timezone.utc).isoformat()
        p.write_text(json.dumps(ctx, indent=2))


def get_context(issue_id: str) -> dict:
    p = _dir(issue_id) / "context.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


# ── Phases (plan issues only) ─────────────────────────────────────────────────

def write_phases(issue_id: str, phases: list[dict]) -> None:
    p = _dir(issue_id) / "phases.json"
    p.write_text(json.dumps({
        "phases": phases,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2))


def get_phases(issue_id: str) -> list[dict]:
    p = _dir(issue_id) / "phases.json"
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text()).get("phases", [])
    except Exception:
        return []


# ── Plans (PEP issues only) ───────────────────────────────────────────────────

def write_plans(issue_id: str, plans: list[dict]) -> None:
    """Persist plan metadata created by the PEP Reader Agent.

    Each plan dict: {id, identifier, title, blocks_ids: [uuid, ...]}
    blocks_ids lists plan UUIDs that this plan is blocked by.
    """
    p = _dir(issue_id) / "plans.json"
    p.write_text(json.dumps({
        "plans": plans,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2))


def get_plans(issue_id: str) -> list[dict]:
    p = _dir(issue_id) / "plans.json"
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text()).get("plans", [])
    except Exception:
        return []


# ── Handoffs ──────────────────────────────────────────────────────────────────

def write_handoff(issue_id: str, iteration: int, content: str) -> None:
    d = _dir(issue_id) / "handoffs"
    d.mkdir(exist_ok=True)
    (d / f"iter-{iteration}.md").write_text(content)


def get_latest_handoff(issue_id: str) -> Optional[str]:
    d = _dir(issue_id) / "handoffs"
    if not d.exists():
        return None
    files = sorted(d.glob("iter-*.md"))
    return files[-1].read_text() if files else None


# ── Feedback ──────────────────────────────────────────────────────────────────

def write_feedback(issue_id: str, text: str, source: str = "human") -> None:
    d = _dir(issue_id) / "feedback"
    d.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    (d / f"{ts}.md").write_text(f"# Feedback — {ts}\n**Source**: {source}\n\n{text}\n")


def get_all_feedback(issue_id: str) -> list[str]:
    d = _dir(issue_id) / "feedback"
    if not d.exists():
        return []
    return [f.read_text() for f in sorted(d.glob("*.md"))]


# ── Artifacts ─────────────────────────────────────────────────────────────────

def update_artifacts(issue_id: str, artifacts: dict) -> None:
    p = _dir(issue_id) / "artifacts.json"
    with _lock:
        existing: dict = {}
        if p.exists():
            try:
                existing = json.loads(p.read_text())
            except Exception:
                pass
        existing.update(artifacts)
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
        p.write_text(json.dumps(existing, indent=2))


def get_artifacts(issue_id: str) -> dict:
    p = _dir(issue_id) / "artifacts.json"
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text())
        data.pop("updated_at", None)
        return data
    except Exception:
        return {}


# ── Decisions ─────────────────────────────────────────────────────────────────

def append_decision(issue_id: str, decision: str, rationale: str = "") -> None:
    p = _dir(issue_id) / "decisions.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    entry = f"\n## {ts}\n**Decision**: {decision}\n"
    if rationale:
        entry += f"**Rationale**: {rationale}\n"
    with _lock:
        with open(p, "a") as f:
            f.write(entry)


# ── Completion report ─────────────────────────────────────────────────────────

def write_completion_report(issue_id: str, content: str) -> None:
    (_dir(issue_id) / "completion-report.md").write_text(content)


# ── RESONANCE.md (portable checkpoint written to worktree root) ──────────────

def write_resonance_checkpoint(
    issue_id: str,
    worktree_path: str,
    issue_url: str,
    issue_title: str,
    branch: str,
    by: str,
    status: str,
    progress_lines: list[str] | None = None,
    whats_left: str = "",
    decisions: str = "",
) -> Path | None:
    """Write RESONANCE.md to the worktree root.

    Called on pause, Human Review transition, and via `resonance checkpoint`.
    Returns the path written, or None if the worktree does not exist.
    """
    wt = Path(worktree_path)
    if not wt.exists():
        return None

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    progress_block = "\n".join(progress_lines) if progress_lines else "_No progress recorded yet_"

    resume_note = (
        f"1. `cd {worktree_path}`\n"
        f"2. `/reso {issue_id}` — loads full context\n"
        f"3. Continue from the first unchecked item above"
    )
    if status in ("Done", "complete"):
        resume_note = "No further work needed in this worktree."

    content = f"""# RESONANCE — {issue_id}
Updated: {ts}  |  By: {by}
Linear: {issue_url}  |  Branch: {branch}  |  Status: {status}

## Issue
{issue_title}

## Progress
{progress_block}

## What's Left
{whats_left or "_See unchecked items above_"}

## Key Decisions
{decisions or "_None recorded_"}

## How to Resume
{resume_note}
"""

    dest = wt / "RESONANCE.md"
    dest.write_text(content)
    return dest


# ── Context brief (for agent prompts and /pd-issue) ───────────────────────────

def build_context_brief(issue_id: str, include_plan: bool = True) -> str:
    """Return a markdown brief of all memory for this issue."""
    lines = [f"# Memory Context — {issue_id}", ""]

    ctx = get_context(issue_id)
    if ctx:
        lines += ["## Current State", ""]
        for k, v in ctx.items():
            if k != "updated_at":
                lines.append(f"- **{k}**: {v}")
        lines.append("")

    if include_plan:
        plan = get_plan(issue_id)
        if plan:
            lines += ["## Approved Plan", "", plan, ""]

    handoff = get_latest_handoff(issue_id)
    if handoff:
        lines += ["## Previous Iteration Handoff", "", handoff, ""]

    feedback = get_all_feedback(issue_id)
    if feedback:
        lines += ["## Human Feedback", ""]
        for fb in reversed(feedback):
            lines.append(fb)
        lines.append("")

    artifacts = get_artifacts(issue_id)
    if artifacts:
        lines += ["## Artifacts Produced", ""]
        for k, v in artifacts.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")

    return "\n".join(lines)
