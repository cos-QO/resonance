---
name: brainstorm
description: "Use when a request is ambiguous, creative, or has multiple valid approaches and needs design exploration before implementation. Triggers on 'brainstorm', 'explore options', 'what approach', 'how should we', 'design session', or when requirements are unclear. NOT for executing plans (use /planning) or researching external technologies (use /research)."
argument-hint: [topic-or-question]
context: fork
agent: pm
---
# /brainstorm — Socratic Design Exploration

Explore the design space through structured questioning before committing to implementation.

## Iron Law

**DESIGN BEFORE IMPLEMENTATION.** Never jump to code when the approach is unclear. Brainstorming ends with a chosen design and a saved document — not with code.

## Process

### Step 1: Understand Context
- Check project state: existing code, patterns, recent changes
- Read relevant memory standards and conventions
- Identify what's known vs what's ambiguous

### Step 2: Clarify the Problem
- Ask ONE clarifying question at a time — never a wall of questions
- Prefer multiple-choice when possible (easier to answer)
- Each question should narrow the solution space
- Maximum 3-5 questions before proposing approaches
- Focus on: purpose, constraints, success criteria, non-goals

### Step 3: Propose Approaches
Present 2-3 genuinely different approaches (not cosmetic variations):

For each approach include:
- **Summary**: One sentence
- **Tradeoffs**: Concrete pros and cons
- **Effort**: Tiny / Small / Medium / Large
- **Risk**: What could go wrong

Lead with your recommendation and explain why.

### Step 4: Refine and Decide
- User selects or combines approaches
- Ask targeted follow-up questions about the selected approach
- Identify edge cases and potential blockers
- Lock in key decisions

### Step 5: Save Design
- Write design document to `/.claude/memory/discovery/DESIGN-[topic]-[date].md`
- Include: chosen approach, rejected alternatives with reasons, key decisions, open questions
- This document feeds into `/planning` when execution follows

## After Brainstorming

Suggest next step explicitly:
> "Design saved. Ready to execute? I can create an execution plan from this design with `/planning`."

If the user wants to proceed, the PM uses the design document as input to the planning workflow.

## Rules
- One question at a time — never overwhelm
- Approaches must be genuinely different, not minor variations
- Always include effort estimates and risk assessment
- If user says "just do it" or "pick one" — give your recommendation and proceed
- Save every brainstorm output to memory for future reference
- YAGNI — strip unnecessary features from all proposed designs
- Keep designs focused enough for a single planning cycle

## Arguments
- `$ARGUMENTS` — Topic, question, or problem to explore
