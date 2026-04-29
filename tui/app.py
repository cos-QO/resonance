"""
Resonance TUI — KDash / UptimeKit-CLI inspired dashboard.

Layout (top → bottom):
  header_bar      — orch health + run counters (1 line)
  attention        — ⚠ Needs Your Attention  (hidden when empty)
  runs_section     — Active Runs table  (or idle hint)
  pipeline_section — Linear Pipeline table
  events_section   — Event Stream / Log viewer  (1fr, fills rest)
"""
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from rich import box as rich_box
from rich.console import Group
from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Input, Label, RichLog, Static


# ── Focusable widgets ─────────────────────────────────────────────────────────

class _EventLog(RichLog):
    """RichLog that never steals keyboard focus from the App."""
    can_focus = False


# ── Modals ────────────────────────────────────────────────────────────────────

class _ProjectInputScreen(ModalScreen):
    """Set the active Linear project by URL or UUID."""

    BINDINGS = [Binding("escape", "dismiss", "Cancel", priority=True)]

    CSS = """
    _ProjectInputScreen { align: center middle; }
    #_proj_box {
        width: 68; height: auto;
        background: $panel; border: round $primary; padding: 1 2;
    }
    #_proj_title  { text-style: bold; color: $primary; margin-bottom: 1; }
    #_proj_hint   { color: $text-muted; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="_proj_box"):
            yield Label("  Set Linear project", id="_proj_title")
            yield Input(
                placeholder="https://linear.app/…/project/…  or UUID",
                id="_proj_input",
            )
            yield Label("  Enter to confirm · Esc to cancel", id="_proj_hint")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip())


class _FeedbackScreen(ModalScreen):
    """Send a feedback message to a waiting agent."""

    BINDINGS = [Binding("escape", "dismiss", "Cancel", priority=True)]

    CSS = """
    _FeedbackScreen { align: center middle; }
    #_fb_box {
        width: 70; height: auto;
        background: $panel; border: round $warning; padding: 1 2;
    }
    #_fb_title  { text-style: bold; color: $warning; margin-bottom: 1; }
    #_fb_hint   { color: $text-muted; margin-top: 1; }
    """

    def __init__(self, issue_hint: str = "") -> None:
        super().__init__()
        self._issue_hint = issue_hint

    def compose(self) -> ComposeResult:
        with Vertical(id="_fb_box"):
            yield Label("  Send feedback to agent", id="_fb_title")
            if self._issue_hint:
                yield Label(f"  Issue: {self._issue_hint}", style="bold cyan")
            else:
                yield Input(placeholder="Issue ID  (e.g. QO-42)", id="_fb_issue")
            yield Input(placeholder="Your message to the agent…", id="_fb_msg")
            yield Label("  Tab · Enter to send · Esc to cancel", id="_fb_hint")

    def on_mount(self) -> None:
        first = "_fb_msg" if self._issue_hint else "_fb_issue"
        self.query_one(f"#{first}", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "_fb_issue":
            self.query_one("#_fb_msg", Input).focus()
        else:
            self._submit()

    def _submit(self) -> None:
        issue_id = (
            self._issue_hint
            if self._issue_hint
            else self.query_one("#_fb_issue", Input).value.strip()
        )
        text = self.query_one("#_fb_msg", Input).value.strip()
        if issue_id and text:
            self.dismiss((issue_id, text))
        elif not issue_id:
            self.query_one("#_fb_issue", Input).focus()


_DEMO_ISSUE_TITLE = "Demo: Resonance Pipeline — Hello World"

_DEMO_ISSUE_DESCRIPTION = """\
# Demo Plan: Hello World Button Component

A demonstration of the full Resonance pipeline — from plan approval through execution
to human review.

## Overview
Build a self-contained, styled Hello World HTML page to verify the pipeline end-to-end.
No existing code is touched. Completely isolated.

## Phases

### Phase 1: Scaffold
Create the `demo/` directory and the base `demo/hello-world.html` file with correct
HTML5 structure, title, and a "Hello from Resonance" heading.

### Phase 2: Styling
Add inline CSS: dark terminal-inspired colour scheme, styled CTA button with a visible
hover state. Everything embedded — no external stylesheets or frameworks.

### Phase 3: Verification & Commit
Verify the file renders correctly (open in browser if possible), commit with message:
`demo: add hello-world button component`

## Acceptance Criteria
- [ ] `demo/hello-world.html` exists at the repository root
- [ ] Page shows "Hello from Resonance" heading
- [ ] Styled button with hover state
- [ ] All CSS inline, no JavaScript, no external dependencies
- [ ] File committed to the repo

## Notes
- Vanilla HTML + CSS only — no build step, no npm, no frameworks
- Dark background, bright accent colour scheme
- Single self-contained `.html` file
"""


class _DemoScreen(ModalScreen):
    """Guided end-to-end demo: creates a plan issue in Todo for user to approve."""

    BINDINGS = [Binding("escape", "dismiss", "Cancel", priority=True)]

    CSS = """
    _DemoScreen { align: center middle; }
    #_demo_box {
        width: 76; height: auto;
        background: $panel; border: round $accent; padding: 1 2;
    }
    #_demo_title         { text-style: bold; color: $accent; margin-bottom: 1; }
    #_demo_proj_section  { height: auto; margin-top: 1; border-top: dashed $panel-lighten-2; padding-top: 1; }
    #_demo_proj_row      { layout: horizontal; height: auto; }
    #_demo_proj_label    { color: $text-muted; width: 12; }
    #_demo_proj_name     { color: $primary; }
    #_demo_proj_input    { height: auto; margin-top: 1; }
    #_demo_status        { height: auto; margin-top: 1; min-height: 1; }
    #_demo_hint          { height: auto; color: $text-muted; margin-top: 1; }
    """

    _INTRO = """\
[bold]What this demo does:[/bold]

  [dim]1.[/dim]  Creates a [bold cyan]plan[/bold cyan] issue in [bold white]Todo[/bold white] — open in Linear to review it
  [dim]2.[/dim]  Move the issue to [bold bright_green]Plan Approved[/bold bright_green] to kick off the pipeline
  [dim]3.[/dim]  The orchestrator runs the [bold cyan]Planning Agent[/bold cyan] to decompose into phases
  [dim]4.[/dim]  Phase issues execute automatically (each becomes its own run)
  [dim]5.[/dim]  Each phase moves to [bold magenta]Human Review[/bold magenta] when done — you close the loop

[bold]The plan:[/bold]  build [bold white]demo/hello-world.html[/bold white] — a styled button page
[dim]        3 phases: Scaffold → Styling → Verify & Commit[/dim]

[bold]Requirements:[/bold]
  [dim]·[/dim]  Orchestrator running  [dim](● orch must be green in the header)[/dim]
  [dim]·[/dim]  Linear project set    [dim](shown below — press c to change)[/dim]\
"""

    def __init__(self) -> None:
        super().__init__()
        self._busy = False
        self._project_ready = False
        self._project_name  = ""
        self._changing      = False   # True when user is typing a new project URL
        try:
            from orchestrator.config import load_config
            cfg = load_config()
            self._project_ready = bool(cfg.linear_project_id)
            if self._project_ready:
                self._project_name = cfg.linear_project_id[:8] + "…"
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        with Vertical(id="_demo_box"):
            yield Label("  Resonance Demo — full pipeline walkthrough", id="_demo_title")
            yield Static(self._INTRO, markup=True)
            with Vertical(id="_demo_proj_section"):
                with Vertical(id="_demo_proj_row"):
                    yield Label("  Project  ", id="_demo_proj_label")
                    yield Label("", id="_demo_proj_name")
                yield Input(
                    placeholder="paste a Linear project URL or UUID…",
                    id="_demo_proj_input",
                )
            yield Static("", id="_demo_status")
            yield Label("", id="_demo_hint")

    def on_mount(self) -> None:
        self._refresh_display()
        # Fetch project name in background if project is already set
        if self._project_ready:
            threading.Thread(target=self._fetch_project_name, daemon=True).start()

    def _fetch_project_name(self) -> None:
        try:
            from orchestrator.config import load_config
            from orchestrator.linear_client import LinearClient
            cfg = load_config()
            client = LinearClient(cfg.linear_api_key)
            proj = client.get_project(cfg.linear_project_id)
            client.close()
            if proj:
                self._project_name = proj["name"]
                self.call_from_thread(self._update_proj_name_label)
        except Exception:
            pass

    def _update_proj_name_label(self) -> None:
        if self._project_ready and not self._changing:
            self.query_one("#_demo_proj_name", Label).update(
                f"[bold cyan]{self._project_name}[/bold cyan]  [dim](c to change)[/dim]"
            )

    def _refresh_display(self) -> None:
        name_lbl  = self.query_one("#_demo_proj_name",  Label)
        inp       = self.query_one("#_demo_proj_input", Input)
        hint_lbl  = self.query_one("#_demo_hint",       Label)

        if self._project_ready and not self._changing:
            inp.display = False
            name_lbl.update(
                f"[bold cyan]{self._project_name}[/bold cyan]  [dim](c to change)[/dim]"
            )
            hint_lbl.update(
                "  Enter to create demo issue · c to change project · Esc to cancel"
            )
        elif self._changing:
            inp.display = True
            inp.value   = ""
            inp.focus()
            name_lbl.update(
                f"[dim]currently: {self._project_name}[/dim]  [dim](Esc to go back)[/dim]"
            )
            hint_lbl.update("  Paste new project URL · Enter to confirm · Esc to cancel")
        else:
            # No project set
            inp.display = True
            inp.focus()
            name_lbl.update("[bold yellow]not set[/bold yellow]")
            hint_lbl.update("  Paste project URL · Enter to confirm · Esc to cancel")

    def on_key(self, event) -> None:
        if self._busy:
            return

        if event.key == "c" and self._project_ready and not self._changing:
            self._changing = True
            self._refresh_display()
            event.prevent_default()

        elif event.key == "escape":
            if self._changing:
                self._changing = False
                self._refresh_display()
                event.prevent_default()
            else:
                self.dismiss(None)

        elif event.key == "enter" and self._project_ready and not self._changing:
            self._start_demo()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        url = event.value.strip()
        if not url or self._busy:
            return
        self._busy = True
        event.input.disabled = True
        self.query_one("#_demo_status", Static).update("[dim]Resolving project…[/dim]")
        self.query_one("#_demo_hint", Label).update("  Resolving…")
        threading.Thread(target=self._resolve_project, args=(url,), daemon=True).start()

    def _resolve_project(self, url_or_id: str) -> None:
        try:
            result = _resolve_project(url_or_id)
            if not result:
                self.call_from_thread(
                    self._on_project_error, f"Could not resolve: {url_or_id[:50]}"
                )
                return

            project_id, project_name = result

            env_path = Path(".env")
            text  = env_path.read_text() if env_path.exists() else ""
            lines = [ln for ln in text.splitlines() if not ln.startswith("LINEAR_PROJECT_ID=")]
            lines.append(f"LINEAR_PROJECT_ID={project_id}")
            env_path.write_text("\n".join(lines) + "\n")

            try:
                from dotenv import load_dotenv
                load_dotenv(override=True)
            except ImportError:
                pass

            self.call_from_thread(self._on_project_resolved, project_name)

        except Exception as exc:
            self.call_from_thread(self._on_project_error, str(exc)[:80])

    def _on_project_resolved(self, project_name: str) -> None:
        self._project_ready = True
        self._project_name  = project_name
        self._changing      = False
        self._busy          = False
        inp = self.query_one("#_demo_proj_input", Input)
        inp.disabled = False
        self.query_one("#_demo_status", Static).update(
            f"[bold bright_green]✓[/bold bright_green]  Project set: [bold cyan]{project_name}[/bold cyan]"
        )
        self._refresh_display()

    def _on_project_error(self, msg: str) -> None:
        self._busy = False
        inp = self.query_one("#_demo_proj_input", Input)
        inp.disabled = False
        self.query_one("#_demo_status", Static).update(
            f"[bold red]✗[/bold red]  {msg}"
        )
        self.query_one("#_demo_hint", Label).update(
            "  Paste project URL · Enter to confirm · Esc to cancel"
        )

    def _start_demo(self) -> None:
        self._busy = True
        self.query_one("#_demo_hint", Label).update("  Creating demo plan issue…")
        threading.Thread(target=self._run_demo, daemon=True).start()

    def _run_demo(self) -> None:
        try:
            from orchestrator.linear_client import LinearClient
            from orchestrator.config import load_config

            cfg    = load_config()
            client = LinearClient(cfg.linear_api_key)

            if not cfg.linear_project_id:
                self.call_from_thread(
                    self._set_error,
                    "No project set — press c to set a project first.",
                )
                return

            if not _orch_alive():
                self.call_from_thread(
                    self._set_error,
                    "Orchestrator is not running.\n\n"
                    "  Start it with [bold]./onair.sh[/bold] first, then try again.",
                )
                return

            # Create plan issue in Todo — user must move to Plan Approved to kick off
            issue = client.create_issue(
                team_id=cfg.linear_team_id,
                title=_DEMO_ISSUE_TITLE,
                description=_DEMO_ISSUE_DESCRIPTION,
                project_id=cfg.linear_project_id,
                state_name="Todo",
                label_names=["plan", "RES"],
                priority=2,
            )
            client.close()

            identifier = issue.get("identifier", "?")
            url        = issue.get("url", "")

            self.call_from_thread(self._on_success, identifier, url)

        except Exception as exc:
            err = str(exc)
            # Surface the most actionable part of the error
            if "label" in err.lower() and "not found" in err.lower():
                msg = (
                    "Labels 'plan' or 'RES' not found in Linear.\n\n"
                    "  Run [bold]./onair.sh[/bold] and let it auto-fix labels, then retry."
                )
            elif "state" in err.lower() or "todo" in err.lower():
                msg = f"Could not set Todo state:\n  {err[:80]}"
            else:
                msg = f"Error creating issue:\n  {err[:100]}"
            self.call_from_thread(self._set_error, msg)

    def _set_error(self, msg: str) -> None:
        self._busy = False
        self.query_one("#_demo_status", Static).update(
            f"[bold red]✗[/bold red]  {msg}"
        )
        self.query_one("#_demo_hint", Label).update("  Esc to close")

    def _on_success(self, identifier: str, url: str) -> None:
        status = (
            f"[bold bright_green]✓[/bold bright_green]  Plan issue [bold cyan]{identifier}[/bold cyan] "
            f"created in [bold white]Todo[/bold white]\n\n"
            f"  [bold]Next:[/bold] open Linear, review the plan, then move to "
            f"[bold bright_green]Plan Approved[/bold bright_green] to start the pipeline.\n\n"
            f"  The orchestrator will pick it up within [dim]60s[/dim] of approval."
        )
        self.query_one("#_demo_status", Static).update(status)
        self.query_one("#_demo_hint", Label).update(
            f"  [dim]{url}[/dim]\n  Esc to close"
        )
        self._busy = False


class _EventDetailScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Close", priority=True)]
    CSS = """
    _EventDetailScreen { align: center middle; }
    #_evd_outer {
        width: 100; height: auto; max-height: 85vh;
        background: $panel; border: round $accent; padding: 0;
    }
    #_evd_scroll { padding: 1 3; }
    #_evd_hint { padding: 0 2; color: $text-muted; }
    """
    def __init__(self, ev: dict) -> None:
        super().__init__()
        self._ev = ev
    def compose(self) -> ComposeResult:
        with Vertical(id="_evd_outer"):
            with VerticalScroll(id="_evd_scroll"):
                yield Static(self._build(), markup=True)
            yield Label("  Esc to close", id="_evd_hint")
    def _build(self) -> str:
        ev = self._ev
        ts = ev.get("ts", "")
        issue = ev.get("issue", "system")
        etype = ev.get("type", "?")
        color = _event_color(etype)
        lines = [
            f"[bold white]{etype}[/bold white]  [{color}]●[/{color}]",
            f"[dim]Issue:[/dim] [bold cyan]{issue}[/bold cyan]   [dim]Time:[/dim] {ts}",
            "",
        ]
        for k, v in ev.items():
            if k in ("ts", "issue", "type"):
                continue
            if isinstance(v, dict):
                lines.append(f"[bold dim]{k}:[/bold dim]")
                for sk, sv in v.items():
                    sv_str = str(sv)
                    if isinstance(sv, str) and (sv.startswith("http") or sv.startswith("file://") or ("/" in sv and len(sv) > 4)):
                        lines.append(f"  [dim]{sk}:[/dim] [cyan]{sv_str}[/cyan]")
                    else:
                        lines.append(f"  [dim]{sk}:[/dim] {sv_str}")
            else:
                val = str(v)
                if isinstance(v, str) and (v.startswith("http") or v.startswith("file://") or ("/" in v and len(v) > 4)):
                    lines.append(f"[bold dim]{k}:[/bold dim] [cyan]{val}[/cyan]")
                else:
                    lines.append(f"[bold dim]{k}:[/bold dim] {val}")
            lines.append("")
        return "\n".join(lines)


class _EventBrowserScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "dismiss", "Close", priority=True),
        Binding("enter", "open_detail", "Detail"),
    ]
    CSS = """
    _EventBrowserScreen { align: center middle; }
    #_evb_outer {
        width: 130; height: 85vh;
        background: $panel; border: round $primary; padding: 0;
    }
    #_evb_title { padding: 0 2; color: $primary; text-style: bold; }
    #_evb_list { height: 1fr; }
    #_evb_hint { padding: 0 2; color: $text-muted; }
    """
    def __init__(self, events: list[dict]) -> None:
        super().__init__()
        _sys = _SYSTEM_EVENTS  # module-level constant
        self._events = [
            ev for ev in events
            if not (ev.get("issue") == "system" and ev.get("type") in _sys)
        ]
    def compose(self) -> ComposeResult:
        from textual.widgets import ListView, ListItem
        with Vertical(id="_evb_outer"):
            yield Static("  Event Stream — full history", id="_evb_title")
            items = []
            for ev in reversed(self._events[-300:]):
                ts    = ev.get("ts", "")
                short = ts[11:19] if len(ts) > 10 else ts
                issue = ev.get("issue", "system")
                etype = ev.get("type", "?")
                color = _event_color(etype)
                extra = {k: v for k, v in ev.items() if k not in {"ts", "issue", "type"}}
                extra_str = "  " + "  ".join(f"{k}={str(v)[:40]}" for k, v in extra.items()) if extra else ""
                items.append(ListItem(Static(
                    f"[dim]{short}[/dim]  [bold cyan]{issue:<12}[/bold cyan]  "
                    f"[{color}]{etype:<28}[/{color}][dim]{extra_str}[/dim]",
                    markup=True
                )))
            yield ListView(*items, id="_evb_list")
            yield Static("  ↑↓ navigate   Enter detail   Esc close", id="_evb_hint")
    def action_open_detail(self) -> None:
        lv = self.query_one("#_evb_list")
        idx = lv.index
        if idx is not None:
            evs = list(reversed(self._events[-300:]))
            if 0 <= idx < len(evs):
                self.push_screen(_EventDetailScreen(evs[idx]))


class _RunDetailScreen(ModalScreen):
    """Detail view for an active or waiting run — shows memory context and artifacts."""

    BINDINGS = [Binding("escape", "dismiss", "Close", priority=True)]

    CSS = """
    _RunDetailScreen { align: center middle; }
    #_detail_outer {
        width: 84; height: auto; max-height: 80vh;
        background: $panel; border: round $primary; padding: 0;
    }
    #_detail_scroll { padding: 1 3; }
    """

    def __init__(self, issue_id: str, run: dict) -> None:
        super().__init__()
        self._issue_id = issue_id
        self._run = run

    def compose(self) -> ComposeResult:
        with Vertical(id="_detail_outer"):
            with VerticalScroll(id="_detail_scroll"):
                yield Static(self._build_content(), markup=True, id="_detail_content")
            yield Label("  Esc to close", id="_detail_hint")

    def _build_content(self) -> str:
        run = self._run
        issue_id = self._issue_id
        status = run.get("status", "?")
        task_type = run.get("task_type", "?")
        iteration = run.get("iteration", 1)
        linear_url = run.get("linear_url", "") or run.get("linear_uuid", "")
        artifacts = run.get("artifacts", {})

        color_map = {
            "running":       "green",
            "waiting_human": "magenta",
            "needs_input":   "yellow",
            "paused":        "dark_orange",
            "complete":      "bright_green",
            "failed":        "red",
        }
        status_color = color_map.get(status, "white")
        status_label = {
            "running":       "RUNNING",
            "waiting_human": "HUMAN REVIEW",
            "needs_input":   "NEEDS INPUT",
            "paused":        "PAUSED",
            "complete":      "DONE",
            "failed":        "FAILED",
        }.get(status, status.upper())

        lines = [
            f"[bold white]{issue_id}[/bold white]  "
            f"[{status_color}]● {status_label}[/{status_color}]  "
            f"[dim]iter {iteration}  ·  {task_type}[/dim]",
            "",
        ]

        if linear_url and linear_url.startswith("http"):
            lines += [f"[dim]Linear:[/dim]  [cyan]{linear_url}[/cyan]", ""]

        if artifacts:
            lines.append("[bold]Artifacts[/bold]")
            for k, v in artifacts.items():
                lines.append(f"  [dim]{k}:[/dim]  [cyan]{v}[/cyan]")
            lines.append("")

        # Load latest handoff from local memory
        handoff_dir = Path(f"runs/memory/{issue_id}/handoffs")
        if handoff_dir.exists():
            handoffs = sorted(handoff_dir.glob("iter-*.md"))
            if handoffs:
                try:
                    text = handoffs[-1].read_text()[:800]
                    lines += [
                        f"[bold]Latest Handoff[/bold]  [dim]({handoffs[-1].name})[/dim]",
                        "",
                        text,
                        "",
                    ]
                except Exception:
                    pass

        if status in ("waiting_human", "needs_input"):
            q = run.get("pending_question", "")
            if status == "needs_input":
                lines += [
                    "[bold yellow]⏸ Agent needs your input[/bold yellow]",
                    "",
                    q or "Agent hit a blocker and is waiting for your decision.",
                    "",
                    "[dim]Reply in Linear with your answer — agent resumes automatically.[/dim]",
                ]
            else:
                lines += [
                    "[bold magenta]👁 Ready for your review[/bold magenta]",
                    "",
                    q or "Agent completed work — ready for your review.",
                    "",
                    "[dim]To continue:[/dim] reply in Linear → move to [bold]Agent Feedback Needed[/bold]",
                    "[dim]To accept:[/dim]   move issue to [bold]Done[/bold]",
                ]

        if run.get("error"):
            lines += [
                f"[bold red]Last error:[/bold red]  {run['error']}",
                "",
            ]

        worktree = run.get("worktree", "")
        branch   = run.get("branch", "")
        log_file = run.get("log_file", "")
        lines += [
            "",
            "[bold dim]─── Manual Control ───────────────────────────────[/bold dim]",
            "",
            f"[dim]Issue ID:[/dim]  [bold white]{issue_id}[/bold white]",
            f"[dim]Branch:  [/dim]  [cyan]{branch}[/cyan]",
            f"[dim]Worktree:[/dim]  [cyan]{worktree}[/cyan]",
            "",
            "[dim]Open in Claude Code:[/dim]",
            f"[bold green]  cd {worktree} && claude[/bold green]",
            "",
            "[dim]Use in cc-pipeline skill:[/dim]",
            f"[bold green]  /pd-issue {issue_id}[/bold green]",
        ]
        if log_file:
            lines += [
                "",
                f"[dim]Log:[/dim]  {log_file}",
            ]

        return "\n".join(lines)


class _CleanupScreen(ModalScreen):
    """Confirm clearing completed/failed runs from the state file."""

    BINDINGS = [Binding("escape", "dismiss", "Cancel", priority=True)]

    CSS = """
    _CleanupScreen { align: center middle; }
    #_cleanup_box {
        width: 62; height: auto;
        background: $panel; border: round $warning; padding: 1 2;
    }
    #_cleanup_title  { text-style: bold; color: $warning; margin-bottom: 1; }
    #_cleanup_detail { color: $text-muted; margin-bottom: 1; }
    #_cleanup_hint   { color: $text-muted; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="_cleanup_box"):
            yield Label("  Clear session?", id="_cleanup_title")
            yield Static(
                "  This will:\n\n"
                "  [bold]·[/bold]  Remove [bold]failed[/bold], [bold]complete[/bold], and [bold]archived[/bold] run entries\n"
                "  [bold]·[/bold]  Clear the [bold]event stream[/bold] log\n"
                "  [bold]·[/bold]  Reset [bold]performance stats[/bold]\n\n"
                "  Active, paused, and waiting runs are [bold]not[/bold] affected.\n"
                "  Memory files in [dim]runs/memory/[/dim] are preserved.",
                markup=True,
                id="_cleanup_detail",
            )
            yield Label("  y / Enter to confirm · n / Esc to cancel", id="_cleanup_hint")

    def on_key(self, event) -> None:
        if event.key in ("y", "Y", "enter"):
            self.dismiss(True)
        elif event.key in ("n", "N", "escape"):
            self.dismiss(False)


