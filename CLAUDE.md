# Queen One UI Workflow

This repository is a `Claude Code` project for supervised `UX/Figma -> production UI` work.

## Project Memory

Use this repo to turn:

- a `Linear` issue
- a `Figma` reference
- a visual reference from a vibe-coding tool, screenshots, or prototype code

into:

- reusable component mapping
- an implementation plan
- a first-pass UI built with real components
- Playwright-backed visual feedback
- QA findings
- final review-ready documentation

## Operating Model

- `Linear` holds the task, references, clarifications, and milestone updates.
- `Claude Code` does the analysis, planning, implementation, and QA work.
- `Playwright` is mandatory for frontend and visual work.
- humans approve the plan and the final visual result.

Use this sentence as the rule:

`Linear holds the task and milestones. Claude Code does the work.`

## Required Inputs

For UI work, the issue should include:

- product requirement / description
- Figma URL
- visual reference code or screenshots
- acceptance criteria
- scope / route / screen
- constraints or non-goals

## Required Behavior

### Before building

- read the Linear issue and comments
- inspect the Figma reference
- inspect the visual reference
- inspect the design system and existing code
- produce a component map and plan
- wait for human approval

### During building

- reuse existing QO / ConnectUI components first
- use design tokens first
- avoid unnecessary custom CSS
- use Playwright during implementation, not only at the end
- compare the rendered result against the Figma and visual reference

### Before handoff

Produce:

- implementation summary
- reused components list
- new components list
- deviations list
- QA findings
- screenshots / preview evidence

Do not mark work complete without human visual review.

## Important Files

- `docs/supervised-session-architecture-v2.md`
- `.claude/README.md`
- `.claude/memory/standards/connectui-design-system.md`
- `.claude/memory/standards/connectui-stack.md`
- `.claude/rules/frontend.md`

## Project Commands

Use these project commands:

- `/qo-ui-kickoff`
- `/qo-ui-analyze`
- `/qo-ui-build`
- `/qo-ui-qa`
- `/qo-ui-report`

## Subagents

The project keeps only three focused subagents:

- `ui-analysis-agent`
- `ui-build-agent`
- `ui-qa-agent`

Do not default to large PM-led multi-agent chains for everyday UI work.
