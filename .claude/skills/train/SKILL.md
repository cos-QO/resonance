---
name: train
description: "Launch autonomous skill/rule/agent improvement loop. Iteratively proposes, tests, and evaluates changes — keeping improvements, discarding regressions. Like autoresearch but for Claude Code skills."
argument-hint: "<skill-name|agent-name|rule-name|discover|all-skills> [--max-iterations N]"
user_invocable: true
agent: trainer
model: sonnet
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Skill
---

# /train — Autonomous Skill Improvement

Launch an autoresearch-inspired improvement loop on skills, agents, or rules. The trainer proposes changes one at a time, evaluates each against skill-eval scoring, and keeps improvements while discarding regressions.

## Usage

```
/train <target>              # Improve a specific skill/agent/rule
/train discover              # Find and improve the 3 weakest skills
/train all-skills            # Improve all skills sequentially
/train <target> --max-iterations 5   # Custom iteration limit
```

## Target Resolution

Based on `$ARGUMENTS`, resolve the target:

### Named target (skill, agent, or rule)
1. Check `/.claude/skills/$TARGET/SKILL.md` — if exists, treat as skill
2. Check `/.claude/agents/$TARGET.md` — if exists, treat as agent
3. Check `/.claude/rules/$TARGET.md` — if exists, treat as rule
4. If none found, report error and stop

### `discover` mode
1. List all skills in `/.claude/skills/*/SKILL.md`
2. Run trigger accuracy evaluation on each
3. Rank by score (lowest first)
4. Run improvement loop on top 3 weakest (max 5 iterations each)

### `all-skills` mode
1. List all skills in `/.claude/skills/*/SKILL.md`
2. Skip skills already at 50/50
3. Run improvement loop on each (max 5 iterations each)

## Parse max-iterations
- Default: 10 for single target, 5 for discover/all-skills
- Override: `--max-iterations N` in arguments

## Workflow

Invoke the **trainer** agent with:

```
Target: <resolved file path>
Mode: <single|discover|all-skills>
Max iterations: <N>
```

The trainer agent handles the full improvement loop autonomously (see trainer.md for loop details).

## What the trainer does per iteration
1. Reads target file + counts lines
2. Evaluates current quality (trigger accuracy for skills, structural review for agents/rules)
3. Loads scenario file from `training/scenarios/<target>-scenarios.json` if it exists (uses stable test prompts/criteria)
4. Classifies the proposed change into a `change_category` (`clarity|trigger|workflow|antipattern|alignment|simplification`)
5. Proposes ONE focused change
6. Applies the change
7. Re-evaluates — scores the modified version; for skills, captures FP/FN counts separately
8. Keeps if improved (or simpler at same score), discards if worse (with `failure_reason`)
9. Logs 16-column TSV to `/.claude/memory/reports/training/results.tsv`
10. Commits kept changes: `train(<target>): <description> [score: X→Y]`
11. Stops after convergence (3 consecutive discards) or max iterations

## Safety
- Trainer cannot modify: skill-eval, hooks, settings, CLAUDE.md, version.json, training-protocol
- Every attempt is logged (kept and discarded)
- Every kept change gets a git commit for audit trail
- See `/.claude/memory/standards/training-protocol.md` for full guardrails

## After Training
The trainer outputs a summary report with:
- Iterations run, changes kept/discarded
- Score progression (before → after)
- Line count changes
- Convergence status
