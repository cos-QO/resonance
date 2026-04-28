# PEP Template — Product Execution Prompt

> Fill Tier 1 for any task. Add Tier 2 for medium/large work. Add Tier 3 and domain variants only when relevant.

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

## Phasing

### Phase 1 — Now

* 

### Phase 2 — Next

* 

### Phase 3 — Later

* 

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