class _HelpScreen(ModalScreen):
    """Full-screen help overlay — press ? or Esc to close."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close", priority=True),
        Binding("question_mark", "dismiss", "Close", priority=True),
    ]

    CSS = """
    _HelpScreen {
        align: center middle;
    }
    #_help_outer {
        width: 114;
        height: 90vh;
        background: $panel;
        border: round $primary;
        padding: 0;
    }
    #_help_scroll {
        padding: 1 3;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="_help_outer"):
            with VerticalScroll(id="_help_scroll"):
                yield Static(_help_content(), markup=True)

    def on_key(self, event) -> None:
        if event.key in ("q", "question_mark", "escape"):
            self.dismiss()
        elif event.key == "d":
            self.dismiss()
            self.app.action_demo()


def _help_content() -> str:
    return """\
[bold white]  Resonance[/bold white]   [dim]supervised agentic delivery pipeline[/dim]

[bold cyan]─── Overview ───────────────────────────────────────────────────────────────[/bold cyan]

  Resonance monitors your Linear project for issues in [bold bright_green]Plan Approved[/bold bright_green] state,
  spawns a Claude Code agent per issue, and manages the full execution lifecycle.
  Two human gates are mandatory: [bold]plan approval[/bold] and [bold]PR review[/bold]. Everything else
  is automated.

[bold cyan]─── How to prepare a ticket ────────────────────────────────────────────────[/bold cyan]

  [bold white]1. Apply a task label[/bold white]  (at least one required — determines agent skill set)

     [bold bright_green]frontend[/bold bright_green]   UI component, page, or interaction
     [bold bright_green]backend[/bold bright_green]    API endpoint, service, data model, integration
     [bold bright_green]design[/bold bright_green]     Figma spec → built component (requires Figma link)
     [bold bright_green]bug[/bold bright_green]        Combine with [bold]frontend[/bold] or [bold]backend[/bold] to route bug fixes

  [bold white]2. Write a good description[/bold white]

     Good issues have a [bold]Goal[/bold] sentence, [bold]Acceptance Criteria[/bold] (bullet list of
     testable conditions), and [bold]Technical Notes[/bold] (files to touch, patterns to follow,
     APIs to use). Bad issues say "fix the button" or "see Slack for context".

     [dim]Tip: run /resonance-kickoff in Claude Code to create structured issues[/dim]
     [dim]     automatically from a project description.[/dim]

  [bold white]3. Move to Plan Approved[/bold white]

     The orchestrator only picks up issues in this state. Moving an issue here
     is your explicit authorisation for an agent to start working on it.
     The orchestrator re-validates the state before starting — fail-closed.

  [bold white]4. Good ticket size[/bold white]

     Each issue = one agent session = one PR.
     Target [bold]3–8 hours[/bold] of work. Too small wastes session overhead.
     Too large won't complete in one go. One endpoint, one page, one migration.

[bold cyan]─── Workflow states ────────────────────────────────────────────────────────[/bold cyan]

  [dim]You control →[/dim]  [bold bright_green]Plan Approved[/bold bright_green]        Move here to authorise execution
  [dim]Orchestrator →[/dim] [bold cyan]In Progress[/bold cyan]           Agent is actively working
  [dim]Orchestrator →[/dim] [bold yellow]Agent Feedback Needed[/bold yellow]  Agent paused — needs your input
  [dim]Orchestrator →[/dim] [bold magenta]Human Review[/bold magenta]          PR open — your review required
  [dim]You control →[/dim]  [bold white]Done[/bold white]                  Merge + close; workspace cleaned up
  [dim]Orchestrator →[/dim] [bold red]Todo[/bold red]                  Returned on failure after 3 attempts

[bold cyan]─── Human gates ────────────────────────────────────────────────────────────[/bold cyan]

  [bold]Gate 1 — Plan Approved[/bold]   You move the issue. The agent won't start without it.
  [bold]Gate 2 — Human Review[/bold]    Agent signals done → PR opens → you review and merge.

  The system is designed to be [bold]fail-closed[/bold]: if anything is ambiguous, the
  agent pauses and asks. You can always send feedback, approve, or abort.

[bold cyan]─── TUI keyboard shortcuts ─────────────────────────────────────────────────[/bold cyan]

  [dim]General[/dim]
  [bold white]q[/bold white]    Quit                        [bold white]r[/bold white]    Refresh state
  [bold white]l[/bold white]    Refresh Linear pipeline     [bold white]p[/bold white]    Set or change project scope
  [bold white]Tab[/bold white]  Cycle run selection         [bold white]?[/bold white]    This help screen

  [dim]Run actions[/dim]  [dim](press Tab to select a run first — it shows [/dim][bold white]>[/bold white][dim] prefix)[/dim]
  [bold white]f[/bold white]    Send feedback to agent      [bold white]a[/bold white]    Approve / resume selected run
  [bold white]x[/bold white]    Abort selected run          [bold white]v[/bold white]    Toggle raw log viewer

[bold cyan]─── Demo ───────────────────────────────────────────────────────────────────[/bold cyan]

  [bold white]d[/bold white]    Launch the full pipeline walkthrough

  Creates a [bold cyan]plan[/bold cyan] issue in [bold white]Todo[/bold white] in your active project — labelled [bold cyan]plan[/bold cyan] + [bold yellow]RES[/bold yellow].
  You review it in Linear, then move it to [bold bright_green]Plan Approved[/bold bright_green] to kick off.

  [dim]What happens next:[/dim]
  [dim]  1.  Planning Agent decomposes the plan into phase issues[/dim]
  [dim]  2.  Phase issues run automatically (one worktree each)[/dim]
  [dim]  3.  Each phase moves to Human Review when complete[/dim]

  [dim]The plan:[/dim]  build [bold white]demo/hello-world.html[/bold white] — 3 phases: Scaffold → Style → Commit

  [dim]Requirements:[/dim]
  [dim]  ·  Orchestrator running     (● orch green in the header)[/dim]
  [dim]  ·  Project scope set        (set in demo modal, or press p)[/dim]
  [dim]  ·  Labels "plan" + "RES"    (run resonance fix if missing)[/dim]

[bold cyan]─── CLI commands ───────────────────────────────────────────────────────────[/bold cyan]

  [bold white]resonance doctor[/bold white]              Validate all credentials and configuration
  [bold white]resonance status[/bold white]              Show all active runs with state
  [bold white]resonance approve QO-42[/bold white]       Resume a run waiting for approval
  [bold white]resonance feedback QO-42 "…"[/bold white]  Send a message to a waiting agent
  [bold white]resonance abort QO-42[/bold white]         Stop a run permanently
  [bold white]resonance logs QO-42[/bold white]          Tail the raw agent log
  [bold white]resonance plan[/bold white]                Interactively create issues in Linear
  [bold white]resonance project list[/bold white]        List available Linear projects
  [bold white]resonance project set [url][/bold white]   Scope to a specific project

[bold cyan]─── Starting the orchestrator ──────────────────────────────────────────────[/bold cyan]

  [bold white]./onair.sh[/bold white]                    Start with current project scope
  [bold white]./onair.sh --project[/bold white]          Pick project interactively before starting
  [bold white]./onair.sh --project [url][/bold white]    Set a specific project then start
  [bold white]./onair.sh --clear-project[/bold white]    Remove project scope (monitor all team issues)

  The orchestrator keeps running in the background. Closing this TUI does not
  stop it. Re-open with [bold white]./onair.sh[/bold white] — it reattaches to the running process.

[bold cyan]─── Good ticket checklist ──────────────────────────────────────────────────[/bold cyan]

  [bold bright_green]☑[/bold bright_green]  Title is specific  ("Add POST /auth/login endpoint"  not  "build auth")
  [bold bright_green]☑[/bold bright_green]  Description has clear acceptance criteria
  [bold bright_green]☑[/bold bright_green]  At least one label:  frontend / backend / design / bug
  [bold bright_green]☑[/bold bright_green]  Scope is one agent session: 3–8 hours of work
  [bold bright_green]☑[/bold bright_green]  Self-contained: no "see Slack" or "ask Alice" references
  [bold red]☒[/bold red]  Do not scope an entire feature in one issue
  [bold red]☒[/bold red]  Do not move to Plan Approved before the description is complete

[dim]  Press Esc · ? · q  to close     Press d  to launch the demo[/dim]
"""


