"""
Loads WORKFLOW.md and environment variables into a typed Config object.
Called once at startup; passed to all components.

Credential loading order:
  1. Environment variables (highest priority — good for CI/CD)
  2. .env file in the current working directory (loaded by python-dotenv)
WORKFLOW.md contains only policy config — no credentials live there.
"""
import os
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Load .env if present — silently skip if python-dotenv isn't installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

WORKFLOW_PATH = Path("WORKFLOW.md")


def load_workflow() -> dict:
    with open(WORKFLOW_PATH) as f:
        return yaml.safe_load(f)


@dataclass
class Config:
    workflow: dict
    linear_api_key: str
    linear_team_id: str
    linear_project_id: Optional[str]
    figma_api_key: Optional[str]
    github_token: Optional[str]

    # ── State names (env-overridable, set by resonance setup) ────────────────

    @property
    def state_eligibility(self) -> str:
        return (
            os.environ.get("LINEAR_STATE_ELIGIBILITY", "").strip()
            or self.workflow["linear"]["eligibility_state"]
        )

    @property
    def state_in_progress(self) -> str:
        return os.environ.get("LINEAR_STATE_IN_PROGRESS", "").strip() or "In Progress"

    @property
    def state_feedback(self) -> str:
        return os.environ.get("LINEAR_STATE_FEEDBACK", "").strip() or "Agent Feedback Needed"

    @property
    def state_review(self) -> str:
        return (
            os.environ.get("LINEAR_STATE_REVIEW", "").strip()
            or self.workflow.get("handoff", {}).get("success", "Human Review")
        )

    @property
    def state_return(self) -> str:
        return (
            os.environ.get("LINEAR_STATE_RETURN", "").strip()
            or self.workflow.get("handoff", {}).get("failure", "Todo")
        )

    # Convenience accessors
    @property
    def eligibility_state(self) -> str:
        return self.state_eligibility

    @property
    def max_parallel_runs(self) -> int:
        return self.workflow.get("concurrency", {}).get("max_parallel_runs", 2)

    @property
    def poll_interval(self) -> int:
        return self.workflow.get("polling", {}).get("interval_seconds", 60)

    @property
    def max_attempts(self) -> int:
        return self.workflow.get("retry", {}).get("max_attempts", 3)

    @property
    def backoff_seconds(self) -> list[int]:
        return self.workflow.get("retry", {}).get("backoff_seconds", [5, 15, 60])

    @property
    def stall_minutes(self) -> int:
        return self.workflow.get("retry", {}).get("on_stall_minutes", 30)

    def task_config(self, task_type: str) -> dict:
        return self.workflow["task_types"][task_type]

    def unsupported_config(self) -> dict:
        cfg = dict(self.workflow.get("unsupported", {
            "action": "post_comment_and_return",
            "return_state": "Todo",
            "comment": "Task type not supported by orchestrator.",
        }))
        cfg["return_state"] = self.state_return
        return cfg


def load_config() -> Config:
    workflow = load_workflow()

    linear_api_key = os.environ.get("LINEAR_API_KEY", "").strip()
    if not linear_api_key:
        raise ValueError(
            "LINEAR_API_KEY is required.\n"
            "Set it in your .env file or as an environment variable.\n"
            "Run: resonance setup  to configure interactively."
        )

    linear_team_id = os.environ.get("LINEAR_TEAM_ID", "").strip()
    if not linear_team_id:
        raise ValueError(
            "LINEAR_TEAM_ID is required.\n"
            "Set it in your .env file or as an environment variable.\n"
            "Run: resonance setup  to configure interactively."
        )

    # LINEAR_PROJECT_ID now means the project UUID for issue filtering (optional).
    # It is no longer a fallback for LINEAR_TEAM_ID.
    linear_project_id = os.environ.get("LINEAR_PROJECT_ID", "").strip() or None

    return Config(
        workflow=workflow,
        linear_api_key=linear_api_key,
        linear_team_id=linear_team_id,
        linear_project_id=linear_project_id,
        figma_api_key=os.environ.get("FIGMA_API_KEY") or None,
        github_token=os.environ.get("GITHUB_TOKEN") or None,
    )
