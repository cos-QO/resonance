"""
Git worktree lifecycle management.

Non-block issues (pep, core_plan, plan, execution):
  With project:   workspaces/{project_slug}/issues/{issue_id}   branch: agent/{issue_id}
  Without project: workspaces/{team_prefix}/{issue_id}          branch: agent/{issue_id}

Block issues (is_block=True, project scoped):
  Shared worktree: workspaces/{project_slug}/main/              branch: agent/{project_slug}
  Per-block data:  workspaces/{project_slug}/issues/{issue_id}/ (plain directory, not a worktree)

  All block agents for a project share one git worktree so they build on the same codebase.
  The orchestrator updates ISSUE_ID (and ISSUE_PATH) in .claude/settings.json each time a new
  block starts; MAIN_PATH always points to the shared worktree root.

The project_slug is the Linear project name slugified (spaces/punctuation → hyphens).
The orchestrator writes a minimal .claude/settings.json into each worktree.
"""
import json
import logging
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .config import Config
from .events import write as write_event

logger = logging.getLogger(__name__)


def slugify(name: str) -> str:
    """Convert a display name to a filesystem-safe slug. 'D2D Demo-gorgon' → 'D2D-Demo-gorgon'"""
    return re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-")


class WorkspaceManager:
    def __init__(self, config: Config, project_slug: Optional[str] = None):
        self._config = config
        self._base = Path(config.workflow["workspace"]["base_dir"])
        self._base.mkdir(parents=True, exist_ok=True)
        # When set, block worktrees use a shared main/ dir; non-blocks group under
        # {base}/{project_slug}/issues/{issue_id}.
        # When None, falls back to {base}/{team_prefix}/{issue_id} (team-level polling).
        self._project_slug = project_slug

    # ── Public API ────────────────────────────────────────────────────────────

    def create(self, issue_id: str, is_block: bool = False) -> Path:
        """
        Create a workspace for issue_id.

        For blocks (is_block=True, project scoped):
          - Returns the shared main/ worktree path (creates it on first call).
          - Creates issues/{issue_id}/ as a plain directory for per-block local data.
          - If main/ already exists, only updates .claude/settings.json with new ISSUE_ID.

        For all other issues:
          - Creates a git worktree at _path(issue_id) with branch agent/{issue_id}.
          - Idempotent: returns existing path if already created.
        """
        if is_block and self._project_slug:
            return self._create_block(issue_id)

        # Non-block (or no project slug): legacy per-issue worktree
        path = self._path(issue_id)
        branch = self._branch(issue_id)

        if path.exists():
            logger.info("workspace already exists issue=%s path=%s", issue_id, path)
            return path

        path.parent.mkdir(parents=True, exist_ok=True)
        if self._project_slug:
            self._ensure_project_root()
        self._git_worktree_add(path, branch)
        self._write_agent_config(path, issue_id)
        _ensure_log_dir()

        write_event(issue_id, "workspace_created", path=str(path), branch=branch)
        logger.info("workspace created issue=%s path=%s branch=%s", issue_id, path, branch)
        return path

    def remove(self, issue_id: str, is_block: bool = False) -> None:
        """
        Remove the workspace for issue_id.

        For blocks (is_block=True, project scoped):
          - Removes only the issues/{issue_id}/ plain directory.
          - Does NOT touch main/ — other blocks or future runs need it.

        For all other issues:
          - Removes the git worktree and deletes its branch.
          - Safe to call on a missing workspace.
        """
        if is_block and self._project_slug:
            issue_dir = self._base / self._project_slug / "issues" / issue_id
            if issue_dir.exists():
                try:
                    shutil.rmtree(issue_dir)
                    write_event(issue_id, "workspace_removed", path=str(issue_dir))
                    logger.info("block issue dir removed issue=%s", issue_id)
                except Exception as e:
                    logger.warning("block issue dir removal failed issue=%s: %s", issue_id, e)
            return

        # Non-block: remove git worktree
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

    def issue_path(self, issue_id: str) -> Path:
        """Return the per-block local data directory for issue_id.

        When project_slug is set: workspaces/{project_slug}/issues/{issue_id}
        Otherwise falls back to _path(issue_id) (legacy).
        """
        if self._project_slug:
            return self._base / self._project_slug / "issues" / issue_id
        return self._path(issue_id)

    def exists(self, issue_id: str) -> bool:
        return self._path(issue_id).exists()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _create_block(self, issue_id: str) -> Path:
        """Create or reuse the shared main/ worktree for block issues."""
        main_path = self._base / self._project_slug / "main"
        issue_path = self._base / self._project_slug / "issues" / issue_id
        branch = f"agent/{self._project_slug.lower()}"

        # Always create the per-block local data directory
        issue_path.mkdir(parents=True, exist_ok=True)

        if main_path.exists():
            # Shared worktree already exists — update settings.json with new ISSUE_ID
            self._write_agent_config(
                main_path, issue_id,
                issue_path=issue_path,
                main_path=main_path,
            )
            write_event(issue_id, "workspace_ready", path=str(main_path), branch=branch)
            logger.info("shared workspace ready issue=%s main=%s", issue_id, main_path)
            return main_path

        # First block for this project — create the shared worktree
        self._ensure_project_root()
        self._git_worktree_add(main_path, branch)
        self._write_agent_config(
            main_path, issue_id,
            issue_path=issue_path,
            main_path=main_path,
        )
        _ensure_log_dir()

        write_event(issue_id, "workspace_created", path=str(main_path), branch=branch)
        logger.info("shared workspace created issue=%s main=%s branch=%s", issue_id, main_path, branch)
        return main_path

    @staticmethod
    def _team_prefix(issue_id: str) -> str:
        return issue_id.split("-")[0] if "-" in issue_id else issue_id

    def _path(self, issue_id: str) -> Path:
        if self._project_slug:
            return self._base / self._project_slug / "issues" / issue_id
        # Fallback: team_prefix/issue_id — matches legacy structure for unscoped polling
        team_prefix = self._team_prefix(issue_id)
        return self._base / team_prefix / issue_id

    def _ensure_project_root(self) -> None:
        """Create project directory and write a PROJECT marker on first use."""
        project_dir = self._base / self._project_slug
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "issues").mkdir(exist_ok=True)
        marker = project_dir / "PROJECT"
        if not marker.exists():
            marker.write_text(
                f"project: {self._project_slug}\n"
                f"created: {datetime.now(timezone.utc).isoformat()}\n"
            )

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

    def _write_agent_config(
        self,
        worktree_path: Path,
        issue_id: str,
        issue_path: Optional[Path] = None,
        main_path: Optional[Path] = None,
    ) -> None:
        """
        Write a minimal .claude/settings.json into the worktree.
        Uses absolute paths for plugin dirs so depth doesn't matter.

        For block workspaces, also injects ISSUE_PATH and MAIN_PATH env vars
        so the agent knows where its local scratch space is and where the shared
        codebase lives.
        """
        claude_dir = worktree_path / ".claude"
        claude_dir.mkdir(exist_ok=True)

        repo_root = Path.cwd().resolve()
        agent_cfg = self._config.workflow["workspace"]["agent_config"]

        # Resolve repo-root-relative paths to absolute — depth-independent
        plugin_dirs = [str(repo_root / p) for p in agent_cfg["plugin_dirs"]]
        mcp_config = str(repo_root / agent_cfg["mcp_config"])

        env: dict = {"ISSUE_ID": issue_id}
        if issue_path is not None:
            env["ISSUE_PATH"] = str(issue_path)
        if main_path is not None:
            env["MAIN_PATH"] = str(main_path)

        settings = {
            "pluginDirs": plugin_dirs,
            "mcpConfig": mcp_config,
            "permissions": {
                "allow": [
                    "mcp__*",
                    "Bash(*)",
                    "Read(*)",
                    "Write(*)",
                    "Edit(*)",
                    "MultiEdit(*)",
                    "Glob(*)",
                    "Grep(*)",
                    "WebSearch(*)",
                    "WebFetch(*)",
                    "TodoWrite(*)",
                ],
            },
            "env": env,
        }
        settings_path = claude_dir / "settings.json"
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)

        # Symlink shared memory so workers can read standards and write reports.
        # Absolute path — resolves correctly regardless of worktree nesting depth.
        memory_link = claude_dir / "memory"
        if not memory_link.exists():
            memory_link.symlink_to(repo_root / ".claude" / "memory")


def _ensure_log_dir() -> None:
    Path("runs/logs").mkdir(parents=True, exist_ok=True)


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True, text=True)
