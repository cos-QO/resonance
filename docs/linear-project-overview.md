# Cross-Team Agentic Delivery Pipeline — Project Overview

## What This Is

A **supervised agentic delivery pipeline** built around Linear, Claude Code (or Cursor), and GitHub. The goal is not full automation — it is a structured operating model where agents move fast and humans stay accountable at the right moments.

Without this structure, agents tend to overfit to the current issue, miss cross-team dependencies, lose state between sessions, and produce outputs that are hard to audit. This pipeline solves those problems by giving agents high-quality context, a clear operating model, durable working memory, and strong human checkpoints.

---

## End-to-End Flow

1. Intent and requirements captured in Linear (from template)
2. Agent gathers broad cross-team context from Linear
3. Context pack generated (issue + project + adjacent teams + impact map)
4. Agent drafts implementation plan
5. **→ Human approves plan** *(critical gate — before any code is written)*
6. Agent executes in Claude Code or Cursor
7. Tests and verification run
8. GitHub PR opened, linked to the Linear issue
9. **→ Human reviews PR** *(enforcement gate — before merge)*
10. Merge and deploy
11. Execution report posted back to Linear, issue closed

---

## Three Control Planes

| System | Role |
|---|---|
| **Linear** | Intent, ownership, approvals, cross-team context, final reports |
| **Claude Code / Cursor** | Planning, broad awareness, execution, verification |
| **GitHub** | PR review, CI, merge gates, deployment controls |

---

## Milestones

| Milestone | Focus | Status |
|---|---|---|
| **M1 — Foundation** | Issue templates + plan approval gate + GitHub PR review | 🔵 In Progress |
| **M2 — Context Engine** | Broad awareness + context packs + impact maps | ⚪ Planned |
| **M3 — Knowledge Layer** | Thin context catalog + cross-team dependency maps | ⚪ Planned |
| **M4 — Automation** | Execution reports + status automation + metrics | ⚪ Planned |

---

## Ticket Map

### M1 — Foundation (High Priority)
- Define mandatory issue template schema
- Design plan approval workflow in Linear
- Set up GitHub branch protection rules for PR review gate
- Define minimum Linear update set for every completed task
- Define simple task vs. broad-awareness task threshold

### M2 — Context Engine (Medium Priority)
- Design context pack schema and generation logic
- Build broad awareness context retrieval from Linear
- Define adjacent team selection rules for broad awareness
- Implement impact map generator

### M3 — Knowledge Layer (Low Priority)
- Design thin context catalog structure (repo-local)
- Build catalog refresh mechanism from Linear
- Create cross-team dependency maps
- Document catalog ownership and maintenance policy

### M4 — Automation (Low Priority)
- Design execution report template and auto-generation
- Automate Linear issue status updates at key pipeline milestones
- Define success metrics schema and tracking

---

## Principles

- Linear is the **human-facing source of truth** for intent, ownership, and approvals
- Repo-local memory is the **agent's working ledger** for plans, context packs, and checkpoints
- GitHub is the **enforcement layer** — no merge without human review
- Humans approve at points where reversal becomes expensive
- Templates and consistency matter more than prompt cleverness

---

## Flow Diagram

[View system architecture on Mermaid →](https://mermaid.ai/app/projects/49f9c684-ff3a-450e-8482-c1cbe71a0196/diagrams/327798ef-ca9d-4b86-8b1a-7fb10b9bb0c8/version/v0.1/edit)

---

## Open Questions

1. What exact threshold triggers full context-pack generation?
2. Which approvals are mandatory for all teams?
3. What should be written back to Linear vs. kept only locally?
4. Who owns the thin context catalog?
5. How should adjacent teams be chosen during broad awareness?
6. Where should final success metrics live?

---

## Risks

| Risk | Impact |
|---|---|
| Inconsistent issue templates across teams | Poor retrieval quality — context packs become unreliable |
| Weak project documentation | Broad awareness becomes guesswork |
| State drift between Linear, local memory, and GitHub | Trust in the system breaks down |
| Humans skip plan approval and only review at PR time | Major architectural mistakes detected too late |
| Retrieval too broad | Agents get noise instead of awareness |
| No clear catalog ownership | System degrades over time |
