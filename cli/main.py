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
    console.print("  [dim]2. A Linear project   — the project Resonance will watch[/dim]")
    console.print("  [dim]3. Figma token        — optional, only for design tasks[/dim]")
    console.print("  [dim]4. GitHub token       — optional, only for auto PR creation[/dim]")
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
    console.print("[bold]Step 1/4[/bold]  Linear API key")
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
    console.print("[bold]Step 2/4[/bold]  Linear team")
    console.print("  [dim]Resonance watches a team's issues — not a specific project.[/dim]")
    console.print("  [dim]Fetching your teams…[/dim]")
    console.print()

    # Accept LINEAR_TEAM_ID (new) or LINEAR_PROJECT_ID (legacy)
    team_id = (
        os.environ.get("LINEAR_TEAM_ID")
        or env_values.get("LINEAR_TEAM_ID", "")
        or os.environ.get("LINEAR_PROJECT_ID")
        or env_values.get("LINEAR_PROJECT_ID", "")
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
        # Remove legacy key if present
        env_values.pop("LINEAR_PROJECT_ID", None)
        team = team_obj
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"  [red]✗ Could not load team:[/red] {e}")
        raise typer.Exit(1)

    # ── Step 3: Linear states and labels ─────────────────────────────────────
    console.print()
    console.print("[bold]Step 3/4[/bold]  Linear workflow states")
    console.print("  [dim]Creating the workflow states Resonance needs (if they don't exist yet).[/dim]")
    console.print()
    _ensure_states(client, team_id)

    console.print()
    console.print("  [dim]Creating issue labels:[/dim]")
    console.print()
    _ensure_labels(client, team_id)

    # ── Step 4: Optional credentials ─────────────────────────────────────────
    console.print()
    console.print("[bold]Step 4/4[/bold]  Optional credentials")

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


def _ensure_states(client, team_id: str) -> None:
    from orchestrator.linear_client import REQUIRED_STATES
    existing = {s["name"] for s in client.get_team_states(team_id)}
    for state in REQUIRED_STATES:
        if state["name"] in existing:
            console.print(f"  [dim]–[/dim] {state['name']} (already exists)")
        else:
            try:
                client.create_state(team_id, state["name"], state["color"], state["type"])
                console.print(f"  [green]✓[/green] Created state: {state['name']}")
            except Exception as e:
                console.print(f"  [yellow]⚠[/yellow] Could not create '{state['name']}': {e}")


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
    VAR_ORDER = ["LINEAR_API_KEY", "LINEAR_PROJECT_ID", "FIGMA_API_KEY", "GITHUB_TOKEN"]
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
    team_id = (
        os.environ.get("LINEAR_TEAM_ID", "").strip()
        or os.environ.get("LINEAR_PROJECT_ID", "").strip()
    )

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
        from orchestrator.linear_client import LinearClient, REQUIRED_STATES, REQUIRED_LABELS
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
            for state in REQUIRED_STATES:
                if state["name"] in existing_states:
                    _ok(state["name"])
                else:
                    _fail(state["name"], "missing — run: resonance setup")
                    all_ok = False

            console.print()
            console.print("[bold]Linear labels[/bold]")
            existing_labels = {l["name"].lower() for l in client.get_team_labels(team_id)}
            for label in REQUIRED_LABELS:
                if label["name"].lower() in existing_labels:
                    _ok(label["name"])
                else:
                    _fail(label["name"], "missing — run: resonance setup")
                    all_ok = False

        client.close()

    except Exception as e:
        _fail("Linear API", str(e))
        all_ok = False

    # ── Summary ───────────────────────────────────────────────────────────────
    console.print()
    if all_ok:
        console.print("[bold green]✓ All checks passed.[/bold green]")
        console.print("  Ready to run: [bold]./onair.sh[/bold]")
    else:
        console.print("[bold red]✗ Some checks failed.[/bold red]")
        console.print("  Run [bold]resonance setup[/bold] to fix missing configuration.")

    raise typer.Exit(0 if all_ok else 1)


def _ok(label: str) -> None:
    console.print(f"  [green]✓[/green] {label}")

def _fail(label: str, detail: str) -> None:
    console.print(f"  [red]✗[/red] {label} — [dim]{detail}[/dim]")

def _warn(label: str, detail: str) -> None:
    console.print(f"  [yellow]–[/yellow] {label} — [dim]{detail}[/dim]")


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


# ── watch (Milestone 2 placeholder) ───────────────────────────────────────────

@app.command()
def watch():
    """Launch the TUI dashboard (Milestone 2 — coming soon)."""
    console.print("[yellow]TUI dashboard is coming in Milestone 2.[/yellow]")
    console.print("For now, use [bold]resonance status[/bold] and [bold]resonance logs <ID>[/bold].")


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
