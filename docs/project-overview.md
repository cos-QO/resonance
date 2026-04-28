# Project Overview

## What This Project Is

This project is designing a supervised agentic delivery pipeline built around `Linear`, `Claude Code` or `Cursor`, and `GitHub`.

It is intended to let product, design, engineering, and stakeholders work through a common system where:

- requirements and project context live in Linear
- agents can retrieve and reason over that context
- agents can draft plans and execute implementation work
- humans remain in the loop for approval, supervision, review, and acceptance

## Core Goal

Create a repeatable process where an issue can move from idea to delivered implementation with strong structure:

1. capture intent and requirements in Linear
2. gather broad context from across teams and projects
3. draft a structured implementation plan
4. get human approval before coding starts
5. execute in Claude Code or Cursor
6. open a GitHub pull request for review
7. merge and report outcomes back into Linear

## Why This Matters

Without structure, agents can be fast but fragile. They often:

- overfit to the current issue body
- miss adjacent team dependencies
- lose state between sessions
- produce outputs that are difficult for humans to audit

The pipeline should solve those problems by giving agents:

- high-quality context
- a clear operating model
- durable working memory
- strong human checkpoints

## Principles

- `Linear` is the human-facing source of truth for intent, ownership, approvals, and shared documentation.
- `Repo-local memory` is the agent-facing working ledger for plans, context packs, checkpoints, and reports.
- `GitHub` is the enforcement layer for review, CI, merge, and deployment controls.
- `Humans approve critical transitions`.
- `Broad awareness is mandatory for non-trivial work`.
- `Templates and consistency matter more than prompt cleverness`.

## Intended Users

- product managers
- product designers
- engineers
- technical leads
- stakeholders reviewing progress and outputs
- agents acting on behalf of those teams

## Current Direction

The current recommendation is to build a thin orchestration layer around Linear instead of creating a separate project management system.

That means:

- use Linear as the canonical operational workspace
- use a small amount of local structured memory for execution continuity
- use GitHub to enforce human quality gates

## Initial Scope

The first version should focus on a few guaranteed behaviors:

- every issue is created from a structured template
- every medium or large task generates a context pack
- every implementation starts with a written plan
- no merge happens without human PR review
- every completed issue receives an execution report