# ── Bootstrap ─────────────────────────────────────────────────────────────────

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

STATE_FILE  = Path("runs/state.json")
EVENTS_FILE = Path("runs/events.jsonl")
EVENTS_TAIL = 300
HISTORY_LEN = 20

# ── Color tables ──────────────────────────────────────────────────────────────

_STATUS: dict[str, tuple[str, str]] = {
    "running":       ("green",       "RUNNING"),
    "waiting_human": ("yellow",      "WAITING"),
    "needs_input":   ("yellow",      "NEEDS INPUT"),
    "paused":        ("dark_orange", "PAUSED"),
    "complete":      ("dark_green",  "DONE"),
    "failed":        ("red",         "FAILED"),
    "archived":      ("grey50",      "ARCHIVED"),
}

_PIPELINE_COLOR: dict[str, str] = {
    "plan approved":         "bright_green",
    "in progress":           "dark_orange",
    "agent feedback needed": "yellow",
    "needs input":           "yellow",
    "human review":          "magenta",
    "in review":             "magenta",
    "backlog":               "grey50",
    "todo":                  "grey50",
    "done":                  "bright_green",
    "cancelled":             "red",
}

_PIPELINE_ORDER = [
    "in progress",
    "agent feedback needed",
    "human review",
    "plan approved",
]

_GLYPH_COLOR: dict[str, str] = {
    "run_started":       "cyan",
    "run_complete":      "green",
    "run_failed":        "red",
    "run_aborted":       "red",
    "run_retry":         "yellow",
    "run_paused":        "dark_orange",
    "run_approved":      "bright_green",
    "feedback_received": "yellow",
    "worker_stalled":    "red",
}

_REVIEW_STATES   = {"human review", "in review"}
_SYSTEM_EVENTS   = {"orchestrator_started", "orchestrator_stopping"}
_ACTIVE_STATUSES = {"running", "waiting_human", "needs_input", "paused"}
_SPINNER_FRAMES  = "⠋⠙⠸⠴⠦⠇"

# ── Pure helpers ──────────────────────────────────────────────────────────────

