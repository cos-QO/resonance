# WORKFLOW.md
# Queen One Agentic Pipeline — Runtime Contract
#
# This file is the machine-readable contract between the orchestrator and this repository.
# The orchestrator reads it on startup. Operators edit it to change runtime behaviour.
# Do not add logic here — only configuration and policy.
#
# Version history is tracked via git. Changes to this file affect all active runs
# on next orchestrator restart.

version: "1.0"
project: resonance

# ─────────────────────────────────────────────────────────────────────────────
# LINEAR CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

linear:
  # LINEAR_PROJECT_ID is set via .env or environment variable — not here.
  # Run: resonance setup   to configure it interactively.
  # Run: resonance doctor  to verify it is correctly set.

  # State model — these must exist as workflow states in your Linear workspace.
  # Order matters: the orchestrator understands this as a directed progression.
  states:
    - Todo                    # not yet ready for work
    - Ready for Planning      # scoping can begin
    - Plan Proposed           # agent has drafted a plan, awaiting human review
    - Plan Approved           # human approved — orchestrator picks up from here
    - In Progress             # orchestrator has claimed and started this issue
    - Agent Feedback Needed   # agent paused, waiting for human input or approval
    - Needs Input              # agent blocked, awaiting human decision
    - Human Review            # human approved the output — PR is open
    - Done                    # human-verified complete
    - Cancelled               # abandoned, workspace cleaned up

  # DECISION: Plan approval is represented as a custom Linear workflow state.
  # Rationale: queryable via API, unambiguous, visible on the board.
  # Alternative considered: label — rejected because labels can be misapplied
  # and do not appear in the workflow state filter.
  eligibility_state: "Plan Approved"

  # DECISION: Task type is determined by Linear labels applied before eligibility.
  # Rationale: explicit human signal, queryable, no agent inference needed.
  # Labels must match exactly (case-insensitive).
  labels:
    design_to_code:
      requires: [design]
      optional: [figma]
    frontend_feature:
      requires: [frontend]
      excludes: [bug]
    frontend_bug:
      requires: [bug, frontend]

# ─────────────────────────────────────────────────────────────────────────────
# PLAN APPROVAL GATE
# ─────────────────────────────────────────────────────────────────────────────

plan_approval:
  # How the orchestrator verifies an approved plan exists before starting work.
  mechanism: linear_status
  status_name: "Plan Approved"

  # fail_closed: if approval status cannot be verified, do NOT start the run.
  # This is the strongest safety control in the system. Never set to false.
  fail_closed: true

# ─────────────────────────────────────────────────────────────────────────────
# TASK TYPES
# To add a task type: add a block here. No orchestrator code changes needed.
# 'plan' is always checked first — plan issues are routed to the Planning Agent.
# ─────────────────────────────────────────────────────────────────────────────

task_types:

  # ── pep ──────────────────────────────────────────────────────────────────────
  # A Product Execution Prompt (PEP) document. When approved, the PEP Reader
  # Agent reads it and produces ONE Core Plan issue containing all plans, blocks,
  # and tasks. The Core Plan goes to Human Review. PEP issue is then marked Done.
  pep:
    detection:
      labels: [pep]
    worker: claude-opus        # strongest reasoning for PEP decomposition
    mcp:
      - linear                 # creates issues, posts comments, reads project
    description: |
      Reads a PEP document from a Linear issue.
      Creates ONE Core Plan issue (label: core-plan) as a child of the PEP issue.
      The Core Plan contains all plans, blocks, tasks, and dependencies.
      Moves Core Plan to Human Review for operator sign-off.
      Posts summary comment. Marks PEP issue Done.

  # ── core_plan ────────────────────────────────────────────────────────────────
  # A Core Plan issue (produced by PEP Reader) reviewed and approved by a human.
  # The Block Decomposer Agent reads it and creates Block sub-issues — one per
  # block — with full context, task checklists, and acceptance criteria.
  core_plan:
    detection:
      labels: [core-plan]
    worker: claude-opus        # PM-level reasoning for block decomposition
    mcp:
      - linear
    description: |
      Reads an approved Core Plan and decomposes it into Block sub-issues.
      Each Block is a child issue with tasks, acceptance criteria, and context.
      Sets blocking relations between dependent blocks.
      Moves blocks to Plan Approved. Posts summary comment.
      Core Plan moves to In Progress while blocks execute.

  # ── block ────────────────────────────────────────────────────────────────────
  # A single execution block — one agent session, one PR, 3-8 hours of work.
  # Agent implements all tasks, updates description checkboxes, self-verifies,
  # then signals block_complete → Done. Blocked → Needs Input (human decides).
  # When all sibling blocks are Done → parent plan → Human Review.
  block:
    detection:
      labels: [block]
    worker: claude-sonnet
    mcp:
      - linear
    description: |
      Implements one self-contained block. Updates description task checkboxes
      as each task completes. Self-verifies against acceptance criteria.
      block_complete → Done. Blocked → Needs Input with takeover instructions.
      When all blocks Done → plan moves to Human Review automatically.

  # ── plan ─────────────────────────────────────────────────────────────────────
  # Legacy: a plan document describing phases. Kept for backward compatibility.
  # Human creates this in Todo, then moves to Plan Approved.
  plan:
    detection:
      labels: [plan]
    worker: claude-opus      # planning needs strongest reasoning
    mcp:
      - linear               # creates issues, posts comments, sets states
    description: |
      Reads the plan document and decomposes it into Linear phase issues.
      Creates one issue per phase with correct labels, skills, and acceptance
      criteria. Moves all phase issues to Plan Approved. Posts a summary comment.

  # ── design_to_code ──────────────────────────────────────────────────────────
  # Figma reference → built component or screen. Agent reads Figma to inspect
  # designs, extract specs, and match tokens — it never writes to Figma.
  # Iterative by nature. Visual review required.
  design_to_code:
    # Agents work inside connect-ui (the real platform repo) for all frontend tasks.
    # Set CONNECT_UI_PATH in .env to the absolute path of your local connect-ui clone.
    target_repo_path: "${CONNECT_UI_PATH}"
    detection:
      labels: [design]
      # Figma link in issue description is expected but not enforced.
      # Worker will request it if missing.
    skills:
      - pd-pep             # structured input from issue
      - pd-context-pack    # broad awareness if needed
      - connectui-dev      # design system + code standards
      - pd-plan-post       # post plan to Linear for approval
      - pd-report-post     # post execution report on completion
    rules:
      - pd-guardrail       # blocks execution without approved plan
      - pd-issue-standard  # validates required fields
      - frontend.md        # frontend coding standards
    worker: claude-sonnet
    mcp:
      - linear             # always required
      - figma              # read-only: inspect designs, extract specs/tokens
    # Artifacts the agent MUST produce before Agent Feedback Needed state is valid.
    # Orchestrator will not transition state until these are present in the run log.
    artifacts_required:
      - preview_url        # agent starts dev server and posts URL to Linear
    # Optional but strongly recommended:
    artifacts_recommended:
      - figma_comparison   # side-by-side or annotation showing fidelity
    verify_level: L1       # build + lint minimum; L2 for larger components
    # Visual work requires multiple passes. Humans see it, give feedback, repeat.
    iteration_model: visual
    max_iterations: 5

  # ── frontend_feature ────────────────────────────────────────────────────────
  # New UI feature from a Linear spec. May or may not have a Figma reference.
  frontend_feature:
    target_repo_path: "${CONNECT_UI_PATH}"
    detection:
      labels: [frontend]
      excludes: [bug]
    skills:
      - pd-pep
      - pd-context-pack
      - connectui-dev
      - pd-plan-post
      - pd-report-post
    rules:
      - pd-guardrail
      - pd-issue-standard
      - frontend.md
    worker: claude-sonnet
    mcp:
      - linear
      - figma              # loaded if Figma link present; optional
    artifacts_required:
      - preview_url
    verify_level: L2       # build + lint + tests
    iteration_model: feature
    max_iterations: 3

  # ── frontend_bug ─────────────────────────────────────────────────────────────
  # UI regression or visual defect. Reproduction steps required.
  frontend_bug:
    target_repo_path: "${CONNECT_UI_PATH}"
    detection:
      labels: [bug, frontend]
    skills:
      - pd-pep
      - connectui-dev
      - pd-report-post
    rules:
      - pd-guardrail
      - pd-issue-standard
    worker: claude-sonnet
    mcp:
      - linear
    artifacts_required:
      - preview_url
      - before_after_evidence   # screenshot or description of before/after state
    verify_level: L2
    iteration_model: bug
    max_iterations: 3

  # ── backend_feature ──────────────────────────────────────────────────────────
  # API endpoints, services, data models, integrations.
  backend_feature:
    detection:
      labels: [backend]
      excludes: [bug]
    skills:
      - pd-pep
      - pd-context-pack
      - pd-plan-post
      - pd-report-post
    rules:
      - pd-guardrail
      - pd-issue-standard
      - api.md
    worker: claude-sonnet
    mcp:
      - linear
    artifacts_required:
      - test_output          # passing tests demonstrating the implementation
    verify_level: L2
    iteration_model: feature
    max_iterations: 3

  # ── backend_bug ───────────────────────────────────────────────────────────────
  # Server-side defect fix. Reproduction steps and test coverage required.
  backend_bug:
    detection:
      labels: [bug, backend]
    skills:
      - pd-pep
      - pd-report-post
    rules:
      - pd-guardrail
      - pd-issue-standard
    worker: claude-sonnet
    mcp:
      - linear
    artifacts_required:
      - test_output
    verify_level: L2
    iteration_model: bug
    max_iterations: 3

