# pd-issue-standard

**Auto-loaded rule. Validates issue quality before planning starts.**

## When this rule applies

Before any planning or PEP generation, check the Linear issue meets the minimum standard. An issue that fails validation should not proceed to planning — surface the gaps and ask the human to fill them.

## Minimum standard (all issue types)

| Field | Requirement |
|---|---|
| Title | Clear and specific — not "fix bug" or "update thing" |
| Description | At least one sentence describing what needs to change |
| Outcome | What changes for whom — even one sentence |
| Acceptance criteria | At least one verifiable condition |

If any of these are missing: post a comment on the Linear issue listing the gaps, and stop. Do not generate a PEP from an empty or vague issue.

## What the pd-pep skill handles

Fields that the `pd-pep` skill will infer or generate (not human-required upfront):
- Domain classification
- Scope boundaries (will be surfaced as OQs if missing)
- FRs with Verify by lines
- Sub-agent assignment

## Override

If the user says "create the PEP anyway" despite missing fields: proceed, but mark all inferred fields as assumptions in the OQ table with `status: needs-human-confirmation`.
