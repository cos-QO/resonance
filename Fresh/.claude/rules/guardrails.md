# Guardrails

These are the core workflow guardrails for this repo.

## Input guardrails

- Do not start a non-trivial UI task without:
  - product requirement
  - Figma reference
  - visual reference code or screenshots
  - acceptance criteria or clear success conditions

## Planning guardrails

- Do not build before analysis.
- Do not build before component mapping.
- Do not build before human approval of the plan.

## Build guardrails

- Reuse existing Queen One / ConnectUI components first.
- Use design tokens first.
- Avoid unnecessary custom CSS.
- Use Playwright during implementation for visual work.

## Handoff guardrails

- Do not hand off without preview evidence.
- Do not hand off without screenshots.
- Do not hand off without reused components and new components lists.
- Do not hand off without QA findings.
- Do not mark work done without human visual review.