def _normalize_project_url(url: str) -> str:
    """
    Strip Linear UI tab suffixes from a project URL so matching works regardless
    of which tab the user copied the URL from.
    e.g. .../project/slug/overview  → .../project/slug
         .../project/slug/issues    → .../project/slug
    """
    import re
    # Remove trailing slash, then strip known Linear tab path segments
    url = url.rstrip("/")
    url = re.sub(r'/(?:overview|issues|members|settings|cycles|roadmap|docs|updates)$', '', url)
    return url


def _resolve_project(url_or_id: str) -> tuple[str, str] | None:
    """
    Resolve a Linear project URL or UUID to (project_id, project_name).
    Returns None if no match found.

    Resolution order:
    1. Exact URL match against project.url field (after stripping tab suffixes)
    2. Project URL is a prefix of the input URL (handles extra path segments)
    3. Hex-suffix match against project UUID
    4. Direct UUID match
    5. get_project() by UUID
    """
    import re
    from orchestrator.linear_client import LinearClient
    from orchestrator.config import load_config
    cfg      = load_config()
    client   = LinearClient(cfg.linear_api_key)
    projects = client.get_projects(cfg.linear_team_id)

    project_id   = None
    project_name = None

    normalized = _normalize_project_url(url_or_id)

    # 1. Exact URL match (after normalizing tab suffix)
    matched = next((p for p in projects if p.get("url", "").rstrip("/") == normalized), None)
    if matched:
        project_id, project_name = matched["id"], matched["name"]

    # 2. Project URL is a prefix of what the user pasted (extra path segments ok)
    if not project_id:
        matched = next(
            (p for p in projects
             if normalized.startswith(p.get("url", "").rstrip("/"))),
            None,
        )
        if matched:
            project_id, project_name = matched["id"], matched["name"]

    # 3. Hex-suffix match (for UUIDs embedded in slugs like /project/resonance-abc1def2)
    if not project_id:
        url_match = re.search(r'/project/([^/?#]+)', url_or_id, re.I)
        if url_match:
            slug      = url_match.group(1)
            hex_parts = [p for p in slug.split("-") if len(p) >= 4 and all(c in "0123456789abcdef" for c in p)]
            hex_suffix = hex_parts[-1] if hex_parts else ""
            if hex_suffix:
                matched = next(
                    (p for p in projects if p["id"].replace("-", "").endswith(hex_suffix)),
                    None,
                )
                if matched:
                    project_id, project_name = matched["id"], matched["name"]

    # 4. Direct UUID match
    if not project_id:
        matched = next((p for p in projects if p["id"] == url_or_id), None)
        if matched:
            project_id, project_name = matched["id"], matched["name"]

    # 5. get_project() UUID lookup
    if not project_id:
        try:
            proj = client.get_project(url_or_id)
            if proj:
                project_id, project_name = proj["id"], proj["name"]
        except Exception:
            pass

    client.close()
    if project_id:
        return project_id, project_name
    return None


def _archive_session(prev_project_id: str) -> str | None:
    """
    Archive the current session to runs/sessions/<project-id>-<timestamp>.md.
    Returns the archive path, or None if there was nothing to archive.
    """
    state_path  = Path("runs/state.json")
    events_path = Path("runs/events.jsonl")
    if not state_path.exists():
        return None

    try:
        runs = json.loads(state_path.read_text())
    except Exception:
        return None
    if not runs:
        return None

    # Collect events for timeline
    events: list[dict] = []
    if events_path.exists():
        for line in events_path.read_text().splitlines():
            try:
                events.append(json.loads(line))
            except Exception:
                pass

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    sessions_dir = Path("runs/sessions")
    sessions_dir.mkdir(parents=True, exist_ok=True)
    archive_path = sessions_dir / f"{prev_project_id}-{ts}.md"

    first_ts = events[0].get("ts", "") if events else ""
    last_ts  = events[-1].get("ts", "") if events else ""

    lines = [
        f"# Session Archive — {prev_project_id}",
        f"",
        f"**Archived**: {ts}",
        f"**Period**: {first_ts[:19]} → {last_ts[:19]}",
        f"**Issues worked**: {len(runs)}",
        f"",
        f"## Runs",
        f"",
        f"| Issue | Status | Task type | Attempts | Artifacts |",
        f"|-------|--------|-----------|----------|-----------|",
    ]
    for issue_id, run in sorted(runs.items()):
        status    = run.get("status", "?")
        task_type = run.get("task_type", "?")
        attempts  = run.get("attempt", 0)
        artifacts = ", ".join(f"{k}={v}" for k, v in run.get("artifacts", {}).items()) or "—"
        lines.append(f"| {issue_id} | {status} | {task_type} | {attempts} | {artifacts} |")

    # Counts
    statuses = [r.get("status") for r in runs.values()]
    completed = sum(1 for s in statuses if s in ("complete", "waiting_human", "archived"))
    failed    = sum(1 for s in statuses if s == "failed")
    lines += [
        f"",
        f"## Summary",
        f"",
        f"- Completed / human-reviewed: {completed}",
        f"- Failed: {failed}",
        f"- Total: {len(runs)}",
        f"",
        f"## How to Resume",
        f"",
        f"To restore this project context:",
        f"```bash",
        f"# Set project back in TUI with p, then paste:",
        f"# Project ID: {prev_project_id}",
        f"```",
        f"",
        f"Run histories are in `runs/logs/`. Memory files in `runs/memory/`.",
    ]

    archive_path.write_text("\n".join(lines) + "\n")
    return str(archive_path)


def _orch_alive() -> bool:
    pid_file = Path("runs/orchestrator.pid")
    if not pid_file.exists():
        return False
    try:
        pid = int(pid_file.read_text().strip())
        os.kill(pid, 0)
        return True
    except (ValueError, OSError):
        return False


def _status_cell(status: str) -> Text:
    color, label = _STATUS.get(status, ("grey50", status.upper()))
    t = Text()
    if status == "running":
        frame = _SPINNER_FRAMES[int(time.monotonic() * 3) % len(_SPINNER_FRAMES)]
        t.append(f"{frame} ", style=f"bold {color}")
    else:
        t.append("● ", style=color)
    t.append(label, style=f"bold {color}")
    return t


def _time_ago(iso: str) -> str:
    if not iso:
        return "—"
    try:
        dt   = datetime.fromisoformat(iso[:19].replace("T", " "))
        diff = max(0, (datetime.now(timezone.utc).replace(tzinfo=None) - dt).total_seconds())
        if diff < 60:   return f"{int(diff)}s"
        if diff < 3600: return f"{int(diff / 60)}m"
        return f"{int(diff / 3600)}h"
    except Exception:
        return iso[11:16] if len(iso) > 10 else iso


def _uptime(started: datetime) -> str:
    diff = int((datetime.now(timezone.utc).replace(tzinfo=None) - started).total_seconds())
    if diff < 60:   return f"{diff}s"
    if diff < 3600: return f"{diff // 60}m {diff % 60}s"
    h, m = diff // 3600, (diff % 3600) // 60
    return f"{h}h {m}m"


def _history_strip(events: list[dict], issue_id: str) -> Text:
    relevant = [e for e in events if e.get("issue") == issue_id][-HISTORY_LEN:]
    if not relevant:
        return Text("─" * 10, style="grey23")
    t = Text()
    for ev in relevant:
        color = next(
            (c for k, c in _GLYPH_COLOR.items() if k in ev.get("type", "")),
            "grey50",
        )
        t.append("■", style=color)
    return t


def _event_color(etype: str) -> str:
    if any(x in etype for x in ("fail", "error", "abort", "stall")): return "red"
    if any(x in etype for x in ("complete", "success", "approved")):  return "bright_green"
    if any(x in etype for x in ("waiting", "paused", "feedback")):    return "yellow"
    if "started" in etype:                                              return "cyan"
    return "white"


def _section_header(left: Text, right: Optional[Text] = None) -> Table:
    t = Table(show_header=False, show_edge=False, box=None, padding=(0, 0), expand=True)
    t.add_column("left", ratio=1)
    t.add_column("right", justify="right", no_wrap=True)
    t.add_row(left, right or Text())
    return t

# ── Section renderers ─────────────────────────────────────────────────────────

def _header_bar(runs: dict) -> Text:
    c: dict[str, int] = {}
    for r in runs.values():
        s = r.get("status", "")
        c[s] = c.get(s, 0) + 1
    running = c.get("running", 0)
    waiting = c.get("waiting_human", 0)
    failed  = c.get("failed", 0)
    alive   = _orch_alive()

    t = Text()
    t.append("  ")
    t.append("● orch  ", style="bold green" if alive else "bold red")
    t.append("  ")
    t.append(f"● {running} running  ", style="bold green"  if running else "grey50")
    t.append(f"● {waiting} waiting  ", style="bold yellow" if waiting else "grey50")
    t.append(f"● {failed} failed",     style="bold red"    if failed  else "grey50")
    return t


