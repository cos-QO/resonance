# Memory System

Persistent shared memory for all agents. Standards and templates are long-lived; active work and reports are transient.

## Structure

```
memory/
├── standards/          # Project conventions, coding style, naming, testing
│   ├── conventions.md  # Core coding standards (READ FIRST)
│   ├── tree.md         # File structure map
│   ├── stack.md        # Technology decisions
│   └── ...             # Domain-specific standards
│
├── templates/          # Reusable templates for plans, TODOs, reports, handoffs
│
├── active/             # Current work in progress
│   ├── execution-tracker.json  # Phase tracking (created by PM)
│   ├── skill-drafts/   # Skills staged for review before install
│   └── options/        # Option command state
│
├── todos/              # Active TODO files (created by PM)
├── plans/              # Active plan directories
│
├── reports/            # Output from verify, heartbeat, skill-eval, troubleshooting
│   ├── verify/
│   ├── skill-eval/
│   ├── heartbeat/
│   ├── errors/         # tool-failures.jsonl from error-tracker hook
│   └── troubleshooting/
│
├── discovery/          # Research findings and analysis (temporary)
├── project/            # Project context, roadmap, decisions
├── security/           # Security enhancement plans
├── session_checkpoints/ # PreCompact context saves
├── telemetry/          # Execution traces
│
└── archive/            # Completed work (historical reference)
```

## Usage

- **Standards**: Read before starting any work. Updated by documenter when patterns emerge.
- **Active + TODOs**: Created by PM per plan. Updated by agents during execution.
- **Reports**: Written by verify, heartbeat, and skill-eval skills. Auto-archived after 7 days.
- **Templates**: Referenced when creating plans, TODOs, reports, handoffs.
- **Archive**: Read-only historical reference. Never modify archived files.
