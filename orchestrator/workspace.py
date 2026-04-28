"""
Git worktree lifecycle management.
Each issue gets an isolated worktree at workspaces/{issue_id} on branch agent/{issue_id}.
The orchestrator writes a minimal .claude/settings.json pointing at shared plugin dirs.
"""
import json
import logging
import subprocess
from pathlib import Path

from .config import Config
from .events import write as write_event

logger = logging.getLogger(__name__)


class WorkspaceManager:
    def __init__(self, config: Config):
        self._config = config
        self._base = Path(config.workflow["workspace"]["base_dir"])
        self._base.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def create(self, issue_id: str) -> Path:
        """
        Create a git worktree for issue_id.
        Returns the worktree path. Idempotent: returns existing path if already created.
        """
        path = self._path(issue_id)
        branch = self._branch(issue_id)

        if path.exists():
            logger.info("workspace already exists issue=%s path=%s", issue_id, path)
            return path

        self._git_worktree_add(path, branch)
        self._write_agent_config(path, issue_id)
        _ensure_log_dir()

        write_event(issue_id, "workspace_created", path=str(path), branch=branch)
        logger.info("workspace created issue=%s path=%s branch=%s", issue_id, path, branch)
        return path

    def remove(self, issue_id: str) -> None:
        """Remove the worktree and delete its branch. Safe to call on missing workspace."""
        path = self._path(issue_id)
        branch = self._branch(issue_id)

        if not path.exists():
            return

        try:
            _run(["git", "worktree", "remove", "--force", str(path)])
            _run(["git", "branch", "-D", branch])
            write_event(issue_id, "workspace_removed", path=str(path))
            logger.info("workspace removed issue=%s", issue_id)
        except subprocess.CalledProcessError as e:
            logger.warning("workspace removal failed issue=%s: %s", issue_id, e)

    def path(self, issue_id: str) -> Path:
        return self._path(issue_id)

    def exists(self, issue_id: str) -> bool:
        return self._path(issue_id).exists()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _path(self, issue_id: str) -> Path:
        naming = self._config.workflow["workspace"]["naming"]
        return self._base / naming.format(issue_id=issue_id)

    def _branch(self, issue_id: str) -> str:
        naming = self._config.workflow["workspace"]["branch_naming"]
        return naming.format(issue_id=issue_id)

    def _git_worktree_add(self, path: Path, branch: str) -> None:
        # Create branch from HEAD; --orphan would lose shared history
        try:
            _run(["git", "worktree", "add", "-b", branch, str(path), "HEAD"])
        except subprocess.CalledProcessError:
            # Branch may already exist from a prior failed attempt — try without -b
            _run(["git", "worktree", "add", str(path), branch])

    def _write_agent_config(self, worktree_path: Path, issue_id: str) -> None:
        """
        Write a minimal .claude/settings.json into the worktree.
        Points at shared plugin dirs so agents use shared cc-pipeline skills.
        """
        claude_dir = worktree_path / ".claude"
        claude_dir.mkdir(exist_ok=True)

        agent_cfg = self._config.workflow["workspace"]["agent_config"]
        settings = {
            "pluginDirs": agent_cfg["plugin_dirs"],
            "mcpConfig": agent_cfg["mcp_config"],
            "env": {
                "ISSUE_ID": issue_id,
            },
        }
        settings_path = claude_dir / "settings.json"
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)


def _ensure_log_dir() -> None:
    Path("runs/logs").mkdir(parents=True, exist_ok=True)


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True, text=True)
