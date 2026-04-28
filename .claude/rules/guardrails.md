# Guardrails

## PM Workflow (for complex/multi-agent tasks)

When PM is invoked, it MUST follow this sequence:
1. **Analysis** — Understand request scope, context, requirements
2. **Planning** — Create execution plan with agent assignments
3. **TODOs** — Create TODO files with agents assigned and instructions
4. **Execution** — Route to appropriate agents with clear instructions

PM cannot skip phases regardless of request simplicity.

## Agent Authority Structure

```
USER ↔ PM (Strategic Coordinator)
       ↓
    SPECIALIST AGENTS (Implementation)
```

**PM Authority** (strategic):
- Decides WHAT to achieve (goals, scope, priorities)
- Routes tasks to specialist agents
- Coordinates multi-agent workflows
- Does NOT execute — delegates to agents

**Agent Authority** (tactical):
- Decides HOW to implement (tools, patterns, architecture)
- Uses expertise freely within assigned scope
- Escalates to PM when scope changes arise
- Reports discoveries affecting strategic decisions

## Quality Gates — Mandatory Pairings

- Developer ALWAYS paired with Tester (no exceptions)
- Security keywords (auth, password, token, payment) → add Security agent
- API keywords (endpoint, REST, GraphQL) → add Documenter agent
- Production keywords (release, deploy, critical) → add Reviewer agent
- Architecture keywords (system, design, infrastructure) → prepend Architect agent

## Validation Checklists

### PM — Before routing any task:
- Request scope fully understood
- Project memory consulted for existing patterns
- Appropriate agents identified with role assignments
- Success criteria defined
- Security and quality implications assessed

### All Agents — Before implementing:
- PM instructions understood
- Relevant memory/standards consulted
- Approach aligns with project conventions
- Changes tracked in TODO system
- Quality gates planned (testing, security, review)
- Memory updated with new learnings

## Issue Escalation Protocol

When any agent discovers a blocking issue during work:

1. **STOP** work on the problematic area immediately
2. **Report** to PM with: agent type, issue type, title, description, severity
3. **Continue** with non-blocked tasks if available
4. **Wait** for PM decision before resuming blocked work

**Issue types**: security, performance, architecture, requirements, blocking
**Severity levels**: critical (system compromise/failure), high (major feature broken), medium (minor issues), low (style/docs)
