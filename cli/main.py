"""
resonance — Resonance orchestrator CLI

Usage examples:
  resonance setup                                    first-time configuration wizard
  resonance doctor                                   health check

  resonance status                                   all active runs
  resonance status QO-123                            detail for one run
  resonance logs QO-123                              recent events

  resonance approve QO-123                           resume a waiting run
  resonance feedback QO-123 "use primary button"     send feedback to agent
  resonance pause QO-123                             pause a run
  resonance abort QO-123                             stop permanently
  resonance attach QO-123                            print worktree + log paths
  resonance checkpoint QO-123                        write RESONANCE.md to worktree
  resonance checkpoint QO-123 --push                 write RESONANCE.md and push branch

  resonance watch                                    TUI dashboard (Milestone 2)
"""
import os
import re
import sys
from pathlib import Path
from typing import Optional

# Matches: linear.app/workspace/team/KEY/anything
_LINEAR_TEAM_URL_RE = re.compile(r'linear\.app/[\w-]+/team/([A-Z0-9]+)', re.IGNORECASE)

import typer
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Load .env before any orchestrator imports so env vars are available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from orchestrator import state as run_state
from orchestrator.events import tail as events_tail
from orchestrator.state import post_command
from orchestrator import memory as issue_memory

app = typer.Typer(name="resonance", help="Resonance orchestrator control", add_completion=False)
console = Console()


# ── setup ──────────────────────────────────────────────────────────────────────