def _attention_section(
    runs: dict,
    issues: Optional[list[dict]],
) -> Optional[Group]:
    """Returns a renderable only when human action is needed; None otherwise."""
    items: list[tuple[str, str, str]] = []  # (kind, issue_id, message)

    for issue_id, run in runs.items():
        if run.get("status") == "waiting_human":
            q = run.get("pending_question") or "Agent is waiting for your input"
            items.append(("feedback", issue_id, q[:60]))

    if issues:
        for issue in issues:
            state_name = issue.get("state", {}).get("name", "").lower()
            if state_name in _REVIEW_STATES:
                title = issue.get("title", "")[:52]
                items.append(("review", issue.get("identifier", "?"), title))

    if not items:
        return None

    header = _section_header(
        Text("  ⚠  Needs Your Attention", style="bold yellow"),
        Text(f"  {len(items)} item{'s' if len(items) != 1 else ''}  ", style="dim yellow"),
    )

    table = Table(
        show_header=False,
        box=None,
        show_edge=False,
        padding=(0, 1),
        expand=True,
    )
    table.add_column("Icon",    width=3)
    table.add_column("Issue",   style="bold cyan", width=10)
    table.add_column("Message", ratio=1)
    table.add_column("Action",  justify="right", style="dim", width=26, no_wrap=True)

    for kind, issue_id, msg in items:
        if kind == "feedback":
            icon   = Text("⏸ ", style="bold yellow")
            msg_t  = Text(msg, style="yellow")
            action = Text("[f] feedback   [a] approve", style="dim")
        else:
            icon   = Text("● ", style="bold magenta")
            msg_t  = Text(msg, style="magenta")
            action = Text("→ Human Review  [Enter] details", style="dim")
        table.add_row(icon, issue_id, msg_t, action)

    return Group(header, table)


def _runs_section(
    runs: dict,
    events: list[dict],
    started_at: datetime,
    selected_id: Optional[str] = None,
) -> Group:
    started_n  = sum(1 for e in events if e.get("type") == "run_started")
    complete_n = sum(1 for e in events if e.get("type") == "run_complete")
    failed_n   = sum(1 for e in events
                     if "fail" in e.get("type", "") or "abort" in e.get("type", ""))

    session_t = Text()
    session_t.append(f"↑ {started_n}  ",  style="bold cyan"  if started_n  else "grey50")
    session_t.append(f"✓ {complete_n}  ", style="bold green"  if complete_n else "grey50")
    session_t.append(f"✗ {failed_n}  ",   style="bold red"    if failed_n   else "grey50")
    session_t.append("up ",               style="dim")
    session_t.append(_uptime(started_at), style="bold white")

    header = _section_header(Text("  Active Runs", style="bold white"), session_t)

    active = {k: v for k, v in runs.items() if v.get("status") in _ACTIVE_STATUSES}

    if not active:
        idle = Text()
        idle.append("  ● idle", style="grey50")
        idle.append("   —   move an issue to ", style="dim")
        idle.append("Plan Approved", style="bold cyan")
        idle.append(" to begin", style="dim")
        return Group(header, idle)

    table = Table(
        show_header=True,
        header_style="bold dim",
        box=rich_box.SIMPLE_HEAD,
        show_edge=False,
        padding=(0, 1),
        expand=True,
    )
    table.add_column("Issue",   width=12)
    table.add_column("Status",  width=14)
    table.add_column("Task",    width=14, style="dim")
    table.add_column("Iter",    width=5,  style="dim", justify="center")
    table.add_column("Detail",  width=30, style="dim")
    table.add_column("Time",    width=8)

    for issue_id, run in sorted(
        active.items(),
        key=lambda x: x[1].get("started_at", ""),
        reverse=True,
    ):
        is_sel = issue_id == selected_id
        id_t   = Text()
        id_t.append("> " if is_sel else "  ", style="bold white")
        id_t.append(issue_id, style="bold cyan")

        detail = run.get("branch", "—")
        if run.get("status") == "waiting_human":
            detail = "⏸ waiting for review"
        elif run.get("status") == "running":
            iter_n = run.get("iteration", 1)
            detail = f"iter {iter_n}  ·  {run.get('branch', '—')}"

        table.add_row(
            id_t,
            _status_cell(run.get("status", "?")),
            run.get("task_type", "—"),
            f"{run.get('attempt', 1)}/3",
            detail,
            _time_ago(run.get("started_at", "")),
        )
        if q := run.get("pending_question"):
            q_t = Text()
            q_t.append("    ⏸  ", style="bold yellow")
            q_t.append((q[:58] + "…") if len(q) > 58 else q, style="yellow")
            table.add_row("", q_t, "", "", "", "", "")

    hint_t = Text()
    hint_t.append("[tab] select  ", style="dim")
    if selected_id:
        run = active.get(selected_id, {})
        if run.get("status") == "waiting_human":
            hint_t.append("[f] feedback  [a] approve  ", style="dim yellow")
        hint_t.append("[enter] detail  [x] abort  [v] log  ", style="dim")
    hint_t.append("[enter] detail  [c] clean", style="dim")

    return Group(header, table, hint_t)


def _pipeline_section(
    issues: Optional[list[dict]],
    error: Optional[str],
    project_name: Optional[str],
    last_poll_at: Optional[datetime] = None,
) -> Group:
    title_t = Text()
    title_t.append("  Linear Pipeline", style="bold white")
    if project_name:
        title_t.append(f"  ·  {project_name}", style="dim cyan")

    right_t = Text()
    if last_poll_at:
        diff = int(
            (datetime.now(timezone.utc).replace(tzinfo=None) - last_poll_at).total_seconds()
        )
        if diff < 60:
            right_t.append(f"↺ {diff}s ago  ", style="dim")
        else:
            right_t.append(f"↺ {diff // 60}m ago  ", style="dim yellow")
    right_t.append("[l] ↺  ", style="dim")

    header = _section_header(title_t, right_t)

    table = Table(
        show_header=True,
        header_style="bold dim",
        box=rich_box.SIMPLE_HEAD,
        show_edge=False,
        padding=(0, 1),
        expand=True,
    )
    table.add_column("Issue",    style="dim cyan", width=10)
    table.add_column("Title",    width=44)
    table.add_column("State",    width=26)
    table.add_column("Assignee", width=14, style="dim")
    table.add_column("Updated",  width=10, style="dim")

    if error:
        table.add_row("", Text(f"  ✗ {error[:52]}", style="dim red"), "", "", "")
    elif issues is None:
        table.add_row("", Text("  Fetching…", style="dim"), "", "", "")
    elif not issues:
        table.add_row("", Text("  No issues in pipeline states", style="dim"), "", "", "")
    else:
        def _rank(issue: dict) -> int:
            name = issue.get("state", {}).get("name", "").lower()
            try:   return _PIPELINE_ORDER.index(name)
            except ValueError: return len(_PIPELINE_ORDER)

        for issue in sorted(issues, key=_rank):
            state_name = issue.get("state", {}).get("name", "?")
            state_lower = state_name.lower()
            if "done" in state_lower:
                glyph, color = "✓ ", "bright_green"
            elif "cancel" in state_lower or "duplicate" in state_lower:
                glyph, color = "✗ ", "red"
            else:
                color = _PIPELINE_COLOR.get(state_lower, "white")
                glyph = "● "
            state_t = Text()
            state_t.append(glyph, style=color)
            state_t.append(state_name, style=color)

            title  = issue.get("title", "")
            title_t = Text((title[:42] + "…") if len(title) > 42 else title)

            table.add_row(
                issue.get("identifier", ""),
                title_t,
                state_t,
                (issue.get("assignee") or {}).get("name", "—"),
                _time_ago(issue.get("updatedAt", "")),
            )

    return Group(header, table)

# ── Performance stats ─────────────────────────────────────────────────────────

_SPARK = " ▁▂▃▄▅▆▇█"


def _sparkline(values: list[int]) -> Text:
    max_v = max(values) if values else 0
    if not max_v:
        return Text("▁" * len(values), style="grey23")
    t = Text()
    for v in values:
        idx   = min(8, round(v / max_v * 8))
        style = "cyan" if v > 0 else "grey23"
        t.append(_SPARK[idx], style=style)
    return t


def _gauge(pct: int, width: int = 20) -> Text:
    filled = round(pct / 100 * width)
    color  = "bright_green" if pct >= 75 else "yellow" if pct >= 50 else "red"
    t = Text()
    t.append("█" * filled,          style=color)
    t.append("░" * (width - filled), style="grey23")
    return t


def _fmt_dur(seconds: int) -> str:
    if seconds < 60:   return f"{seconds}s"
    if seconds < 3600: return f"{seconds // 60}m {seconds % 60}s"
    h, m = seconds // 3600, (seconds % 3600) // 60
    return f"{h}h {m}m"


