# Workflow and Approval Model

## End-to-End Workflow

1. create or refine a Linear project document
2. create an execution issue from a structured template
3. gather broad awareness context from Linear
4. generate a context pack
5. draft an implementation plan
6. obtain human approval on the plan
7. execute implementation in Claude Code or Cursor
8. run tests and verification
9. open a GitHub PR linked to the Linear issue
10. obtain human PR review
11. merge
12. deploy if approved
13. post an execution report back to Linear
14. close the issue or update the project state

## Human Gates

### Mandatory

- plan approval before implementation
- PR review before merge
- deployment approval for protected environments
- final acceptance for ambiguous or sensitive product work

### Optional depending on team policy

- design review before plan approval
- architecture review for high-risk changes
- stakeholder review before release

## What Should Be Automated

- issue normalization from templates
- multi-team context gathering
- plan drafting
- local plan and report creation
- implementation and testing
- progress updates at major milestones
- execution report drafting

## What Should Stay Human-Controlled

- prioritization
- approval of scope and plan
- resolution of ambiguity or tradeoffs
- code review and merge decision
- production release approval

## Approval Philosophy

Humans should review at points where reversal becomes expensive.

That means the first important gate is not the PR. It is the plan.

If the plan is wrong and humans only review at PR time, the organization is reviewing after architecture, execution, and hidden assumptions have already solidified.

## Completion Standard

A task should not be considered complete just because code was written.

Completion should include:

- approved plan
- implemented work
- verification evidence
- documented outcome
- updated Linear record
- any follow-up issues clearly recorded