@app.command()
def setup(
    non_interactive: bool = typer.Option(
        False, "--non-interactive", "-n",
        help="Skip prompts and only validate existing env vars (for CI)"
    )
):
    """Configure credentials and create required Linear states and labels."""
    console.print(Panel.fit("[bold]Resonance Setup[/bold]", border_style="cyan"))
    console.print()
    console.print("  You'll need:")
    console.print("  [dim]1. A Linear API key   — takes 30 seconds to create[/dim]")
    console.print("  [dim]2. A Linear team      — the team Resonance will watch[/dim]")
    console.print("  [dim]3. A Linear project   — optional: scope to one project within the team[/dim]")
    console.print("  [dim]4. Figma token        — optional, only for design tasks[/dim]")
    console.print("  [dim]5. GitHub token       — optional, only for auto PR creation[/dim]")
    console.print()

    env_path = Path(".env")
    env_values: dict[str, str] = {}

    # Load existing .env values as defaults
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env_values[k.strip()] = v.strip()

    # ── Step 1: Linear API key ────────────────────────────────────────────────
    console.print("[bold]Step 1/5[/bold]  Linear API key")
    console.print("  [dim]Where to get it:[/dim]")
    console.print("    [dim]Linear → Settings → API → Personal API keys → Create key[/dim]")
    console.print("    [dim]Direct URL: https://linear.app/settings/api[/dim]")
    console.print("  [dim]Format: lin_api_...[/dim]")
    console.print()

    api_key = os.environ.get("LINEAR_API_KEY") or env_values.get("LINEAR_API_KEY", "")
    # Treat placeholder-only value as unset
    if api_key == "lin_api_":
        api_key = ""

    if not api_key and not non_interactive:
        api_key = typer.prompt("  LINEAR_API_KEY")
    elif api_key:
        masked = api_key[:12] + "…"
        console.print(f"  [dim]Using existing key:[/dim] {masked}")

    if not api_key:
        console.print("  [red]✗ LINEAR_API_KEY not set — aborting[/red]")
        raise typer.Exit(1)

    # Validate key
    try:
        from orchestrator.linear_client import LinearClient
        client = LinearClient(api_key)
        viewer = client.get_viewer()
        console.print(f"  [green]✓[/green] Authenticated as [bold]{viewer['name']}[/bold] ({viewer['email']})")
        env_values["LINEAR_API_KEY"] = api_key
    except Exception as e:
        console.print(f"  [red]✗ Linear API key invalid:[/red] {e}")
        raise typer.Exit(1)

    # ── Step 2: Team ──────────────────────────────────────────────────────────
    console.print()
    console.print("[bold]Step 2/5[/bold]  Linear team")
    console.print("  [dim]Resonance watches a Linear team. You can scope it to a project in the next step.[/dim]")
    console.print("  [dim]Fetching your teams…[/dim]")
    console.print()

    team_id = (
        os.environ.get("LINEAR_TEAM_ID")
        or env_values.get("LINEAR_TEAM_ID", "")
    )

    if not team_id and not non_interactive:
        try:
            teams = client.get_teams()
            if not teams:
                console.print("  [yellow]No teams found on this account.[/yellow]")
                raise typer.Exit(1)

            for i, t in enumerate(teams, 1):
                console.print(f"  [bold cyan]{i:2d}[/bold cyan]  {t['name']}  [dim][{t['key']}][/dim]")
            console.print()
            console.print("  [dim]You can also paste a team URL, e.g.:[/dim]")
            console.print("  [dim]https://linear.app/queen-one/team/RND/all[/dim]")
            console.print()
            raw = typer.prompt("  Type a number or paste a team URL").strip()

            # URL paste — extract team key and match against fetched teams
            url_match = _LINEAR_TEAM_URL_RE.search(raw)
            if url_match:
                key = url_match.group(1).upper()
                matched = next((t for t in teams if t["key"].upper() == key), None)
                if matched:
                    team_id = matched["id"]
                    console.print(f"  [dim]Resolved {key} → {matched['name']}[/dim]")
                else:
                    console.print(f"  [red]✗ Team key '{key}' not found in your workspace.[/red]")
                    raise typer.Exit(1)
            elif raw.isdigit() and 1 <= int(raw) <= len(teams):
                team_id = teams[int(raw) - 1]["id"]
            else:
                team_id = raw  # treat as direct UUID

        except typer.Exit:
            raise
        except Exception as exc:
            console.print(f"  [red]✗ Could not fetch teams:[/red] {exc}")
            raise typer.Exit(1)
    elif team_id:
        console.print(f"  [dim]Using existing team ID:[/dim] {team_id[:8]}…")

    if not team_id:
        console.print("  [red]✗ LINEAR_TEAM_ID not set — aborting[/red]")
        raise typer.Exit(1)

    try:
        team_obj = client.get_team(team_id)
        if not team_obj:
            console.print(f"  [red]✗ Team not found: {team_id}[/red]")
            raise typer.Exit(1)
        console.print(f"  [green]✓[/green] Team: [bold]{team_obj['name']}[/bold]  [dim][{team_obj['key']}][/dim]")
        env_values["LINEAR_TEAM_ID"] = team_id
        team = team_obj
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"  [red]✗ Could not load team:[/red] {e}")
        raise typer.Exit(1)

    # ── Step 3: Project (optional) ────────────────────────────────────────────
    console.print()
    console.print("[bold]Step 3/5[/bold]  Linear project  [dim](optional)[/dim]")
    console.print("  [dim]Scope Resonance to a specific project within the team.[/dim]")
    console.print("  [dim]Leave blank to watch all team issues.[/dim]")
    console.print()

    project_id = (
        os.environ.get("LINEAR_PROJECT_ID")
        or env_values.get("LINEAR_PROJECT_ID", "")
    )

    if not non_interactive:
        try:
            projects = client.get_projects(team_id)
        except Exception as exc:
            console.print(f"  [yellow]⚠[/yellow] Could not fetch projects: {exc}")
            projects = []

        if projects:
            for i, p in enumerate(projects, 1):
                console.print(f"  [bold cyan]{i:2d}[/bold cyan]  {p['name']}")
            console.print()

        if project_id:
            console.print(f"  [dim]Using existing project ID:[/dim] {project_id[:8]}…")
            try:
                proj_obj = client.get_project(project_id)
                if proj_obj:
                    console.print(f"  [green]✓[/green] Project: [bold]{proj_obj['name']}[/bold]")
                    env_values["LINEAR_PROJECT_ID"] = project_id
                else:
                    console.print(f"  [yellow]⚠[/yellow] Project ID not found — clearing it")
                    project_id = ""
                    env_values.pop("LINEAR_PROJECT_ID", None)
            except Exception as exc:
                console.print(f"  [yellow]⚠[/yellow] Could not verify project: {exc}")
        else:
            if projects:
                raw = typer.prompt("  Number or project UUID (Enter to skip)", default="").strip()
            else:
                raw = typer.prompt("  Project UUID (Enter to skip)", default="").strip()

            if raw:
                if raw.isdigit() and 1 <= int(raw) <= len(projects):
                    project_id = projects[int(raw) - 1]["id"]
                    project_name = projects[int(raw) - 1]["name"]
                    console.print(f"  [green]✓[/green] Project: [bold]{project_name}[/bold]")
                else:
                    project_id = raw  # treat as UUID
                    console.print(f"  [dim]Using:[/dim] {project_id[:8]}…")
                env_values["LINEAR_PROJECT_ID"] = project_id
            else:
                console.print("  [dim]–[/dim] Skipped — watching all team issues")
                env_values.pop("LINEAR_PROJECT_ID", None)
    else:
        if project_id:
            console.print(f"  [dim]LINEAR_PROJECT_ID set:[/dim] {project_id[:8]}…")
            env_values["LINEAR_PROJECT_ID"] = project_id
        else:
            console.print("  [dim]–[/dim] LINEAR_PROJECT_ID not set (optional)")

    # ── Step 4: Linear states and labels ─────────────────────────────────────
    console.print()
    console.print("[bold]Step 4/5[/bold]  Linear workflow states")
    console.print("  [dim]Checking what exists and creating any missing Resonance states...[/dim]")
    console.print()

    existing_state_env = {
        "eligibility": env_values.get("LINEAR_STATE_ELIGIBILITY"),
        "in_progress": env_values.get("LINEAR_STATE_IN_PROGRESS"),
        "feedback":    env_values.get("LINEAR_STATE_FEEDBACK"),
        "review":      env_values.get("LINEAR_STATE_REVIEW"),
        "return":      env_values.get("LINEAR_STATE_RETURN"),
    }
    state_mapping = _ensure_states(client, team_id, non_interactive, existing_state_env)

    _ENV_KEY_FOR_ROLE = {
        "eligibility": "LINEAR_STATE_ELIGIBILITY",
        "in_progress": "LINEAR_STATE_IN_PROGRESS",
        "feedback":    "LINEAR_STATE_FEEDBACK",
        "review":      "LINEAR_STATE_REVIEW",
        "return":      "LINEAR_STATE_RETURN",
    }
    for role, env_key in _ENV_KEY_FOR_ROLE.items():
        if role in state_mapping:
            env_values[env_key] = state_mapping[role]

    console.print()
    console.print("  [dim]Creating issue labels:[/dim]")
    console.print()
    _ensure_labels(client, team_id)

    # ── Step 5: Optional credentials ─────────────────────────────────────────
    console.print()
    console.print("[bold]Step 5/5[/bold]  Optional credentials")

    if not non_interactive:
        figma_key = os.environ.get("FIGMA_API_KEY") or env_values.get("FIGMA_API_KEY", "")
        if not figma_key:
            console.print("  [dim]Figma API key — only needed for design_to_code tasks (Figma → code).[/dim]")
            console.print("  [dim]Where to get it: Figma → Settings → Account → Personal access tokens[/dim]")
            console.print("  [dim]Direct URL: https://www.figma.com/settings[/dim]")
            figma_input = typer.prompt("  FIGMA_API_KEY (press Enter to skip)", default="")
            if figma_input.strip():
                env_values["FIGMA_API_KEY"] = figma_input.strip()
                console.print("  [green]✓[/green] FIGMA_API_KEY saved")
            else:
                console.print("  [dim]–[/dim] Skipped")
        else:
            console.print(f"  [green]✓[/green] FIGMA_API_KEY already set")

        console.print()
        github_token = os.environ.get("GITHUB_TOKEN") or env_values.get("GITHUB_TOKEN", "")
        if not github_token:
            console.print("  [dim]GitHub token — only needed for automated PR creation (Milestone 3, not required now).[/dim]")
            console.print("  [dim]Where to get it: GitHub → Settings → Developer settings → Personal access tokens[/dim]")
            console.print("  [dim]Direct URL: https://github.com/settings/tokens — scopes needed: repo[/dim]")
            gh_input = typer.prompt("  GITHUB_TOKEN (press Enter to skip)", default="")
            if gh_input.strip():
                env_values["GITHUB_TOKEN"] = gh_input.strip()
                console.print("  [green]✓[/green] GITHUB_TOKEN saved")
            else:
                console.print("  [dim]–[/dim] Skipped")
        else:
            console.print(f"  [green]✓[/green] GITHUB_TOKEN already set")
    else:
        for var in ("FIGMA_API_KEY", "GITHUB_TOKEN"):
            val = os.environ.get(var)
            if val:
                console.print(f"  [green]✓[/green] {var} set")
            else:
                console.print(f"  [dim]–[/dim] {var} not set (optional)")

    # ── Write .env ────────────────────────────────────────────────────────────
    if not non_interactive:
        console.print()
        _write_env(env_path, env_values)

    client.close()
    console.print()
    console.print("[bold green]✓ Setup complete.[/bold green]")
    console.print()
    console.print("  Start the orchestrator:")
    console.print("    [bold]./onair.sh[/bold]")
    console.print()