def _compute_stats(events: list[dict]) -> dict:
    now       = datetime.now(timezone.utc).replace(tzinfo=None).timestamp()
    cut_24h   = now - 86400
    cut_12h   = now - 43200

    completed = failed = retried = 0
    hourly: list[int]       = [0] * 12
    starts: dict[str, float] = {}
    durations: list[float]   = []

    for ev in events:
        try:
            ts = datetime.fromisoformat(
                ev.get("ts", "")[:19].replace("T", " ")
            ).timestamp()
        except Exception:
            continue
        if ts < cut_24h:
            continue

        etype = ev.get("type", "")
        issue = ev.get("issue", "")

        if   etype == "run_complete":              completed += 1
        elif etype in {"run_failed", "run_aborted"}: failed    += 1
        elif etype == "run_retry":                 retried   += 1
        elif etype == "run_started":               starts[issue] = ts

        if etype == "run_complete" and issue in starts:
            dur = ts - starts[issue]
            if dur > 0:
                durations.append(dur)

        if etype == "run_started" and ts >= cut_12h:
            bucket = 11 - min(11, int((now - ts) / 3600))
            hourly[bucket] += 1

    total       = completed + failed
    success_pct = round(completed / total * 100) if total else 0
    avg_dur     = int(sum(durations) / len(durations)) if durations else 0

    return {
        "completed":   completed,
        "failed":      failed,
        "retried":     retried,
        "total":       total,
        "success_pct": success_pct,
        "hourly":      hourly,
        "avg_dur":     avg_dur,
    }


def _stats_section(events: list[dict]) -> Group:
    s = _compute_stats(events)

    header = _section_header(
        Text("  Performance", style="bold white"),
        Text("  24h window  ", style="dim"),
    )

    if s["total"] == 0:
        empty = Text()
        empty.append("  No run history yet — stats appear after the first completed run", style="dim")
        return Group(header, empty)

    pct       = s["success_pct"]
    pct_style = "bold bright_green" if pct >= 75 else "bold yellow" if pct >= 50 else "bold red"

    row1 = Text.assemble(
        "  ",
        _gauge(pct, 20),
        (f"  {pct}%  ", pct_style),
        ("✓ ", "green"),
        (str(s["completed"]), "bold white"),
        ("  ✗ ", "red"),
        (str(s["failed"]), "bold white"),
        ("  ⟳ ", "yellow"),
        (f"{s['retried']} retried", "dim"),
    )
    if s["avg_dur"] > 0:
        row1.append("   avg ", style="dim")
        row1.append(_fmt_dur(s["avg_dur"]), style="bold white")

    row2 = Text.assemble(
        "  Activity (12h)  ",
        _sparkline(s["hourly"]),
        ("  oldest → newest", "grey23"),
    )

    return Group(header, row1, row2)

# ── Linear background poller ──────────────────────────────────────────────────

class _LinearPoller:
    INTERVAL = 30

    def __init__(self) -> None:
        self._issues:       Optional[list[dict]] = None
        self._error:        Optional[str]        = None
        self._project_name: Optional[str]        = None
        self._last_poll_at: Optional[datetime]   = None
        self._lock         = threading.Lock()
        self._stop         = threading.Event()
        self._callback     = None

    def set_callback(self, cb) -> None:
        self._callback = cb

    def start(self) -> None:
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self) -> None:
        self._stop.set()

    def get(self) -> tuple[
        Optional[list[dict]], Optional[str], Optional[str], Optional[datetime]
    ]:
        with self._lock:
            return self._issues, self._error, self._project_name, self._last_poll_at

    def _run(self) -> None:
        while not self._stop.is_set():
            self._fetch()
            self._stop.wait(self.INTERVAL)

    def _fetch(self) -> None:
        try:
            from orchestrator.linear_client import LinearClient
            from orchestrator.config import load_config
            cfg    = load_config()
            client = LinearClient(cfg.linear_api_key)
            states = [
                cfg.state_eligibility,
                cfg.state_in_progress,
                cfg.state_feedback,
                cfg.state_review,
            ]
            issues = client.get_pipeline_issues(
                cfg.linear_team_id, states, project_id=cfg.linear_project_id
            )
            project_name = None
            if cfg.linear_project_id:
                try:
                    proj = client.get_project(cfg.linear_project_id)
                    project_name = proj["name"] if proj else None
                except Exception:
                    pass
            client.close()
            with self._lock:
                self._issues       = issues
                self._error        = None
                self._project_name = project_name
                self._last_poll_at = datetime.now(timezone.utc).replace(tzinfo=None)
        except Exception as exc:
            with self._lock:
                self._error = str(exc)[:80]
        if self._callback:
            self._callback()

# ── App ───────────────────────────────────────────────────────────────────────

class ResonanceDashboard(App):

    CSS = """
    Screen {
        layout: vertical;
        background: $surface;
    }

    #header_bar {
        height: 1;
        background: $panel;
        padding: 0 0;
    }

    #attention_section {
        height: auto;
        padding: 1 1 0 1;
        margin-bottom: 1;
    }

    #runs_section {
        height: auto;
        padding: 1 1 0 1;
    }

    #pipeline_section {
        height: auto;
        padding: 1 1 0 1;
    }

    #stats_section {
        height: auto;
        padding: 1 1 0 1;
        border-top: solid $panel-lighten-2;
        margin-top: 1;
    }

    #events_section {
        height: 1fr;
        padding: 1 2 0 2;
        border-top: solid $panel-lighten-2;
        margin: 1 0 0 0;
    }

    #events_label {
        height: 1;
        color: $text-muted;
        text-style: bold;
    }

    #events_log {
        height: 1fr;
    }
    """

    TITLE     = "Resonance"
    SUB_TITLE = "supervised agentic delivery"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("q",             "quit",           "Quit",     priority=True),
        Binding("r",             "manual_refresh", "Refresh"),
        Binding("l",             "refresh_linear", "Linear ↺"),
        Binding("p",             "set_project",    "Project"),
        Binding("tab",           "select_next",    "Select"),
        Binding("enter",         "detail",         "Detail",   show=False),
        Binding("c",             "cleanup",        "Cleanup",  show=False),
        Binding("f",             "feedback",       "Feedback"),
        Binding("a",             "approve",        "Approve"),
        Binding("x",             "abort",          "Abort"),
        Binding("v",             "toggle_log",     "Log"),
        Binding("question_mark", "help",           "Help"),
        Binding("d",             "demo",           "Demo",     show=False),
        Binding("e",             "event_browser",  "Events",   show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._started_at    = datetime.now(timezone.utc).replace(tzinfo=None)
        self._linear        = _LinearPoller()
        self._selected_id: Optional[str] = None
        self._log_mode:    bool          = False
        self._cached_runs:   dict        = {}
        self._cached_events: list        = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("", id="header_bar")
        yield Static("", id="attention_section")
        yield Static("", id="runs_section")
        yield Static("", id="pipeline_section")
        yield Static("", id="stats_section")
        yield Vertical(
            Static("  Event Stream", id="events_label"),
            _EventLog(id="events_log", highlight=True, markup=True, auto_scroll=True),
            id="events_section",
        )
        yield Footer()

    def on_mount(self) -> None:
        self._linear.set_callback(lambda: self.call_from_thread(self._draw_pipeline))
        self._linear.start()
        self.set_interval(2.0, self._tick)
        self.set_interval(0.2, self._tick_spinner)
        self._tick()

    def on_unmount(self) -> None:
        self._linear.stop()

    # ── Data ─────────────────────────────────────────────────────────────────

    def _state(self) -> dict:
        if not STATE_FILE.exists(): return {}
        try: return json.loads(STATE_FILE.read_text())
        except Exception: return {}

    def _events(self) -> list[dict]:
        if not EVENTS_FILE.exists(): return []
        try:
            lines = EVENTS_FILE.read_text().strip().splitlines()[-EVENTS_TAIL:]
            out = []
            for ln in lines:
                try: out.append(json.loads(ln))
                except Exception: pass
            return out
        except Exception: return []

    # ── Draw ──────────────────────────────────────────────────────────────────

    def _tick(self) -> None:
        runs   = self._state()
        events = self._events()
        self._cached_runs   = runs
        self._cached_events = events

        # Invalidate selection if run is no longer active
        active_ids = {k for k, v in runs.items() if v.get("status") in _ACTIVE_STATUSES}
        if self._selected_id not in active_ids:
            self._selected_id = None
            self._log_mode    = False

        self.query_one("#header_bar", Static).update(_header_bar(runs))
        self._update_attention(runs)
        self.query_one("#runs_section", Static).update(
            _runs_section(runs, events, self._started_at, self._selected_id)
        )
        self.query_one("#stats_section", Static).update(
            _stats_section(events)
        )

        if self._log_mode and self._selected_id:
            self._draw_log_view(runs)
        else:
            self._draw_events(events)

    def _tick_spinner(self) -> None:
        """Fast refresh for spinner animation — uses cached data, no I/O."""
        runs = self._cached_runs
        if not any(v.get("status") == "running" for v in runs.values()):
            return
        self.query_one("#runs_section", Static).update(
            _runs_section(runs, self._cached_events, self._started_at, self._selected_id)
        )

    def _draw_pipeline(self) -> None:
        issues, error, project_name, last_poll_at = self._linear.get()
        self.query_one("#pipeline_section", Static).update(
            _pipeline_section(issues, error, project_name, last_poll_at)
        )
        runs = self._state()
        self._update_attention(runs)

    def _update_attention(self, runs: dict) -> None:
        issues, *_ = self._linear.get()
        attention  = _attention_section(runs, issues)
        widget     = self.query_one("#attention_section", Static)
        if attention:
            widget.display = True
            widget.update(attention)
        else:
            widget.display = False

    def _draw_events(self, events: list[dict]) -> None:
        self.query_one("#events_label", Static).update("  Event Stream")
        log = self.query_one("#events_log", _EventLog)
        log.clear()
        visible = [
            ev for ev in events
            if not (ev.get("issue") == "system" and ev.get("type") in _SYSTEM_EVENTS)
        ]
        for ev in visible[-60:]:
            ts    = ev.get("ts", "")
            short = ts[11:19] if len(ts) > 10 else ts
            issue = ev.get("issue", "system")
            etype = ev.get("type", "?")
            extra = {k: v for k, v in ev.items() if k not in {"ts", "issue", "type"}}
            extra_str = (
                "  " + "  ".join(
                    f"[dim]{k}=[/dim][dim white]{str(v)[:30]}[/dim white]"
                    for k, v in extra.items()
                ) if extra else ""
            )
            color = _event_color(etype)
            log.write(
                f"[dim]{short}[/dim]  "
                f"[bold cyan]{issue:<12}[/bold cyan]  "
                f"[{color}]{etype:<28}[/{color}]"
                f"{extra_str}"
            )

    def _draw_log_view(self, runs: dict) -> None:
        run = runs.get(self._selected_id or "")
        if not run:
            self._log_mode = False
            return
        self.query_one("#events_label", Static).update(
            f"  Log — {self._selected_id}   [dim]v to return to event stream[/dim]"
        )
        log_file = Path(run.get("log_file", ""))
        log = self.query_one("#events_log", _EventLog)
        log.clear()
        if not log_file.exists():
            log.write(f"[dim]No log file yet: {log_file}[/dim]")
            return
        try:
            lines = log_file.read_text().splitlines()[-60:]
            for line in lines:
                escaped = line.replace("[", r"\[")
                log.write(f"[dim white]{escaped}[/dim white]")
        except Exception as exc:
            log.write(f"[red]Error reading log: {exc}[/red]")

    # ── Key actions ───────────────────────────────────────────────────────────

    def action_help(self) -> None:
        self.push_screen(_HelpScreen())

    def action_detail(self) -> None:
        """Open detail modal for selected run or most recently updated run."""
        runs = self._state()
        if self._selected_id:
            run = runs.get(self._selected_id)
            if run:
                self.push_screen(_RunDetailScreen(self._selected_id, run))
                return
        # Prefer active runs, then fall back to any run sorted by recency
        active = {k: v for k, v in runs.items() if v.get("status") in _ACTIVE_STATUSES}
        pool = active or runs
        if pool:
            issue_id, run = max(pool.items(), key=lambda x: x[1].get("last_event_at", ""))
            self.push_screen(_RunDetailScreen(issue_id, run))

    def action_cleanup(self) -> None:
        def _on_confirm(confirmed: bool | None) -> None:
            if not confirmed:
                return
            try:
                from orchestrator import state as run_state
                result = run_state.clear_session(clear_events=True)
                msg = f"Session cleared — {result['runs_removed']} run(s) removed"
                if result["events_cleared"]:
                    msg += ", event log wiped"
                self.notify(msg, severity="information")
                # Also clear the live event log widget
                try:
                    self.query_one("#events_log").clear()
                except Exception:
                    pass
                self._tick()
            except Exception as exc:
                self.notify(f"Cleanup failed: {exc}", severity="error")
        self.push_screen(_CleanupScreen(), _on_confirm)

    def action_demo(self) -> None:
        self.push_screen(_DemoScreen())

    def action_event_browser(self) -> None:
        self.push_screen(_EventBrowserScreen(self._cached_events))

    def action_manual_refresh(self) -> None:
        self._tick()

    def action_refresh_linear(self) -> None:
        threading.Thread(target=self._linear._fetch, daemon=True).start()

    def action_select_next(self) -> None:
        runs = self._state()
        ids  = sorted(k for k, v in runs.items() if v.get("status") in _ACTIVE_STATUSES)
        if not ids:
            self.notify("No active runs", timeout=1.5)
            return
        if self._selected_id not in ids:
            self._selected_id = ids[0]
        else:
            self._selected_id = ids[(ids.index(self._selected_id) + 1) % len(ids)]
        self._tick()
        self.notify(f"Selected: {self._selected_id}", timeout=1.5)

    def action_feedback(self) -> None:
        hint = ""
        if self._selected_id:
            run = self._state().get(self._selected_id, {})
            if run.get("status") == "waiting_human":
                hint = self._selected_id

        def _on_result(result: Optional[tuple]) -> None:
            if result:
                issue_id, text = result
                threading.Thread(
                    target=self._send_feedback, args=(issue_id, text), daemon=True
                ).start()

        self.push_screen(_FeedbackScreen(issue_hint=hint), _on_result)

    def _send_feedback(self, issue_id: str, text: str) -> None:
        try:
            from orchestrator.state import post_command
            post_command(issue_id, "feedback", text=text)
            self.call_from_thread(
                self.notify, f"Feedback sent → {issue_id}", severity="information"
            )
        except Exception as exc:
            self.call_from_thread(self.notify, f"Error: {exc}", severity="error")

    def action_approve(self) -> None:
        issue_id = self._selected_id
        if not issue_id:
            self.notify("Select a run first  (Tab)", severity="warning")
            return
        run = self._state().get(issue_id, {})
        if run.get("status") != "waiting_human":
            self.notify(f"{issue_id} is not waiting for approval", severity="warning")
            return
        threading.Thread(target=self._do_approve, args=(issue_id,), daemon=True).start()

    def _do_approve(self, issue_id: str) -> None:
        try:
            from orchestrator.state import post_command
            post_command(issue_id, "approve")
            self.call_from_thread(
                self.notify, f"Approved {issue_id}", severity="information"
            )
        except Exception as exc:
            self.call_from_thread(self.notify, f"Error: {exc}", severity="error")

    def action_abort(self) -> None:
        issue_id = self._selected_id
        if not issue_id:
            self.notify("Select a run first  (Tab)", severity="warning")
            return
        threading.Thread(target=self._do_abort, args=(issue_id,), daemon=True).start()

    def _do_abort(self, issue_id: str) -> None:
        try:
            from orchestrator.state import post_command
            post_command(issue_id, "abort")
            self.call_from_thread(
                self.notify, f"Aborted {issue_id}", severity="warning"
            )
        except Exception as exc:
            self.call_from_thread(self.notify, f"Error: {exc}", severity="error")

    def action_toggle_log(self) -> None:
        if not self._selected_id:
            self.notify("Select a run first  (Tab)", severity="warning")
            return
        self._log_mode = not self._log_mode
        self._tick()

    def action_set_project(self) -> None:
        def _on_result(url_or_id: str | None) -> None:
            if url_or_id:
                threading.Thread(
                    target=self._resolve_and_set_project,
                    args=(url_or_id,),
                    daemon=True,
                ).start()
        self.push_screen(_ProjectInputScreen(), _on_result)

    def _resolve_and_set_project(self, url_or_id: str) -> None:
        try:
            result = _resolve_project(url_or_id)
            if not result:
                self.call_from_thread(
                    self.notify, f"Could not resolve: {url_or_id[:50]}", severity="error"
                )
                return

            project_id, project_name = result

            # Archive current session before switching
            from orchestrator.config import load_config
            try:
                prev_cfg = load_config()
                prev_id  = prev_cfg.linear_project_id
                if prev_id and prev_id != project_id:
                    archive_path = _archive_session(prev_id)
                    if archive_path:
                        self.call_from_thread(
                            self.notify,
                            f"Session archived → {archive_path}",
                            severity="information",
                            timeout=6,
                        )
            except Exception:
                pass

            env_path = Path(".env")
            text  = env_path.read_text() if env_path.exists() else ""
            lines = [ln for ln in text.splitlines() if not ln.startswith("LINEAR_PROJECT_ID=")]
            lines.append(f"LINEAR_PROJECT_ID={project_id}")
            env_path.write_text("\n".join(lines) + "\n")

            try:
                from dotenv import load_dotenv
                load_dotenv(override=True)
            except ImportError:
                pass

            self.call_from_thread(
                self.notify, f"Project set: {project_name}", severity="information"
            )
            self._linear._fetch()

        except Exception as exc:
            self.call_from_thread(
                self.notify, f"Error: {str(exc)[:60]}", severity="error"
            )


def main() -> None:
    ResonanceDashboard().run()


if __name__ == "__main__":
    main()
