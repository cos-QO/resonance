# Flow Diagrams

## End-to-End Delivery Flow

```mermaid
flowchart TD
    A[Product request or PRD in Linear] --> B[Create or refine Linear project document]
    B --> C[Create execution issue — meets issue standard]
    C --> D{Simple or broad-awareness task?}
    D -- Simple --> F
    D -- Broad --> E[Agent gathers cross-team context via Linear MCP]
    E --> E2[Generate context pack<br/>impact map · blockers · assumptions · confidence]
    E2 --> F[Draft implementation plan]
    F --> G{Human approves plan?}
    G -- No --> H[Revise plan]
    H --> F
    G -- Yes --> I[Execute — agent loads team standards via skills + rules]
    I --> J[Run tests and verification]
    J --> K[Open GitHub PR linked to Linear issue]
    K --> L{Human review passes?}
    L -- No --> M[Agent revises implementation]
    M --> J
    L -- Yes --> N[Merge]
    N --> O{Deployment approval needed?}
    O -- Yes --> P[Human approves deployment]
    P --> Q[Deploy]
    O -- No --> Q
    Q --> R[Agent posts execution report to Linear]
    R --> S[Issue closed / project updated]
```

---

## Systems Of Record

```mermaid
flowchart LR
    A[Linear] -->|intent · ownership · approvals · references| X[Shared delivery workflow]
    B[Repo-local memory] -->|context packs · plans · checkpoints · reports| X
    C[GitHub] -->|PR review · CI · merge gates · deploy gates| X
```

---

## Human Control Points

```mermaid
flowchart TD
    A[Intake] --> B[Plan drafted by agent]
    B --> C[Human plan approval ← first gate]
    C --> D[Implementation by agent]
    D --> E[GitHub PR]
    E --> F[Human PR review ← second gate]
    F --> G[Merge]
    G --> H[Human deployment approval when needed]
    H --> I[Closeout report posted to Linear]
```

---

## Skills & Rules Layer

Each pipeline stage is wrapped by a skill. Rules auto-inject context based on file paths and issue type. This is what makes the pipeline agentic rather than a documented checklist.

```mermaid
flowchart TD
    subgraph ISSUE["Issue Creation"]
        IS[/qo-issue skill/] --> ISV[Issue standard validation<br/>required fields by type]
    end

    subgraph CLASSIFY["Classification"]
        CL[/qo-classify skill/] --> CLR{Broad awareness<br/>needed?}
    end

    subgraph CTX["Context Phase — broad only"]
        CP[/qo-context-pack skill/] --> LM[Linear MCP<br/>parent project · adjacent teams · docs]
        LM --> IM[Impact map + context pack<br/>saved to local memory]
    end

    subgraph PLAN["Planning Phase"]
        PL[/qo-plan skill/] --> PLT[Structured plan<br/>posted to Linear for approval]
    end

    subgraph GUARD["Execution Gate"]
        GR[pipeline-guardrail rule] -->|blocks if no approved plan| EX
    end

    subgraph EXEC["Execution Phase"]
        EX[Specialisation skill loaded<br/>connectui-dev · python-dev · api-dev · etc.] --> STD[Standards auto-loaded<br/>design system · code conventions · API contracts]
    end

    subgraph VERIFY["Verification"]
        VR[/verify L1·L2·L3/] --> QG[Quality gates<br/>build · lint · tests · security]
    end

    subgraph REPORT["Report Phase"]
        RP[/qo-report skill/] --> LU[Execution report posted to Linear<br/>what was done · evidence · follow-ups · PR link]
    end

    ISSUE --> CLASSIFY --> CTX --> PLAN --> GUARD --> EXEC --> VERIFY --> REPORT
```

---

## Issue Standards Model

Not a rigid template — a set of required fields with quality criteria, varying by issue type. Agents validate completeness before planning; humans validate intent before approving.

```mermaid
flowchart TD
    CORE["All Issues — Core Fields
    ──────────────────────
    · Outcome (what changes for whom)
    · Scope (what's in / what's out)
    · Dependencies (systems + teams)
    · Acceptance criteria
    · Classification (simple · medium · large · complex)"]

    CORE --> T{Issue type}

    T --> FEAT["Feature / Epic
    ──────────────────
    + Success metrics
    + Design reference (Figma)
    + Product sign-off required
    + Adjacent teams impacted"]

    T --> BUG["Bug
    ──────────────────
    + Steps to reproduce
    + Expected vs actual behaviour
    + Severity + customer impact
    + Systems involved"]

    T --> TECH["Technical task
    ──────────────────
    + Risk if deferred
    + Complexity estimate
    + Systems + APIs touched
    + Rollback plan if needed"]

    T --> DATA["Data / Analytics
    ──────────────────
    + Analytics events affected
    + Data model changes
    + Downstream consumers
    + Privacy / compliance flags"]

    T --> SPIKE["Research / Spike
    ──────────────────
    + Questions to answer
    + Time-box
    + Output format (doc · decision · prototype)
    + Decision owner"]
```

---

## Agent Context Loading

How agents load the right knowledge for the task — before writing a single line of code.

```mermaid
flowchart LR
    A[Issue loaded] --> B[/qo-classify/]

    B -->|simple| C[Load team rules only]
    B -->|broad| D[/qo-context-pack/ via Linear MCP]

    C --> R[team-specific rules auto-injected<br/>by path matching]
    D --> E[Pull: parent project · adjacent issues · linked docs · comments]
    E --> F[Impact map · blockers · assumptions · confidence level]
    F --> R

    R --> G{Team / domain?}
    G --> H[Frontend: connectui.md · orion.md · state.md · routing.md]
    G --> I[Backend: api-standards · data-models · contracts]
    G --> J[Data: analytics-events · schema · privacy]
    G --> K[DevOps: infra · deploy · rollback]

    H & I & J & K --> L[Agent begins planning with full context]
```