def _ensure_states(
    client,
    team_id: str,
    non_interactive: bool,
    existing_env: dict,
) -> dict:
    """
    Ensure Resonance workflow states exist. Returns {role: actual_state_name}.
    If a state cannot be created (no admin), prompts the user to map to an existing state.
    existing_env: {role: currently-configured state name} loaded from .env.
    """
    from orchestrator.linear_client import STATES_TO_CREATE, STATES_STANDARD

    all_states = client.get_team_states(team_id)
    existing_names = {s["name"] for s in all_states}

    mapping: dict[str, str] = {}
    need_mapping: list[dict] = []

    # Standard states — verify they exist, no creation needed
    for s in STATES_STANDARD:
        role, default = s["role"], s["default"]
        configured = existing_env.get(role) or default
        if configured in existing_names:
            console.print(f"  [dim]–[/dim] {configured}")
            mapping[role] = configured
        elif default in existing_names:
            console.print(f"  [dim]–[/dim] {default}")
            mapping[role] = default
        else:
            fallback = all_states[0]["name"] if all_states else default
            console.print(f"  [yellow]⚠[/yellow] '{default}' not found — using '{fallback}'")
            mapping[role] = fallback

    # Resonance-specific states — try to create, fall back to user mapping
    for s in STATES_TO_CREATE:
        role = s["role"]
        default = s["default"]
        configured = existing_env.get(role)

        # Already configured and the state exists
        if configured and configured in existing_names:
            console.print(f"  [dim]–[/dim] {configured}")
            mapping[role] = configured
            continue

        # Default name already exists in the team
        if default in existing_names:
            console.print(f"  [dim]–[/dim] {default} (already exists)")
            mapping[role] = default
            continue

        # Try to create it
        try:
            client.create_state(team_id, default, s["color"], s["type"])
            console.print(f"  [green]✓[/green] Created: {default}")
            mapping[role] = default
        except Exception as e:
            if non_interactive:
                console.print(f"  [red]✗[/red] Cannot create '{default}': {e}")
                mapping[role] = configured or default
            else:
                console.print(f"  [yellow]⚠[/yellow] Cannot create '{default}' (permission denied) — needs manual mapping")
                need_mapping.append(s)

    # Interactive fallback for states that couldn't be created
    if need_mapping:
        console.print()
        console.print("  [dim]Resonance can't create states in this team (admin access required).[/dim]")
        console.print("  [dim]Pick an existing state to use for each role:[/dim]")
        console.print()

        sorted_states = sorted(all_states, key=lambda x: x["name"])
        for i, st in enumerate(sorted_states, 1):
            console.print(f"  [bold cyan]{i:2d}[/bold cyan]  {st['name']}  [dim][{st['type']}][/dim]")
        console.print()

        for s in need_mapping:
            role = s["role"]
            console.print(f"  [bold]{s['default']}[/bold]  — [dim]{s['description']}[/dim]")
            raw = typer.prompt("  Number or state name").strip()
            if raw.isdigit() and 1 <= int(raw) <= len(sorted_states):
                chosen = sorted_states[int(raw) - 1]["name"]
            else:
                chosen = raw
            mapping[role] = chosen
            console.print(f"  [green]→[/green] Mapped to: [bold]{chosen}[/bold]")
            console.print()

    return mapping


def _ensure_labels(client, team_id: str) -> None:
    from orchestrator.linear_client import REQUIRED_LABELS
    existing = {l["name"].lower() for l in client.get_team_labels(team_id)}
    for label in REQUIRED_LABELS:
        if label["name"].lower() in existing:
            console.print(f"  [dim]–[/dim] {label['name']} (already exists)")
        else:
            try:
                client.create_label(team_id, label["name"], label["color"])
                console.print(f"  [green]✓[/green] Created label: {label['name']}")
            except Exception as e:
                console.print(f"  [yellow]⚠[/yellow] Could not create '{label['name']}': {e}")


def _write_env(env_path: Path, values: dict) -> None:
    COMMENT_HEADER = (
        "# Resonance — environment configuration\n"
        "# Generated by: resonance setup\n"
        "# Do not commit this file.\n\n"
    )
    VAR_ORDER = [
        "LINEAR_API_KEY",
        "LINEAR_TEAM_ID",
        "LINEAR_PROJECT_ID",
        "LINEAR_STATE_ELIGIBILITY",
        "LINEAR_STATE_IN_PROGRESS",
        "LINEAR_STATE_FEEDBACK",
        "LINEAR_STATE_REVIEW",
        "LINEAR_STATE_RETURN",
        "FIGMA_API_KEY",
        "GITHUB_TOKEN",
    ]
    lines = [COMMENT_HEADER]
    written = set()
    for key in VAR_ORDER:
        if key in values:
            lines.append(f"{key}={values[key]}\n")
            written.add(key)
    # Append any extra vars not in the standard order
    for key, val in values.items():
        if key not in written:
            lines.append(f"{key}={val}\n")

    env_path.write_text("".join(lines))
    console.print(f"  [green]✓[/green] Wrote [bold].env[/bold]")


# ── doctor ─────────────────────────────────────────────────────────────────────

