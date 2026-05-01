# Claude Workflow Reference

This document is the practical operator guide for this repo.

It explains:

- what the repo is for
- what each command does
- what each subagent does
- what the rules and MCPs are for
- what to expect from a run
- how to validate the setup
- how to collect feedback from real usage

---

## What This Repo Does

This repo is a `Claude Code` workflow setup for supervised frontend and design work.

It helps turn:

- a `Linear` issue
- a `Figma` reference
- a visual reference from screenshots or vibe-coded code

into:

- a component map
- an implementation plan
- a first-pass UI using real reusable components
- Playwright-backed visual checks
- QA findings
- a review-ready summary

It is not a full app runtime.

It is a working environment for Claude Code.

---

## Expected User Experience

You should be able to:

1. open Claude Code in this repo
2. point it at a Linear issue or Figma reference
3. run the project commands in order
4. review the analysis
5. approve the plan
6. let Claude build the first pass
7. review screenshots and QA findings
8. give feedback and iterate

The process is intentionally supervised.

You are not expected to trust the first pass blindly.

---

## Command Reference

Project commands live in `.claude/commands/`.

### `/qo-ui-kickoff`

Purpose:

- start a supervised UI task correctly
- resolve the issue inputs
- verify the task is ready for analysis
- prepare the context bundle

Use when:

- starting a new UI task
- receiving a new Linear issue
- collecting Figma and visual inputs before planning

Expected outcome:

- the task inputs are clear
- missing information has been surfaced
- the task is ready for `/qo-ui-analyze`

What it should not do:

- write implementation code

### `/qo-ui-analyze`

Purpose:

- understand the requirement
- inspect Figma and visual references
- inspect the repo and design system
- identify reusable components and tokens
- produce the implementation plan

Use when:

- the input task is sufficiently defined
- you want analysis before build

Expected outcome:

- requirement summary
- layout summary
- component map
- gap report
- implementation plan
- open questions

What it should not do:

- build the UI yet

### `/qo-ui-build`

Purpose:

- implement the approved plan
- reuse components and tokens
- verify visually with Playwright during implementation

Use when:

- the analysis is approved
- you want the first-pass UI implemented

Expected outcome:

- code changes
- preview evidence
- screenshots
- reused components list
- new components list
- deviations list

What it should not do:

- skip browser-based inspection

### `/qo-ui-qa`

Purpose:

- review the built UI against Queen One standards
- check token usage, reuse, CSS drift, and visual drift

Use when:

- a build pass exists
- you want a QA review before human review

Expected outcome:

- pass / warn / fail verdict
- findings list
- required fixes
- suggested fixes

### `/qo-ui-report`

Purpose:

- prepare the review handoff
- summarize the current result
- prepare a concise Linear-ready update

Use when:

- you want to package the current pass for review
- you are updating Linear with progress or completion details

Expected outcome:

- human-readable summary
- milestone-ready note
- review-ready artifact summary

---

## Subagent Reference

Project subagents live in `.claude/agents/`.

### `ui-analysis-agent`

Role:

- requirement analyst
- Figma interpreter
- component mapper
- planner

What it focuses on:

- what the screen is trying to do
- how the layout is structured
- which reusable components already exist
- which tokens should be used
- what is missing or ambiguous

Expected outputs:

- `analysis.md`
- `component-map.md`
- `gap-report.md`
- `plan.md`

### `ui-build-agent`

Role:

- implementation specialist
- visual iteration builder

What it focuses on:

- building the approved UI
- reusing components first
- using design tokens correctly
- avoiding unnecessary custom CSS
- checking the rendered output with Playwright

Expected outputs:

- code changes
- screenshots
- preview evidence
- reused and new component lists
- deviations list

### `ui-qa-agent`

Role:

- design-system and visual reviewer

What it focuses on:

- token correctness
- reusable component correctness
- unnecessary CSS
- visual mismatches
- obvious accessibility issues

Expected outputs:

- QA findings
- pass / warn / fail verdict
- fixes required before review

---

## Skills

At the moment, this repo does not define a dedicated project `skills/` directory.

The current workflow is centered on:

- `project commands`
- `project subagents`
- `project rules`
- `MCP tools`

That is intentional.

It keeps the workflow simple while you validate the v1 process.

If later you want reusable agent-facing logic beyond slash commands, the next step would be to add project skills for:

- `qo-ui-analysis`
- `qo-ui-build`
- `qo-ui-qa`
- `qo-ui-report`

For now, treat the commands and subagents as the active workflow primitives.

---

## Rules

Project rules live in `.claude/rules/`.

The most important one for this workflow is:

- `frontend.md`

What it should enforce in practice:

- design-token usage
- reusable component usage
- avoidance of ad hoc styles
- alignment with project frontend conventions

The other existing rules remain as background guardrails, but the workflow should be understood primarily through:

- `CLAUDE.md`
- the `qo-ui-*` commands
- the three subagents

---

## MCP Reference

Project MCP configuration lives in `.mcp.json`.

### Linear MCP

Use for:

- issue reading
- comment reading
- milestone updates

Expectation:

- Claude can pull durable requirement context from Linear

### Figma MCP

Use for:

- frame metadata
- frame images
- styles and layout clues

Expectation:

- Claude can ground the target UI in real Figma data

### GitHub MCP

Use for:

- reading repo or design-system context when needed

Expectation:

- Claude can inspect reusable component sources and related references

### Playwright MCP

Use for:

- running the UI in a real browser
- taking screenshots
- checking the rendered result during implementation

Expectation:

- visual work is not done blind

### Mermaid MCP

Use for:

- diagrams and visual process explanations

Expectation:

- easier reasoning and communication around workflow and architecture

---

## What A Good Run Looks Like

### Input

The Linear issue contains:

- clear description
- Figma URL
- visual reference code or screenshots
- acceptance criteria

### Analysis pass

Claude returns:

- what the screen needs
- which reusable components map to it
- what is missing
- what the implementation plan is

### Approval

You confirm:

- the direction is correct
- the component mapping is acceptable
- any known deviations are acceptable

### Build pass

Claude builds the UI and checks it in a browser with Playwright.

### QA pass

Claude checks for:

- token usage
- component reuse
- visual drift
- unnecessary CSS

### Human review

You review:

- screenshots
- preview
- QA findings
- deviations

Then accept or iterate.

---

## Running And Validating The Setup

### 1. Open Claude Code in the repo

Expected:

- `CLAUDE.md` is loaded as project memory
- project commands appear in `/help`
- subagents are available in `/agents`

### 2. Check MCP connections

Run:

- `/mcp`

Expected:

- `linear`
- `figma`
- `github`
- `playwright`
- `mermaid`

If a server requires credentials, authenticate or set the env vars from `.env`.

### 3. Check commands

Expected project commands:

- `/qo-ui-kickoff`
- `/qo-ui-analyze`
- `/qo-ui-build`
- `/qo-ui-qa`
- `/qo-ui-report`

### 4. Check subagents

Expected project subagents:

- `ui-analysis-agent`
- `ui-build-agent`
- `ui-qa-agent`

### 5. Run a real task

Use one bounded UI task.

Success means:

- the analysis is useful
- the plan is reviewable
- the build uses the right components
- Playwright catches visual issues
- QA findings are helpful

---

## What “Tests” Mean Here

This repo no longer has a Python test suite.

For this workflow, “tests” means validating the setup and the process:

### Setup tests

- Claude sees the project commands
- Claude sees the project subagents
- MCPs connect correctly
- required environment variables are available

### Workflow tests

- kickoff works on a real issue
- analysis produces a useful component map
- build produces a preview and screenshots
- QA produces findings
- the human can review and iterate without confusion

### Output tests

- tokens are used correctly
- reusable components are used where expected
- custom CSS is minimized
- visual output is close enough to the target to refine further

---

## Feedback Collection

When you run the workflow, collect feedback at three levels.

### 1. Input quality

Ask:

- was the Linear issue sufficiently clear?
- was the Figma enough?
- were screenshots or vibe-coded references useful?

### 2. Workflow quality

Ask:

- did the analysis produce the right component map?
- did the plan feel trustworthy?
- did Playwright help catch the right visual problems?
- did QA findings reflect real issues?

### 3. Output quality

Ask:

- was the first pass roughly 70% useful?
- what was missing?
- what drifted from the intended UX?
- what still needed human refinement?

Capture this feedback in a simple note after each run so the workflow can be tightened over time.

---

## Recommended First Trial

Use one bounded screen or feature where:

- the Figma is reasonably complete
- component reuse is likely
- backend complexity is low
- visual quality matters

That is the best way to validate the workflow without adding more architecture.
