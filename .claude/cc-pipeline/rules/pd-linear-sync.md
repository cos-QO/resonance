# pd-linear-sync

**Auto-loaded rule. Enforces Linear updates at each pipeline phase transition.**

## Required Linear updates

Post a comment on the Linear issue at each of the following moments. Keep them brief — one to three lines. Humans use these to follow progress without reading code.

| Phase | When to post | What to include |
|---|---|---|
| PEP created | After `/pd-pep` creates the document | "PEP created — [N] open questions. Link: [doc URL]" |
| Context collected | After `pd-linear-scope` completes | "Context collected from [sources]. Key finding: [1 sentence]. Plan incoming." |
| Plan posted | After `pd-plan-post` runs | "Plan ready for approval — [link to plan comment]. Please set status to Plan Approved to proceed." |
| Execution started | After plan approval confirmed | "Plan approved. Starting implementation." |
| PR opened | After `pd-github-pr` runs | "PR opened: [PR link]. [Reviewer] assigned for review." |
| Execution report | After `/pd-report` runs | Full execution report (handled by `pd-report-post`) |

## What NOT to post

- Intermediate progress updates ("working on FR-2 now")
- Debug logs or error details (keep locally)
- Speculative status ("should be done soon")

## Format

Post via `mcp__linear__create_comment`. Keep every comment under 5 lines except the final execution report.