@app.command()
def doctor():
    """Verify all credentials, dependencies, and Linear configuration."""
    console.print(Panel.fit("[bold]Resonance Doctor[/bold]", border_style="cyan"))
    console.print()

    all_ok = True

    # ── Dependencies ──────────────────────────────────────────────────────────
    console.print("[bold]Dependencies[/bold]")
    deps = ["httpx", "typer", "rich", "yaml", "dotenv"]
    for dep in deps:
        mod = "yaml" if dep == "yaml" else dep.replace("-", "_")
        try:
            __import__(mod)
            _ok(dep)
        except ImportError:
            _fail(dep, "not installed — run: pip install -e .")
            all_ok = False

    # ── WORKFLOW.md ────────────────────────────────────────────────────────────
    console.print()
    console.print("[bold]Configuration[/bold]")
    workflow_path = Path("WORKFLOW.md")
    if workflow_path.exists():
        try:
            import yaml
            with open(workflow_path) as f:
                yaml.safe_load(f)
            _ok("WORKFLOW.md (valid YAML)")
        except Exception as e:
            _fail("WORKFLOW.md", f"parse error: {e}")
            all_ok = False
    else:
        _fail("WORKFLOW.md", "not found")
        all_ok = False

    # ── Credentials ────────────────────────────────────────────────────────────
    console.print()
    console.print("[bold]Credentials[/bold]")

    api_key = os.environ.get("LINEAR_API_KEY", "").strip()
    team_id = os.environ.get("LINEAR_TEAM_ID", "").strip()
    project_id = os.environ.get("LINEAR_PROJECT_ID", "").strip() or None

    if not api_key:
        _fail("LINEAR_API_KEY", "not set — run: resonance setup")
        all_ok = False
    if not team_id:
        _fail("LINEAR_TEAM_ID", "not set — run: resonance setup")
        all_ok = False

    if not api_key or not team_id:
        console.print()
        if not all_ok:
            console.print("[red]✗ Issues found — run: resonance setup[/red]")
        raise typer.Exit(1 if not all_ok else 0)

    # ── Linear API ────────────────────────────────────────────────────────────
    try:
        from orchestrator.linear_client import LinearClient, REQUIRED_LABELS
        client = LinearClient(api_key)

        viewer = client.get_viewer()
        _ok(f"LINEAR_API_KEY (authenticated as {viewer['name']})")

        team_obj = client.get_team(team_id)
        if team_obj:
            _ok(f"LINEAR_TEAM_ID ({team_obj['name']} [{team_obj['key']}])")
        else:
            _fail("LINEAR_TEAM_ID", f"team not found: {team_id}")
            all_ok = False
            team_id = None

        # ── Linear project (optional) ──────────────────────────────────────
        if project_id:
            try:
                proj_obj = client.get_project(project_id)
                if proj_obj:
                    _ok(f"LINEAR_PROJECT_ID ({proj_obj['name']})")
                else:
                    _fail("LINEAR_PROJECT_ID", f"project not found — run: resonance setup")
                    all_ok = False
            except Exception as exc:
                _warn("LINEAR_PROJECT_ID", f"could not verify: {exc}")
        else:
            _warn("LINEAR_PROJECT_ID", "not set — watching all team issues (optional: set to scope to a project)")

        figma_key = os.environ.get("FIGMA_API_KEY")
        if figma_key:
            _ok("FIGMA_API_KEY (set)")
        else:
            _warn("FIGMA_API_KEY", "not set (optional — needed for design_to_code tasks)")

        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            _ok("GITHUB_TOKEN (set)")
        else:
            _warn("GITHUB_TOKEN", "not set (optional — needed for PR creation)")

        # ── Linear states ──────────────────────────────────────────────────
        if team_id:
            console.print()
            console.print("[bold]Linear workflow states[/bold]")
            existing_states = {s["name"] for s in client.get_team_states(team_id)}

            state_checks = [
                ("LINEAR_STATE_ELIGIBILITY", os.environ.get("LINEAR_STATE_ELIGIBILITY", "Plan Approved"),         "trigger — authorize agent work"),
                ("LINEAR_STATE_IN_PROGRESS", os.environ.get("LINEAR_STATE_IN_PROGRESS", "In Progress"),           "set when work starts"),
                ("LINEAR_STATE_FEEDBACK",    os.environ.get("LINEAR_STATE_FEEDBACK",    "Agent Feedback Needed"), "set when agent needs input"),
                ("LINEAR_STATE_REVIEW",      os.environ.get("LINEAR_STATE_REVIEW",      "Human Review"),          "set when agent finishes"),
                ("LINEAR_STATE_RETURN",      os.environ.get("LINEAR_STATE_RETURN",      "Todo"),                  "set on failure"),
            ]
            for env_key, state_name, role_desc in state_checks:
                if state_name in existing_states:
                    _ok(f"{state_name}  [dim]({role_desc})[/dim]")
                else:
                    _fail(state_name, f"not found in team — run: [bold]resonance fix[/bold]")
                    all_ok = False

            console.print()
            console.print("[bold]Linear labels[/bold]")
            existing_labels = {l["name"].lower() for l in client.get_team_labels(team_id)}
            for label in REQUIRED_LABELS:
                if label["name"].lower() in existing_labels:
                    _ok(label["name"])
                else:
                    _fail(label["name"], "missing — run: [bold]resonance fix[/bold]")
                    all_ok = False

        client.close()

    except Exception as e:
        _fail("Linear API", str(e))
        all_ok = False

    # ── MCP ────────────────────────────────────────────────────────────────────
    console.print()
    console.print("[bold]MCP servers[/bold]")
    mcp_path = Path(".mcp.json")
    if mcp_path.exists():
        try:
            import json as _json
            mcp_cfg = _json.loads(mcp_path.read_text())
            servers = mcp_cfg.get("mcpServers", mcp_cfg)
            if "linear" in servers:
                # Warn if any env values are unexpanded ${...} placeholders
                import re as _re
                linear_env = servers["linear"].get("env", {})
                bad = [k for k, v in linear_env.items() if isinstance(v, str) and _re.search(r"\$\{", v)]
                if bad:
                    _warn("MCP linear", f"env fields contain unexpanded variables ({', '.join(bad)}) — run: ./wizard.sh check")
                    all_ok = False
                else:
                    _ok("MCP linear server (auth via LINEAR_ACCESS_TOKEN injected at runtime)")
            else:
                _fail("MCP linear", "not found in .mcp.json — agents will have no Linear access")
                all_ok = False
            if "figma" in servers:
                _ok("MCP figma server")
            else:
                figma_key = os.environ.get("FIGMA_API_KEY")
                if figma_key:
                    _warn("MCP figma", "not in .mcp.json but FIGMA_API_KEY is set — run: ./wizard.sh check")
                else:
                    _warn("MCP figma", "not configured (optional — needed for design_to_code tasks)")
        except Exception as e:
            _fail(".mcp.json", f"parse error: {e}")
            all_ok = False
    else:
        _fail(".mcp.json", "not found — run: cp .mcp.json.example .mcp.json  then resonance setup")
        all_ok = False

    # ── Summary ───────────────────────────────────────────────────────────────
    console.print()
    if all_ok:
        console.print("[bold green]✓ All checks passed.[/bold green]")
        console.print("  Ready to run: [bold]./onair.sh[/bold]")
    else:
        console.print("[bold red]✗ Some checks failed.[/bold red]")
        console.print()
        console.print("  Quick fixes:")
        console.print("    [bold]resonance fix[/bold]          — create missing labels and workflow states")
        console.print("    [bold]resonance setup[/bold]        — full configuration wizard (credentials + Linear)")
        console.print("    [bold]./wizard.sh check[/bold]       — full health-check wizard (auto-fixes MCP, deps)")
        console.print("    [bold]./wizard.sh update[/bold]      — update a specific API key")

    raise typer.Exit(0 if all_ok else 1)


def _ok(label: str) -> None:
    console.print(f"  [green]✓[/green] {label}")

def _fail(label: str, detail: str) -> None:
    console.print(f"  [red]✗[/red] {label} — [dim]{detail}[/dim]")

def _warn(label: str, detail: str) -> None:
    console.print(f"  [yellow]–[/yellow] {label} — [dim]{detail}[/dim]")


# ── fix ────────────────────────────────────────────────────────────────────────

