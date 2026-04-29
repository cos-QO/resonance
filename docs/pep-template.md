# PEP Template — Product Execution Prompt

> Fill Tier 1 for any task. Add Tier 2 for medium/large work. Add Tier 3 and domain variants only when relevant.
>
> **Naming convention:** Create the PEP as a Linear issue with the `pep` label inside a project named `[PEP] <title>`.
> When you move the PEP issue to **Plan Approved**, Resonance reads it and creates Plan issues automatically.
>
> **Plan/Block identifiers** (title-based, since Linear assigns numeric IDs):
> ```
> PEP issue:    RND-22              ← assigned by Linear
> Plan 1:       [RND-22-P1] Title   ← created by Resonance
> Plan 2:       [RND-22-P2] Title
> Block 1/P1:   [RND-22-P1-B1] Title ← created by Execution Agent
> Block 2/P1:   [RND-22-P1-B2] Title
> ```

---

```
# PEP: <title>

id:      pep-<slug>
status:  draft | in-review | approved | in-progress | complete
owner:   <name>
created: YYYY-MM-DD
updated: YYYY-MM-DD
```

---

## 🤖 Agent Handoff

> For Claude Code. Humans skip to **What**.

**Task:** \[one sentence\]

**Collect before planning:**

| Sub-agent | Mission | Resolves |
| -- | -- | -- |
| Codebase |  |  |
| Linear |  |  |
| Figma |  |  |

> Skip sub-agents for quick wins — go straight to plan.

**Gate:** Do not write code until plan is posted to Linear and status = **Plan Approved**.

**Output:** \[PR + preview link / doc / decision / other\]

---

# Tier 1 — Always Required

## What

\[One sentence — what changes\]

## Why

\[One sentence — why it matters\]

## Done When

- [ ] \[Verifiable acceptance criterion\]
- [ ] \[Add more if needed\]

## Not Doing

* \[Explicit out-of-scope — at least one bullet\]

---

# Tier 2 — Medium and Large Tasks

## Outcome

* **Primary:**
* **Secondary:**
* **Non-goals:**

### Success Metrics

| Metric | Target |
| -- | -- |
|  |  |

---

## Scope

### In Scope

* 

### Out of Scope

* 

---

## Functional Requirements

> Atomic and testable. Every FR needs a Verify by line.

**FR-1:**
*Verify by:*

**FR-2:**
*Verify by:*

---

## Plans

> Each Plan becomes one Linear issue ([PEP-ID-P1], [PEP-ID-P2], ...).
> Plans can run in parallel or in sequence. Set `Depends on` to enforce order.
> Resonance sets blocking relations automatically from this section.

### Plan 1 — <name>
**Goal:** [What this plan delivers — one sentence]
**Domain:** frontend | backend | design | mixed
**Depends on:** none

**Blocks:**
- B1: [Block title] — [what it implements, ~3–8 hours]
- B2: [Block title] — [what it implements, depends on B1]

---

### Plan 2 — <name>  *(add/remove plans as needed)*
**Goal:** [What this plan delivers]
**Domain:** frontend | backend | design | mixed
**Depends on:** Plan 1

**Blocks:**
- B1: [Block title] — [what it implements]
- B2: [Block title] — [what it implements]

---

# Tier 3 — Complex / Cross-Team / Product-Level

## Interaction Model

| State | Behaviour |
| -- | -- |
| Loading |  |
| Empty |  |
| Error |  |

---

## Linear Export Mapping

> A filled mapping = a ticket tree the pd-pep skill auto-creates in Linear.

### Epic

* **Title:**
* **Description:**

### Tickets

#### Product

- [ ] Ticket / description / acceptance criteria

#### Design

- [ ] Ticket / description / acceptance criteria

#### Engineering

- [ ] Ticket / description / acceptance criteria

#### Integration

- [ ] Ticket / description / acceptance criteria

---

## Open Questions

| \# | Question | Resolved by | Status |
| -- | -- | -- | -- |
| OQ-1 |  |  | Open |

---

## Appendix

| Item | Link |
| -- | -- |
|  |  |

---

# Domain Variants

> Append the relevant block(s) after Tier 2/3.

---

## \+ Frontend

* ConnectUI components:
* Figma link:
* Token set:
* Responsive breakpoints:

---

## \+ Backend

* Services involved:
* API contracts changed:
* Backwards compatibility:

---

## \+ Data / Analytics

* Schema changes:
* Analytics events:
* Downstream consumers:
* Privacy flags:

---

## \+ Research / Spike

* Questions to answer:
* Time-box:
* Output format:
* Decision owner:
