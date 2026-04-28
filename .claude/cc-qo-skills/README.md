# cc-qo-skills

Execution skills module for Queen One Claude Code workflows.

## What it provides

- `connectui-dev` — loads ConnectUI design system + code standards before frontend work
- `verify` L1/L2/L3 — quality pipeline: build, lint, tests, security
- `qo-pr` — structured PR description from git diff
- `qo-prototype` — Figma-to-code with design system awareness

## Installation

This module is maintained separately. To install:

```bash
# Clone or copy cc-qo-skills into this directory
# Expected path: .claude/cc-qo-skills/

git clone https://github.com/queen-one/cc-qo-skills .claude/cc-qo-skills
```

## Required by

- `cc-pipeline` design_to_code and frontend_feature task types
- Any orchestrated worker run involving frontend implementation

## Relationship to cc-pipeline

cc-pipeline handles: issue intake → context → plan → approval → reporting
cc-qo-skills handles: implementation standards → verify → PR creation

Install both. cc-pipeline calls into cc-qo-skills at the execution phase.