@app.command()
def fix():
    """Auto-create any missing Linear labels and workflow states. No wizard — just fixes."""
    from orchestrator.linear_client import LinearClient, REQUIRED_LABELS, STATES_TO_CREATE
    from orchestrator.config import load_config

    console.print(Panel.fit("[bold]Resonance Fix[/bold]", border_style="cyan"))
    console.print()

    try:
        cfg = load_config()
    except ValueError as e:
        console.print(f"  [red]✗[/red] Config error: {e}")
        console.print("  Run [bold]resonance setup[/bold] first to set credentials.")
        raise typer.Exit(1)

    try:
        client = LinearClient(cfg.linear_api_key)
        viewer = client.get_viewer()
        console.print(f"  Connected as [bold]{viewer['name']}[/bold] ({viewer['email']})")
    except Exception as e:
        console.print(f"  [red]✗[/red] Cannot connect to Linear: {e}")
        raise typer.Exit(1)

    team_id = cfg.linear_team_id
    fixed = 0
    failed = 0

    # ── Labels ────────────────────────────────────────────────────────────────
    console.print()
    console.print("[bold]Labels[/bold]")
    existing_labels = {l["name"].lower() for l in client.get_team_labels(team_id)}
    for label in REQUIRED_LABELS:
        if label["name"].lower() in existing_labels:
            console.print(f"  [dim]–[/dim] {label['name']} (already exists)")
        else:
            try:
                client.create_label(team_id, label["name"], label["color"])
                console.print(f"  [green]✓[/green] Created label: [bold]{label['name']}[/bold]")
                fixed += 1
            except Exception as e:
                console.print(f"  [red]✗[/red] Could not create '{label['name']}': {e}")
                failed += 1

    # ── Workflow states ────────────────────────────────────────────────────────
    console.print()
    console.print("[bold]Workflow states[/bold]")
    existing_states = {s["name"] for s in client.get_team_states(team_id)}
    for s in STATES_TO_CREATE:
        name = s["default"]
        if name in existing_states:
            console.print(f"  [dim]–[/dim] {name} (already exists)")
        else:
            try:
                client.create_state(team_id, name, s["color"], s["type"])
                console.print(f"  [green]✓[/green] Created state: [bold]{name}[/bold]  [dim]({s['description']})[/dim]")
                fixed += 1
            except Exception as e:
                console.print(
                    f"  [yellow]⚠[/yellow] Could not create '{name}': {e}\n"
                    f"        [dim]You may need admin access — create it manually in Linear,[/dim]\n"
                    f"        [dim]then run [bold]resonance setup[/bold] to map it.[/dim]"
                )
                failed += 1

    client.close()

    # ── Summary ───────────────────────────────────────────────────────────────
    console.print()
    if fixed == 0 and failed == 0:
        console.print("[bold green]✓ Nothing to fix — everything is already set up.[/bold green]")
    elif failed == 0:
        console.print(f"[bold green]✓ Fixed {fixed} item{'s' if fixed != 1 else ''}.[/bold green]")
    else:
        console.print(f"[yellow]⚠ Fixed {fixed}, could not fix {failed}.[/yellow]")
        console.print()
        console.print("  The items above marked [red]✗[/red] require admin access in your Linear workspace.")
        console.print("  Create them manually:")
        console.print("    Linear → Settings → Labels  (for missing labels)")
        console.print("    Linear → Settings → Workflow states  (for missing states)")
        console.print("  Then run [bold]resonance setup[/bold] if the names differ from defaults.")
        raise typer.Exit(1)


# ── status ─────────────────────────────────────────────────────────────────────

@app.command()
def status(issue_id: Optional[str] = typer.Argument(None, help="Issue identifier e.g. QO-123")):
    """Show status of active runs (or a specific run)."""
    if issue_id:
        run = run_state.get_run(issue_id)
        if not run:
            console.print(f"[yellow]No run found for {issue_id}[/yellow]")
            raise typer.Exit(1)
        _print_run_detail(issue_id, run)
    else:
        all_runs = run_state.get_all_runs()
        if not all_runs:
            console.print("[dim]No runs on record.[/dim]")
            return
        _print_runs_table(all_runs)


def _print_runs_table(runs: dict) -> None:
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Issue", style="cyan", width=10)
    table.add_column("Status", width=18)
    table.add_column("Task Type", width=20)
    table.add_column("Attempt", width=8)
    table.add_column("Last Event")

    STATUS_STYLE = {
        "running": "green",
        "waiting_human": "yellow",
        "paused": "dim yellow",
        "complete": "dim green",
        "failed": "red",
        "archived": "dim",
    }

    for issue_id, run in sorted(runs.items()):
        status_str = run.get("status", "?")
        style = STATUS_STYLE.get(status_str, "")
        table.add_row(
            issue_id,
            f"[{style}]{status_str}[/{style}]" if style else status_str,
            run.get("task_type", "?"),
            str(run.get("attempt", 1)),
            _short_ts(run.get("last_event_at", "")),
        )

    console.print(table)


def _print_run_detail(issue_id: str, run: dict) -> None:
    console.print(f"\n[bold cyan]{issue_id}[/bold cyan]")
    fields = [
        ("Status", run.get("status")),
        ("Task type", run.get("task_type")),
        ("Worker", run.get("worker")),
        ("Branch", run.get("branch")),
        ("Iteration", run.get("iteration")),
        ("Attempt", run.get("attempt")),
        ("Started", run.get("started_at", "")[:19].replace("T", " ")),
        ("Last event", _short_ts(run.get("last_event_at", ""))),
        ("Log file", run.get("log_file")),
    ]
    for label, value in fields:
        if value is not None:
            console.print(f"  [dim]{label}:[/dim] {value}")

    question = run.get("pending_question")
    if question:
        console.print(f"\n  [yellow]⏸ Pending question:[/yellow] {question}")

    artifacts = run.get("artifacts", {})
    if artifacts:
        console.print("\n  [green]Artifacts:[/green]")
        for k, v in artifacts.items():
            console.print(f"    {k}: {v}")

    console.print()


# ── approve ────────────────────────────────────────────────────────────────────

@app.command()
def approve(issue_id: str = typer.Argument(..., help="Issue identifier e.g. QO-123")):
    """Resume a run that is waiting for human approval."""
    run = run_state.get_run(issue_id)
    if not run:
        console.print(f"[red]No run found for {issue_id}[/red]")
        raise typer.Exit(1)
    if run["status"] not in {"waiting_human", "paused"}:
        console.print(f"[yellow]{issue_id} is not waiting for approval (status: {run['status']})[/yellow]")
        raise typer.Exit(1)

    post_command(issue_id, "approve")
    console.print(f"[green]✓ Approved {issue_id} — orchestrator will resume the run.[/green]")


# ── feedback ───────────────────────────────────────────────────────────────────

@app.command()
def feedback(
    issue_id: str = typer.Argument(..., help="Issue identifier e.g. QO-123"),
    text: str = typer.Argument(..., help="Feedback text to send to the agent"),
):
    """Send feedback to an agent without taking over the run."""
    run = run_state.get_run(issue_id)
    if not run:
        console.print(f"[red]No run found for {issue_id}[/red]")
        raise typer.Exit(1)

    post_command(issue_id, "feedback", text=text)
    console.print(f"[green]✓ Feedback queued for {issue_id}[/green]")
    console.print(f"  [dim]{text}[/dim]")


# ── pause ──────────────────────────────────────────────────────────────────────

@app.command()
def pause(issue_id: str = typer.Argument(..., help="Issue identifier e.g. QO-123")):
    """Pause an active run cleanly. Resume later with `resonance approve`."""
    run = run_state.get_run(issue_id)
    if not run:
        console.print(f"[red]No run found for {issue_id}[/red]")
        raise typer.Exit(1)
    if run["status"] != "running":
        console.print(f"[yellow]{issue_id} is not running (status: {run['status']})[/yellow]")
        raise typer.Exit(1)

    post_command(issue_id, "pause")
    console.print(f"[green]✓ Pause command queued for {issue_id}[/green]")


