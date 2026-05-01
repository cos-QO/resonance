# File Organization

Keep workflow artifacts and code changes easy to inspect.

## For workflow notes

- plans go in `.claude/memory/plans/`
- checkpoints go in `.claude/memory/session_checkpoints/`
- handoff notes go in `.claude/memory/handoffs/`
- QA and visual review notes go in `.claude/memory/reports/`

## For implementation work

- prefer editing the real target files directly
- avoid creating ad hoc duplicate component files
- keep naming aligned with existing Queen One / ConnectUI conventions

## For new files

- only create new UI files when reuse is not sufficient
- keep filenames clear and scoped to the real feature or screen