---

## Broad Awareness Flow

```mermaid
flowchart TD
    A[Current issue] --> F[Context assembly]
    B[Parent project] --> F
    C[Project docs] --> F
    D[Adjacent team issues] --> F
    E[Comments · blockers · external resources] --> F
    F --> G[Impact map]
    G --> H[Plan draft]
```

---

## Skills Gap — Exists vs Needs Building

What cc-qo-skills already provides vs what the pipeline needs to build.

```mermaid
flowchart TD
    subgraph EXISTS["Already exists in cc-qo-skills"]
        E1[connectui-dev: standards loading before code]
        E2[qo-bug: structured Linear ticket creation]
        E3[qo-prototype: Figma-to-code with design system]
        E4[qo-pr: structured PR description]
        E5[verify L1/L2/L3: quality pipeline]
        E6[Path rules: connectui · orion · state · routing · firebase]
        E7[qo-sync: keep rules aligned across tools]
    end

    subgraph BUILD["Needs to be built for the pipeline"]
        B1[/qo-issue/ — issue standard for all types]
        B2[/qo-classify/ — simple vs broad threshold]
        B3[/qo-context-pack/ — broad awareness + impact map]
        B4[pipeline-guardrail rule — no approved plan → no code]
        B5[/qo-report/ — structured execution report to Linear]
        B6[issue-standards rule — field requirements by type]
        B7[team-context rule — adjacent team routing by domain]
    end

    subgraph ADAPT["Adapt / extend from existing"]
        A1[qo-bug → foundation for qo-issue]
        A2[connectui-dev → pattern for standards-loading in all skills]
        A3[qo-sync → model for keeping standards aligned with Linear]
    end
```

---

## Indexing Model

```mermaid
flowchart TD
    A[Linear projects · issues · docs] --> B[Native Linear search and views]
    A --> C[LLM context catalog<br/>thin · repo-local · agent-optimised]
    C --> D[Fast routing for agents]
    B --> D
    D --> E[Context pack generation]
```

---

## Failure Modes

```mermaid
flowchart TD
    A[Inconsistent issue standards] --> X[Poor retrieval quality]
    B[Missing project docs] --> X
    C[Weak cross-team linking] --> X
    D[No approval discipline] --> Y[Unsupervised execution]
    E[Weak branch protection] --> Y
    F[No skills / rules layer] --> Y
    G[No sync mechanism] --> Z[State drift across tools]
    X --> W[Lower planning quality]
    Y --> W
    Z --> W
```

---

## Pipeline Module Architecture

How the cc-pipeline module relates to the rest of the toolchain. Teams install both modules; each handles a distinct layer.

```mermaid
flowchart TD
    subgraph INSTALL["Team installs"]
        M1[cc-pipeline module\n/pd-* commands\npd- skills + rules\nLinear MCP wired]
        M2[cc-qo-skills module\n/qo-* commands\nexecution skills\nConnectUI rules]
    end

    subgraph PIPELINE["cc-pipeline handles"]
        P1[/pd-start/ — classify issue]
        P2[/pd-scope/ — Haiku agent scoping]
        P3[/pd-plan/ — draft + post plan to Linear]
        P4[pd-guardrail rule — block until plan approved]
        P5[/pd-report/ — post execution report to Linear]
    end

    subgraph EXEC["cc-qo-skills handles"]
        E1[connectui-dev — load design system + code standards]
        E2[verify L1/L2/L3 — build · lint · tests]
        E3[qo-pr — PR description]
        E4[qo-prototype — Figma to code]
    end

    subgraph LINEAR["Linear — start and end"]
        L1[Issue with information standard]
        L2[Plan comment — awaiting approval]
        L3[Plan Approved status]
        L4[Phase transition updates]
        L5[Execution report]
    end

    M1 --> PIPELINE
    M2 --> EXEC
    P1 --> P2 --> P3 --> L2
    L2 --> L3
    L3 --> P4
    P4 --> EXEC
    EXEC --> P5
    P5 --> L5
    L1 --> P1
```

---

## M0 — Simplified POC Loop

The minimum viable version. Two human gates, no context packs, no Haiku scoping. Tests the core concept and builds the business case.

```mermaid
flowchart TD
    A([Input\nLinear]) --> B[Analyze and write\nimplementation plan\nClaude Code]
    B --> C{Human approval\nof plan\nLinear}
    C -- Approved --> D[Execute Plan\nClaude Code]
    C -- Rejected --> B
    D --> E[Tests and\nVerification\nClaude Code]
    E --> F{Human Review\nGitHub PR}
    F -- Approved --> G([Output\nGitHub + Preview Link])
    F -- Changes needed --> D
```

---

## Maturity Path

```mermaid
flowchart LR
    P["M0 — POC
    PEP template
    Linear skill
    Core loop demo"] --> A["M1 — Foundation
    Issue standards
    Plan approval gate
    GitHub PR enforcement
    Skills / rules layer"]
    A --> B["M2 — Context Engine
    Broad awareness
    Context packs
    Impact maps"]
    B --> C["M3 — Knowledge Layer
    Thin context catalog
    Cross-team dependency maps
    Catalog refresh"] --> D["M4 — Automation
    Execution reports
    Status automation
    Metrics + dashboards"]
```