# ─────────────────────────────────────────────────────────────────────────────
# UNSUPPORTED TASK TYPES
# Issues that do not match any task type above are rejected explicitly.
# The orchestrator posts a comment and returns the issue to a neutral state.
# ─────────────────────────────────────────────────────────────────────────────

unsupported:
  action: post_comment_and_return
  return_state: Todo
  comment: |
    This issue was picked up by the Queen One orchestrator but its task type
    is not supported in the current configuration.

    Supported task types and required labels:
      pep               → label: pep  (Product Execution Prompt)
      core_plan         → label: core-plan  (created by PEP Reader, human-reviewed)
      block             → label: block  (created by Block Decomposer)
      design_to_code    → label: design
      frontend_feature  → label: frontend (without bug)
      frontend_bug      → labels: bug + frontend
      backend_feature   → label: backend (without bug)
      backend_bug       → labels: bug + backend

    To enable orchestration: add the appropriate label and move the issue
    back to Plan Approved once a plan has been reviewed and approved.

# ─────────────────────────────────────────────────────────────────────────────
# WORKSPACE POLICY
# ─────────────────────────────────────────────────────────────────────────────

workspace:
  # All worktrees are created here. Directory is gitignored.
  base_dir: workspaces/

  # Workspace paths depend on whether a project is scoped (LINEAR_PROJECT_ID set):
  #
  #   With project:   workspaces/{project-slug}/issues/{issue_id}
  #   Without project: workspaces/{team_prefix}/{issue_id}   (team-level fallback)
  #
  # {project-slug} is the Linear project name slugified (spaces/punctuation → hyphens).
  # Example (project scoped):  workspaces/D2D-Demo-gorgon/issues/RND-47
  # Example (no project):      workspaces/RND/RND-47
  naming: "{team_prefix}/{issue_id}"  # used only when no project is scoped

  # Each issue gets an isolated git worktree on its own branch.
  isolation: git_worktree
  branch_naming: "agent/{issue_id}"

  # Workspace is cleaned up when the issue reaches any of these states.
  cleanup_on:
    - Done
    - Cancelled

  # Orphan detection: workspaces older than this with no active run are flagged.
  max_age_hours: 48

  # Minimal .claude/ config written into each workspace by the orchestrator.
  # Points at the shared plugin directories. Do not duplicate content here.
  agent_config:
    # Paths are relative to the repo root. The orchestrator resolves them to
    # absolute paths when writing settings.json, so worktree depth is irrelevant.
    plugin_dirs:
      - ".claude/cc-pipeline"
      - ".claude/cc-qo-skills"
    mcp_config: ".mcp.json"

# ─────────────────────────────────────────────────────────────────────────────
# WORKER CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

worker:
  # Default model for all task types unless overridden per task type above.
  default: claude-sonnet

  # V1: use Claude CLI in print mode with streaming JSON output.
  # V2: migrate to Claude Agent SDK for better session control and structured events.
  runtime: claude_cli
  cli_flags:
    - "--output-format stream-json"
    - "--permission-mode acceptEdits"

  # Spend cap per run (if supported by Claude configuration).
  # Prevents runaway costs on stalled or looping runs.
  max_cost_usd: 5.00

