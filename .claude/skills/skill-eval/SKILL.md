---
name: skill-eval
description: Evaluate, benchmark, and optimize skill descriptions and triggering behavior. Tests if skills activate on correct prompts and stay quiet on incorrect ones. Use to audit skill quality, run A/B comparisons, or optimize descriptions.
argument-hint: [skill-name | "all" | "benchmark skill-name"]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
disable-model-invocation: true
---
# /skill-eval — Skill Evaluation & Optimization

Evaluate skills for triggering accuracy, description quality, and effectiveness.

## Modes

Based on `$ARGUMENTS`, run one of these modes:

### Mode 1: Single Skill Eval (`/skill-eval python-dev`)

1. **Read** the skill from `/.claude/skills/$SKILL_NAME/SKILL.md`
2. **Analyze** the frontmatter:
   - Is `description` specific enough? Does it have NOT clauses for disambiguation?
   - Is `disable-model-invocation` correctly set? (manual vs auto)
   - Does `agent` reference an active agent? (check `/.claude/agents/`)
   - Are `allowed-tools` appropriate for the skill's purpose?
   - Does the body match what the description promises?
3. **Generate test prompts** — 5 positive (should trigger) + 5 negative (should NOT trigger):

```markdown
## Trigger Tests for: python-dev

### SHOULD trigger (positive):
1. "Write a Python script to parse CSV files"
2. "Create a FastAPI endpoint for user registration"
3. "Add type hints to the utils module"
4. "Set up pytest fixtures for the auth module"
5. "Refactor this Python class to use async/await"

### Should NOT trigger (negative):
1. "Build a React component for the dashboard" → react-dev
2. "Design the REST API schema" → api-dev
3. "Fix the CI/CD pipeline" → devops-dev
4. "Why is this function throwing an error?" → debug
5. "Compare Flask vs Express for our backend" → research
```

4. **Score each prompt** — Would Claude's auto-invocation match correctly?
   - For each positive: Is the description specific enough to be selected?
   - For each negative: Does the NOT clause or specificity prevent false triggering?
   - For manual-only skills: Are the trigger words clear enough for human invocation?

5. **Rate the skill**:
   - **PASS** (9-10/10 correct triggers)
   - **NEEDS WORK** (7-8/10)
   - **FAIL** (< 7/10)

6. **Suggest improvements** if score < 10/10

### Mode 2: Full Audit (`/skill-eval all`)

Run Mode 1 on every skill in `/.claude/skills/*/SKILL.md`.

Generate a summary report:

```markdown
# Skill Audit Report
**Date**: [timestamp]
**Skills evaluated**: [count]

## Results
| Skill | Mode | Score | Status | Issues |
|-------|------|-------|--------|--------|
| python-dev | AUTO | 10/10 | PASS | — |
| planning | AUTO | 7/10 | NEEDS WORK | Too broad, triggers on feature requests |
| scope | MANUAL | 9/10 | PASS | Minor: "analyze" overlap with research |

## Conflict Matrix
[Skills that compete for the same prompts]

## Recommendations
[Prioritized list of description improvements]
```

Save report to `/.claude/memory/reports/skill-eval/EVAL-<timestamp>.md`

### Mode 3: Benchmark (`/skill-eval benchmark python-dev`)

Compare skill-loaded vs. baseline output:

1. **Generate 3 test tasks** appropriate for the skill
2. **For each task**, evaluate:
   - **With skill**: What specific guidance does the skill add? (patterns, standards, Context7 queries)
   - **Without skill**: What would the raw developer agent do?
   - **Delta**: What does the skill add that the agent wouldn't do on its own?
3. **Score the skill's value-add**:
   - **HIGH**: Skill adds patterns, standards, or tool access the agent lacks
   - **MEDIUM**: Skill reinforces good practices but agent would mostly get it right
   - **LOW**: Skill adds no meaningful value over the base agent — consider retiring

```markdown
# Benchmark Report: python-dev
**Date**: [timestamp]

## Test 1: "Create a FastAPI CRUD endpoint"
### With skill:
- Queries Context7 for FastAPI patterns ✓ (agent can't do this alone)
- Enforces type hints on all signatures ✓ (agent might do this)
- Uses Pydantic models ✓ (agent might do this)
- Parameterized queries only ✓ (skill-specific enforcement)

### Without skill:
- No Context7 access for latest patterns
- Might use type hints but not enforced
- Might use Pydantic but not guaranteed

### Delta: HIGH — Context7 access + enforced patterns

## Overall Value: HIGH / MEDIUM / LOW
## Recommendation: KEEP / OPTIMIZE / RETIRE
```

Save report to `/.claude/memory/reports/skill-eval/BENCHMARK-<skill>-<timestamp>.md`

### Mode 4: Optimize Description (`/skill-eval optimize python-dev`)

1. Read the current description
2. Run Mode 1 (trigger analysis)
3. Identify trigger gaps or false positives
4. Rewrite the description to improve scoring
5. Present old vs. new description for approval
6. If approved, update the skill file

```markdown
## Description Optimization: python-dev

### Current (score: 8/10):
"Python language specialization — type hints, async/await..."

### Issues:
- Missing trigger for "data processing" tasks
- Could conflict with db-dev for SQLAlchemy work

### Proposed (expected score: 10/10):
"Python language specialization — type hints, async/await, PEP 8, pytest..."

### Changes:
- Added "data processing, scripting" to triggers
- Added NOT clause for SQLAlchemy schema work → /db-dev
```

## Worktree Awareness

If running in a worktree, write all reports to main repo's memory:
- Use `$CLAUDE_PROJECT_DIR/.claude/memory/reports/skill-eval/` for report output
- Skills are read-only — worktree isolation prevents accidental skill modification
- Optimized descriptions (Mode 4) should be staged, NOT directly written to skills/

## Evaluation Criteria

### Description Quality Checklist
- [ ] **Specific**: Lists concrete capabilities, not vague categories
- [ ] **Bounded**: Has NOT clauses pointing to alternative skills
- [ ] **Distinct**: No significant overlap with other auto-invoke skills
- [ ] **Actionable**: Clear what the skill does (not just what it's "about")
- [ ] **Correct agent**: References an active, non-archived agent
- [ ] **Right mode**: Manual for utility/pipeline skills, auto for contextual skills

### Common Anti-Patterns
- "Use for X" without specifying what X includes concretely
- Missing NOT clauses on auto-invoke skills
- Description promises features the body doesn't deliver
- Agent reference to archived/non-existent agent
- Auto-invoke on utility skills that should be manual

## Output Location
All reports saved to: `/.claude/memory/reports/skill-eval/`
