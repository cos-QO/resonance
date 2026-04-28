# Training Protocol — Immutable Guardrails

This document defines the rules for the autonomous training loop. The trainer agent MUST read this before every session and CANNOT override these rules.

## Scope Boundaries

### What the trainer CAN modify
- Skill files: `/.claude/skills/*/SKILL.md`
- Agent definitions: `/.claude/agents/*.md` (except protected agents)
- Rule files: `/.claude/rules/*.md`

### What the trainer CANNOT modify (protected)
```
/.claude/skills/skill-eval/SKILL.md    # Evaluation system — immutable
/.claude/hooks/*                        # Hook infrastructure
/.claude/settings.json                  # Claude Code settings
/.claude/settings.local.json            # Local settings
/.claude/CLAUDE.md                      # Architecture doc
/.claude/version.json                   # Version tracking
/.claude/memory/standards/training-protocol.md  # This file
/.claude/agents/pm.md                   # Core orchestration agent
```

### One file per iteration
The trainer modifies exactly ONE file per iteration. No batch edits, no multi-file changes.

## Evaluation Criteria (scored out of 50)

### Trigger Accuracy (skills) — /50
- Generate 5 positive prompts (should trigger) + 5 negative prompts (should not)
- Score each prompt on a 5-point rubric:
  1. **Accuracy** (0-1) — correct trigger/no-trigger decision
  2. **Specificity** (0-1) — triggers for the right reason, not keyword overlap
  3. **Boundary clarity** (0-1) — respects NOT clauses and scope limits
  4. **Confidence** (0-1) — unambiguous match, not borderline
  5. **Distinctness** (0-1) — doesn't also match a competing skill
- Total per prompt: 0–5. Total score: 10 prompts × 5 = **50**

### Thresholds
- **45-50/50**: PASS — skill is well-tuned
- **35-44/50**: NEEDS WORK — improvement possible
- **< 35/50**: FAIL — significant issues

### Structural Quality Checklist
Every skill must satisfy:
1. **Specific** — Lists concrete capabilities, not vague categories
2. **Bounded** — Has NOT clauses for disambiguation
3. **Distinct** — No significant overlap with other auto-invoke skills
4. **Actionable** — Clear what it does, not just what it's "about"
5. **Correct agent** — References an active, non-archived agent
6. **Right model** — Appropriate compute for the task

## Decision Logic

```
score_improved                          → KEEP + commit
score_equal AND fewer_lines             → KEEP + commit (simpler is better)
score_equal AND same_or_more_lines      → DISCARD
score_worse                             → DISCARD + revert
```

### Simplicity Preference
When two versions score equally, the shorter one wins. Complexity must pay for itself with measurably better results.

## Convergence

### When to stop
- 3 consecutive DISCARDED iterations (no more easy wins)
- Max iterations reached (default: 10 per target)
- Perfect score (50/50) with no simplification possible
- Target file cannot be parsed or is missing

### Session limits
- Default max iterations per target: 10
- Discover mode: max 5 iterations per skill, top 3 weakest
- All-skills mode: max 5 iterations per skill

## Results Tracking

All attempts (KEPT and DISCARDED) logged to:
```
/.claude/memory/reports/training/results.tsv
```

Format: TSV with 16 columns:
```
timestamp  target  iteration  change_description  score_before  score_after  lines_before  lines_after  status  commit_hash  change_category  failure_reason  fp_count  fn_count  scenario_file  standards_consulted
```

**Columns 1–10** (original): timestamp, target, iteration, change_description, score_before, score_after, lines_before, lines_after, status, commit_hash.

**Columns 11–16** (extended):
| Column | Type | Values |
|--------|------|--------|
| `change_category` | enum | `clarity`, `trigger`, `workflow`, `antipattern`, `alignment`, `simplification` |
| `failure_reason` | text | Short reason (max 60 chars) for DISCARDED/ERROR; `-` for KEPT |
| `fp_count` | int | False positive score lost from trigger test (0–25); `-` for agents/rules |
| `fn_count` | int | False negative score lost from trigger test (0–25); `-` for agents/rules |
| `scenario_file` | text | Basename of scenario JSON used, or `-` |
| `standards_consulted` | bool | `yes` or `no` |

Old 10-column rows are backward compatible — missing columns default to `-`.

This file is NOT committed to git — it is a local experiment log.

## Logging Requirements

Every TSV row MUST include:
1. **change_category** — classify the change into exactly one of the 6 enums before applying it
2. **failure_reason** — on DISCARD, record why: `score_decreased`, `no_improvement_larger`, `regression:<specific>`, `error:<specific>`; on KEEP, write `-`
3. **fp_count / fn_count** — for skills, record separately (not just aggregate /50); for agents/rules, write `-`
4. **scenario_file** — if a scenario file was loaded, record its basename; otherwise `-`
5. **standards_consulted** — `yes` if training-protocol.md was read this session (should always be `yes`)

## Evaluation Quality Rules

1. **Scenario files are authoritative** — when `training/scenarios/<target>-scenarios.json` exists, its `trigger_scenarios` and `structural_quality.criteria` MUST be used instead of ad-hoc generated prompts/criteria
2. **Stable test sets** — reuse the same test prompts across iterations within a session so scores are comparable
3. **FP/FN separation** — for skills, track false positives (negative prompts that incorrectly trigger) and false negatives (positive prompts that fail to trigger) independently, not just a total score

## Git Discipline

- Every KEPT change gets a commit: `train(<target>): <description> [score: X→Y]`
- DISCARDED changes are reverted: `git checkout -- <file>`
- Never amend previous commits — always create new ones
- Never force push

## Safety Rules

1. Never modify the evaluation system to inflate scores
2. Never skip logging — every attempt is recorded
3. Never exceed max iterations — respect convergence
4. Never modify infrastructure files — even if they seem "improvable"
5. Never introduce security vulnerabilities in skill/agent instructions
6. If an iteration causes an error, log it as ERROR and continue