# ─────────────────────────────────────────────────────────────────────────────
# CONCURRENCY
# ─────────────────────────────────────────────────────────────────────────────

concurrency:
  # Maximum parallel runs on this machine.
  # Increase only after single-run stability is confirmed.
  max_parallel_runs: 2

  # Never run more than one agent per issue at a time.
  max_runs_per_issue: 1

# ─────────────────────────────────────────────────────────────────────────────
# HOOKS
# These hooks fire during orchestrated runs only.
# They write to the event stream; the TUI reads from it.
# ─────────────────────────────────────────────────────────────────────────────

hooks:
  on_stop:
    # Scans agent output for uncertainty signals → flags ⚠ in TUI
    - orchestrator/hooks/uncertainty_detector.py
    # Writes all lifecycle events to runs/events.jsonl
    - orchestrator/hooks/event_bridge.py

  on_subagent_stop:
    # Marks phases complete in execution-tracker.json
    - orchestrator/hooks/phase_tracker.py
    # Posts completion artifacts to Linear as comments
    - orchestrator/hooks/artifact_poster.py

  on_file_write:
    # Logs file activity → TUI workspace panel shows real-time changes
    - orchestrator/hooks/event_bridge.py

# ─────────────────────────────────────────────────────────────────────────────
# LOCAL RUN STATE
# ─────────────────────────────────────────────────────────────────────────────

run_state:
  # Current state of all active and recent runs.
  state_file: runs/state.json

  # Append-only structured event log. TUI tails this for real-time updates.
  event_log: runs/events.jsonl

  # Per-run log files. Named: {issue_id}-{timestamp}.log
  log_dir: runs/logs/

# ─────────────────────────────────────────────────────────────────────────────
# HANDOFF STATES
# Where the orchestrator stops and what it does when it gets there.
# ─────────────────────────────────────────────────────────────────────────────

handoff:
  # Agent signals ready for review → orchestrator moves issue here and stops.
  # Human then reviews in TUI or Linear. PR is opened at this point.
  success: Human Review

  # On unrecoverable error after max retries → move back to Todo with a comment.
  failure: Todo

  # If issue becomes ineligible mid-run → stop cleanly, return to last stable state.
  ineligible: Todo

  # Agent blocked on a decision or missing input → orchestrator moves issue here.
  blocked: Needs Input

# ─────────────────────────────────────────────────────────────────────────────
# RETRY POLICY
# ─────────────────────────────────────────────────────────────────────────────

retry:
  # Maximum run attempts per issue before giving up and posting a failure report.
  max_attempts: 3

  # Exponential backoff between retries (seconds).
  backoff_seconds: [5, 15, 60]

  on_crash: retry
  on_stall_minutes: 30        # if agent produces no output for this long, restart
  on_ineligible: stop         # issue moved out of eligible state → stop without retry

# ─────────────────────────────────────────────────────────────────────────────
# POLLING
# ─────────────────────────────────────────────────────────────────────────────

polling:
  # How often the orchestrator checks Linear for newly eligible issues.
  interval_seconds: 15

  # Reconciliation: how often to check that active runs still match Linear state.
  reconcile_interval_seconds: 120

# ─────────────────────────────────────────────────────────────────────────────
# REPORTING
# ─────────────────────────────────────────────────────────────────────────────

reporting:
  # Orchestrator posts a Linear comment at these events.
  post_progress_at:
    - phase_complete
    - artifact_ready
    - human_input_needed
    - iteration_start

  # Full execution report posted using pd-report-post skill.
  post_report_on:
    - human_review
    - cancelled
    - failure

# ─────────────────────────────────────────────────────────────────────────────
# OPERATOR NOTES
# ─────────────────────────────────────────────────────────────────────────────
#
# Starting the orchestrator:
#   python -m orchestrator.main
#
# Watching active runs (TUI):
#   resonance watch
#
# Approving a run:
#   resonance approve QO-123
#
# Sending feedback without taking over:
#   resonance feedback QO-123 "use the primary button variant here"
#
# Pausing a run:
#   resonance pause QO-123
#
# Aborting a run:
#   resonance abort QO-123
#
# For full setup and recovery steps, see: docs/operator-runbook.md