# ── abort ──────────────────────────────────────────────────────────────────────

@app.command()
def abort(
    issue_id: str = typer.Argument(..., help="Issue identifier e.g. QO-123"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Abort a run permanently. Workspace is preserved for inspection."""
    run = run_state.get_run(issue_id)
    if not run:
        console.print(f"[red]No run found for {issue_id}[/red]")
        raise typer.Exit(1)

    if not yes:
        confirm = typer.confirm(f"Abort {issue_id}? This cannot be undone.")
        if not confirm:
            raise typer.Abort()

    post_command(issue_id, "abort")
    console.print(f"[red]✗ Abort command queued for {issue_id}[/red]")


# ── logs ───────────────────────────────────────────────────────────────────────

@app.command()
def logs(
    issue_id: str = typer.Argument(..., help="Issue identifier e.g. QO-123"),
    tail: int = typer.Option(50, "--tail", "-n", help="Number of event lines to show"),
):
    """Show the most recent events for a run."""
    events = events_tail(tail)
    filtered = [e for e in events if e.get("issue") == issue_id]

    if not filtered:
        console.print(f"[dim]No events found for {issue_id}[/dim]")
        return

    for event in filtered:
        ts = _short_ts(event.get("ts", ""))
        etype = event.get("type", "?")
        extra = {k: v for k, v in event.items() if k not in {"ts", "issue", "type"}}
        extra_str = "  " + "  ".join(f"{k}={v}" for k, v in extra.items()) if extra else ""
        color = _event_color(etype)
        console.print(f"[dim]{ts}[/dim]  [{color}]{etype:<25}[/{color}]{extra_str}")


# ── project ────────────────────────────────────────────────────────────────────

_LINEAR_PROJECT_URL_RE = re.compile(r'/project/([^/?#]+)', re.IGNORECASE)

project_app = typer.Typer(name="project", help="Manage the active Linear project", add_completion=False)
app.add_typer(project_app)


@project_app.command("list")
def project_list():
    """List available Linear projects for the configured team."""
    from orchestrator.linear_client import LinearClient
    from orchestrator.config import load_config
    try:
        cfg = load_config()
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1)
    client = LinearClient(cfg.linear_api_key)
    try:
        projects = client.get_projects(cfg.linear_team_id)
    except Exception as e:
        console.print(f"[red]✗ Could not fetch projects:[/red] {e}")
        client.close()
        raise typer.Exit(1)
    if not projects:
        console.print("[dim]No projects found.[/dim]")
        client.close()
        return
    current = cfg.linear_project_id or ""
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("#",       width=4,  style="dim")
    table.add_column("Name",    width=32, style="bold cyan")
    table.add_column("ID",      width=12, style="dim")
    table.add_column("Active",  width=8)
    for i, p in enumerate(projects, 1):
        active = "[bold green]✓ active[/bold green]" if p["id"] == current else ""
        table.add_row(str(i), p["name"], p["id"][:8] + "…", active)
    console.print(table)
    client.close()


@project_app.command("set")
def project_set(
    url_or_id: Optional[str] = typer.Argument(None, help="Project URL, UUID, or number from list"),
):
    """Set the active project (writes LINEAR_PROJECT_ID to .env)."""
    from orchestrator.linear_client import LinearClient
    from orchestrator.config import load_config
    try:
        cfg = load_config()
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1)
    client = LinearClient(cfg.linear_api_key)

    try:
        projects = client.get_projects(cfg.linear_team_id)
    except Exception as e:
        console.print(f"[red]✗ Could not fetch projects:[/red] {e}")
        client.close()
        raise typer.Exit(1)

    project_id = None
    project_name = None

    if not url_or_id:
        # Interactive picker
        if not projects:
            console.print("[yellow]No projects found.[/yellow]")
            client.close()
            raise typer.Exit(1)
        for i, p in enumerate(projects, 1):
            console.print(f"  [bold cyan]{i:2d}[/bold cyan]  {p['name']}  [dim]{p['id'][:8]}…[/dim]")
        console.print()
        raw = typer.prompt("  Number or UUID (Enter to skip — watch all team issues)", default="").strip()
        if not raw:
            _env_remove_key(Path(".env"), "LINEAR_PROJECT_ID")
            console.print("  [dim]–[/dim] No project scope set — watching all team issues")
            client.close()
            return
        if raw.isdigit() and 1 <= int(raw) <= len(projects):
            p = projects[int(raw) - 1]
            project_id, project_name = p["id"], p["name"]
        else:
            url_or_id = raw

    if url_or_id and not project_id:
        # Try URL slug match
        url_match = _LINEAR_PROJECT_URL_RE.search(url_or_id)
        if url_match:
            slug = url_match.group(1)
            # Last hex segment of slug is a UUID prefix
            hex_parts = [p for p in slug.split("-") if all(c in "0123456789abcdef" for c in p)]
            hex_suffix = hex_parts[-1] if hex_parts else ""
            matched = next(
                (p for p in projects if hex_suffix and p["id"].replace("-", "").endswith(hex_suffix)),
                None,
            )
            if not matched:
                matched = next((p for p in projects if slug.lower() in p["name"].lower()), None)
            if matched:
                project_id, project_name = matched["id"], matched["name"]
            else:
                console.print(f"  [red]✗ No project matched URL slug:[/red] {slug}")
                client.close()
                raise typer.Exit(1)
        else:
            # Treat as UUID or name
            matched = next((p for p in projects if p["id"] == url_or_id), None)
            if not matched and url_or_id.isdigit():
                idx = int(url_or_id) - 1
                if 0 <= idx < len(projects):
                    matched = projects[idx]
            if matched:
                project_id, project_name = matched["id"], matched["name"]
            else:
                # Try direct API lookup
                try:
                    proj = client.get_project(url_or_id)
                    if proj:
                        project_id, project_name = proj["id"], proj["name"]
                except Exception:
                    pass
            if not project_id:
                console.print(f"  [red]✗ Could not resolve:[/red] {url_or_id}")
                client.close()
                raise typer.Exit(1)

    _env_set_key(Path(".env"), "LINEAR_PROJECT_ID", project_id)
    console.print(f"  [green]✓[/green] Project set: [bold]{project_name}[/bold]  [dim]{project_id[:8]}…[/dim]")
    client.close()


def _env_set_key(env_path: Path, key: str, value: str) -> None:
    text    = env_path.read_text() if env_path.exists() else ""
    lines   = [ln for ln in text.splitlines() if not ln.startswith(f"{key}=")]
    lines.append(f"{key}={value}")
    env_path.write_text("\n".join(lines) + "\n")


def _env_remove_key(env_path: Path, key: str) -> None:
    if not env_path.exists():
        return
    lines = [ln for ln in env_path.read_text().splitlines() if not ln.startswith(f"{key}=")]
    env_path.write_text("\n".join(lines) + "\n")


# ── plan ───────────────────────────────────────────────────────────────────────

@app.command()
def plan():
    """PM agent mode: create Linear issues and milestones for a project or feature."""
    from orchestrator.linear_client import LinearClient
    from orchestrator.config import load_config

    try:
        cfg = load_config()
    except ValueError as e:
        console.print(f"[red]✗ Config error:[/red] {e}")
        raise typer.Exit(1)

    client = LinearClient(cfg.linear_api_key)
    project_id = cfg.linear_project_id
    team_id    = cfg.linear_team_id

    console.print(Panel.fit("[bold]Resonance PM[/bold] — project planning", border_style="cyan"))
    console.print()

    if project_id:
        try:
            proj = client.get_project(project_id)
            project_name = proj["name"] if proj else project_id
        except Exception:
            project_name = project_id
        console.print(f"  Project: [bold cyan]{project_name}[/bold cyan]")
    else:
        console.print("  [dim]No LINEAR_PROJECT_ID set — issues will be created without project association.[/dim]")
        console.print("  [dim]Run: resonance setup  to pick a project.[/dim]")
    console.print()

    # ── Milestones ────────────────────────────────────────────────────────────
    milestones: list[dict] = []  # will hold {name, description, target_date, linear_id}

    if project_id:
        add_milestones = typer.confirm("  Create milestones?", default=False)
        console.print()
        if add_milestones:
            console.print("  [dim]Enter milestones one at a time. Leave name blank to stop.[/dim]")
            console.print()
            while True:
                m_name = typer.prompt("  Milestone name (blank to stop)", default="").strip()
                if not m_name:
                    break
                m_desc = typer.prompt("  Description (optional)", default="").strip()
                m_date = typer.prompt("  Target date YYYY-MM-DD (optional)", default="").strip()
                milestones.append({
                    "name": m_name,
                    "description": m_desc,
                    "target_date": m_date or None,
                })
                console.print(f"  [green]+[/green] Milestone: {m_name}")
                console.print()

    # ── Issues ────────────────────────────────────────────────────────────────
    issues_to_create: list[dict] = []
    milestone_names  = [m["name"] for m in milestones]

    console.print("  [dim]Enter issues one at a time. Leave title blank to stop.[/dim]")
    console.print()

    eligibility_state = cfg.state_eligibility
    priority_labels   = {"1": "urgent", "2": "high", "3": "medium", "4": "low"}

    while True:
        title = typer.prompt("  Issue title (blank to stop)", default="").strip()
        if not title:
            break
        description = typer.prompt("  Description (optional)", default="").strip()
        priority_raw = typer.prompt(
            "  Priority [1=urgent 2=high 3=medium 4=low, Enter=none]", default=""
        ).strip()
        priority = int(priority_raw) if priority_raw.isdigit() and priority_raw in "1234" else 0

        milestone_choice = None
        if milestone_names:
            for i, mn in enumerate(milestone_names, 1):
                console.print(f"    [dim]{i}.[/dim] {mn}")
            ms_raw = typer.prompt("  Milestone # (Enter for none)", default="").strip()
            if ms_raw.isdigit() and 1 <= int(ms_raw) <= len(milestone_names):
                milestone_choice = milestone_names[int(ms_raw) - 1]

        set_eligible = typer.confirm("  Move to 'Plan Approved' (ready for agent)?", default=False)
        issues_to_create.append({
            "title":        title,
            "description":  description,
            "priority":     priority,
            "milestone":    milestone_choice,
            "set_eligible": set_eligible,
        })
        console.print(f"  [green]+[/green] Issue: {title}")
        console.print()

    if not milestones and not issues_to_create:
        console.print("  [dim]Nothing to create.[/dim]")
        client.close()
        return

    # ── Summary ───────────────────────────────────────────────────────────────
    console.print()
    console.print("[bold]Summary[/bold]")
    if milestones:
        console.print(f"  [cyan]{len(milestones)} milestone(s)[/cyan]")
        for m in milestones:
            date_str = f"  [dim]→ {m['target_date']}[/dim]" if m["target_date"] else ""
            console.print(f"    · {m['name']}{date_str}")
    if issues_to_create:
        console.print(f"  [cyan]{len(issues_to_create)} issue(s)[/cyan]")
        for iss in issues_to_create:
            pri = f"  [dim]p{iss['priority']}[/dim]" if iss["priority"] else ""
            ms  = f"  [dim]→ {iss['milestone']}[/dim]" if iss["milestone"] else ""
            eligible = "  [green]Plan Approved[/green]" if iss["set_eligible"] else ""
            console.print(f"    · {iss['title']}{pri}{ms}{eligible}")
    console.print()

    if not typer.confirm("  Create in Linear?", default=True):
        console.print("  [dim]Cancelled.[/dim]")
        client.close()
        return

    # ── Create milestones first ───────────────────────────────────────────────
    milestone_id_map: dict[str, str] = {}  # name → linear_id
    for m in milestones:
        try:
            result = client.create_milestone(
                project_id=project_id,
                name=m["name"],
                description=m["description"],
                target_date=m["target_date"],
            )
            milestone_id_map[m["name"]] = result["id"]
            console.print(f"  [green]✓[/green] Milestone: {m['name']}")
        except Exception as exc:
            console.print(f"  [red]✗[/red] Milestone '{m['name']}': {exc}")

    # ── Create issues ─────────────────────────────────────────────────────────
    for iss in issues_to_create:
        try:
            state_name = eligibility_state if iss["set_eligible"] else None
            milestone_linear_id = milestone_id_map.get(iss["milestone"]) if iss["milestone"] else None
            created = client.create_issue(
                team_id=team_id,
                title=iss["title"],
                description=iss["description"],
                project_id=project_id,
                state_name=state_name,
                priority=iss["priority"],
                milestone_id=milestone_linear_id,
            )
            url = created.get("url", "")
            console.print(f"  [green]✓[/green] {created.get('identifier', '?')}  {iss['title']}  [dim]{url}[/dim]")
        except Exception as exc:
            console.print(f"  [red]✗[/red] '{iss['title']}': {exc}")

    console.print()
    console.print("[bold green]Done.[/bold green]")
    client.close()


# ── watch ──────────────────────────────────────────────────────────────────────

@app.command()
def watch():
    """Launch the TUI dashboard."""
    from tui.app import ResonanceDashboard
    ResonanceDashboard().run()


# ── attach ─────────────────────────────────────────────────────────────────────

@app.command()
def attach(issue_id: str = typer.Argument(..., help="Issue identifier e.g. QO-123")):
    """Print the worktree path and log file path so you can cd and tail manually."""
    run = run_state.get_run(issue_id)
    if not run:
        console.print(f"[red]No run found for {issue_id}[/red]")
        raise typer.Exit(1)

    worktree = run.get("worktree", "?")
    log_file = run.get("log_file", "?")
    console.print(f"\n[bold]Worktree:[/bold]  {worktree}")
    console.print(f"[bold]Log file:[/bold]  {log_file}")
    console.print(f"\n[dim]cd {worktree}[/dim]")
    console.print(f"[dim]tail -f {log_file}[/dim]\n")


# ── debug ──────────────────────────────────────────────────────────────────────

@app.command()
def debug(issue_id: str = typer.Argument(..., help="Issue identifier e.g. RND-32")):
    """Show full diagnostic info for a run: command, settings, recent log output."""
    import glob

    run = run_state.get_run(issue_id)
    if not run:
        console.print(f"[red]No run found for {issue_id}[/red]")
        raise typer.Exit(1)

    worktree  = run.get("worktree", "")
    log_file  = run.get("log_file", "")
    status    = run.get("status", "?")
    error     = run.get("error", "")
    attempt   = run.get("attempt", 1)

    console.print(f"\n[bold]── Run: {issue_id} ──────────────────────────────[/bold]")
    console.print(f"  Status:    [bold]{status}[/bold]")
    console.print(f"  Attempts:  {attempt}")
    if error:
        console.print(f"  Error:     [red]{error}[/red]")
    console.print(f"  Worktree:  {worktree}")

    # Settings.json
    settings_path = Path(worktree) / ".claude" / "settings.json" if worktree else None
    if settings_path and settings_path.exists():
        console.print(f"\n[bold]── .claude/settings.json ─────────────────────[/bold]")
        try:
            import json as _json
            settings = _json.loads(settings_path.read_text())
            console.print(f"  pluginDirs: {settings.get('pluginDirs', [])}")
            console.print(f"  mcpConfig:  {settings.get('mcpConfig', '(not set)')}")
        except Exception as e:
            console.print(f"  [red]Could not read: {e}[/red]")

    # Recent log output
    log_candidates = sorted(glob.glob(f"runs/logs/{issue_id}-*.log"), reverse=True)
    log_to_show = log_file if log_file and Path(log_file).exists() else (log_candidates[0] if log_candidates else None)
    if log_to_show:
        console.print(f"\n[bold]── Last 60 lines of log: {log_to_show} ──────[/bold]")
        try:
            lines = Path(log_to_show).read_text(errors="replace").splitlines()
            for ln in lines[-60:]:
                color = "red" if re.search(r"\berror\b", ln, re.I) else "dim"
                console.print(f"  [{color}]{ln}[/{color}]")
        except Exception as e:
            console.print(f"  [red]Could not read log: {e}[/red]")
    else:
        console.print(f"\n  [dim]No log file found for {issue_id}[/dim]")

    # Recent events from events.jsonl
    events_path = Path("runs/events.jsonl")
    if events_path.exists():
        console.print(f"\n[bold]── Last 20 events ─────────────────────────[/bold]")
        try:
            all_events = [
                json.loads(ln) for ln in events_path.read_text().splitlines()
                if ln.strip()
                if json.loads(ln).get("issue_id") == issue_id
            ]
            for ev in all_events[-20:]:
                ts   = ev.get("ts", "")[-8:]
                kind = ev.get("event", ev.get("type", "?"))
                data = {k: v for k, v in ev.items() if k not in ("ts", "issue_id", "event", "type")}
                data_str = "  ".join(f"{k}={v}" for k, v in data.items())
                color = "red" if "error" in kind or "fail" in kind else "cyan" if "complete" in kind else ""
                prefix = f"[{color}]" if color else ""
                suffix = f"[/{color}]" if color else ""
                console.print(f"  {ts}  {prefix}{kind:<22}{suffix}  [dim]{data_str[:120]}[/dim]")
        except Exception as e:
            console.print(f"  [red]Could not read events: {e}[/red]")

    # Orchestrator log tail
    orch_log = Path("runs/orchestrator.log")
    if orch_log.exists():
        console.print(f"\n[bold]── Orchestrator log (last 20 lines) ───────[/bold]")
        try:
            lines = orch_log.read_text(errors="replace").splitlines()
            issue_lines = [l for l in lines if issue_id in l][-20:]
            for ln in issue_lines:
                color = "red" if re.search(r"\berror\b|\bexception\b", ln, re.I) else "dim"
                console.print(f"  [{color}]{ln}[/{color}]")
        except Exception as e:
            console.print(f"  [red]Could not read orchestrator log: {e}[/red]")

    console.print()


# ── checkpoint ─────────────────────────────────────────────────────────────────

@app.command()
def checkpoint(
    issue_id: str = typer.Argument(..., help="Issue identifier e.g. RND-22-P1-B1"),
    push: bool = typer.Option(False, "--push", help="Push the branch to remote after writing RESONANCE.md"),
):
    """Write a RESONANCE.md checkpoint to the issue worktree.

    Captures current run state so any session (or another machine) can load
    context via /reso. Use --push to push the branch to GitHub for cross-machine access.
    """
    run = run_state.get_run(issue_id)
    if not run:
        console.print(f"[red]No run found for {issue_id}[/red]")
        raise typer.Exit(1)

    worktree = run.get("worktree", "")
    branch = run.get("branch", f"agent/{issue_id}")
    status = run.get("status", "unknown")

    if not worktree:
        console.print(f"[red]No worktree recorded for {issue_id}[/red]")
        raise typer.Exit(1)

    dest = issue_memory.write_resonance_checkpoint(
        issue_id=issue_id,
        worktree_path=worktree,
        issue_url="",
        issue_title=issue_id,
        branch=branch,
        by="resonance",
        status=status,
    )

    if not dest:
        console.print(f"[red]Worktree not found at {worktree}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✓ RESONANCE.md written:[/green] {dest}")
    console.print(f"  Issue:    {issue_id}")
    console.print(f"  Status:   {status}")
    console.print(f"  Branch:   {branch}")
    console.print(f"  Worktree: {worktree}")

    if push:
        import subprocess
        result = subprocess.run(
            ["git", "push", "-u", "origin", branch],
            cwd=worktree,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            console.print(f"[green]✓ Branch pushed:[/green] {branch}")
        else:
            console.print(f"[yellow]⚠ Push failed:[/yellow] {result.stderr.strip()}")
            console.print("[dim]You can push manually: cd {worktree} && git push -u origin {branch}[/dim]")

    console.print(f"\n[dim]Load context in any Claude Code session:[/dim]")
    console.print(f"[dim]  /reso {issue_id}[/dim]\n")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _short_ts(iso: str) -> str:
    if not iso:
        return ""
    return iso[11:19]


def _event_color(event_type: str) -> str:
    if "fail" in event_type or "error" in event_type or "abort" in event_type:
        return "red"
    if "complete" in event_type or "success" in event_type or "approved" in event_type:
        return "green"
    if "waiting" in event_type or "paused" in event_type or "signal" in event_type or "uncertainty" in event_type:
        return "yellow"
    return "cyan"


def cli():
    app()


if __name__ == "__main__":
    cli()
