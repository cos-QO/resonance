# pd-guardrail

**Auto-loaded rule. Enforced on every response.**

## Rule

**Do not write, generate, or modify any implementation code unless the current Linear issue has status "Plan Approved".**

This applies to:
- Any file edit that implements a feature, fix, or change
- Any new file creation that is part of the deliverable
- Any scaffold, boilerplate, or "starter" code for the task

This does NOT apply to:
- Reading files, exploring the codebase, running searches
- Generating or posting the PEP
- Running sub-agent context collection
- Drafting or posting the implementation plan
- Running tests on existing code
- Writing execution reports

## How to check

Before any implementation action, verify:

1. Is there an active Linear issue for this task? If not — ask the user for one.
2. Check `.claude/memory/pd/plans/<issue-id>-meta.json` for `"status": "approved"`
3. If the meta file does not exist or status is not approved — check Linear directly via `mcp__linear__get_issue` for status = "Plan Approved"

If neither check confirms approval: **stop, display the following, and wait:**

```
⛔ GUARDRAIL — No approved plan

This task requires an approved plan before implementation can start.

To proceed:
1. Run /pd-start <issue-id> to generate a PEP and plan
2. Approve the plan in Linear (set status to "Plan Approved")
3. Resume this session

Issue: [issue identifier if known]
```

## Override

A user may explicitly say "skip the plan gate" or "proceed without approval". In that case:
- Acknowledge the override explicitly: "Proceeding without plan approval — guardrail bypassed by user request"
- Continue with implementation
- Note the override in the execution report
