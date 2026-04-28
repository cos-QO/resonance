---
name: pd-pep
description: "Create or validate a PEP (Product Execution Prompt) for a Linear issue. Detects issue domain, generates the correct tiers and domain variant, and posts to Linear."
argument-hint: <linear-issue-id> [--validate] [--create-tickets]
allowed-tools: Read, Write, mcp__linear__*
---

# /pd-pep — PEP Create or Validate

Creates a PEP from a Linear issue or validates an existing one.

## Flags

- No flag — create PEP if missing, validate if exists
- `--validate` — validate an existing PEP only, report missing fields
- `--create-tickets` — execute Section 14 (Linear Export Mapping) to auto-create child tickets

## Workflow

Delegates to the `pd-pep` skill. See `skills/pd-pep/SKILL.md` for full logic.

## Output

- PEP document posted to Linear (linked to the issue)
- Summary in Claude: valid / created / missing fields list
- With `--create-tickets`: list of created ticket identifiers
