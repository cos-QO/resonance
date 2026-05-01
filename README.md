# Queen One UI Workflow

This repo is a `Claude Code`-first workflow setup for supervised `UX/Figma -> production UI` work.

The operating model is simple:

- `Linear` holds the task, requirements, references, and milestone updates
- `Claude Code` does the real work
- `Figma`, `GitHub`, and `Playwright` provide the external context and verification tools
- humans supervise the plan, the visuals, and the final output

## What This Repo Contains

- `CLAUDE.md`
  Project memory for Claude Code. This is the official team-shared project memory file loaded automatically by Claude Code.
- `.claude/settings.json`
  Shared Claude Code project settings.
- `.claude/commands/`
  Project slash commands for the supervised UI workflow.
- `.claude/agents/`
  Project subagents for analysis, build, and QA.
- `.claude/memory/standards/`
  Queen One and ConnectUI standards used during analysis and implementation.
- `.mcp.json`
  Project MCP configuration for Linear, Figma, GitHub, Playwright, and Mermaid.
- `docs/supervised-session-architecture-v2.md`
  The main architecture and workflow design document.
- `docs/ui-dom-inspector.md`
  The plan for the browser-side inspector layer that will improve agent vision.

## Official Claude Code Shape

This repo follows Anthropic's Claude Code project conventions:

- project memory in `CLAUDE.md`
- shared project settings in `.claude/settings.json`
- project slash commands in `.claude/commands/`
- project subagents in `.claude/agents/`
- project-shared MCP servers in `.mcp.json`

## Workflow

1. Create or update a Linear issue with:
   - product requirement
   - Figma reference
   - visual reference code or screenshots
   - acceptance criteria
2. Run Claude Code in this repo.
3. Use the project commands:
   - `/qo-ui-kickoff`
   - `/qo-ui-analyze`
   - `/qo-ui-build`
   - `/qo-ui-qa`
   - `/qo-ui-report`
4. Review the output in the browser with Playwright-backed screenshots and previews.
5. Update Linear with milestone summaries and the final outcome.

## Notes

- Playwright is mandatory for visual work in this workflow.
- Reuse existing design-system components first.
- Use design tokens first.
- Do not mark work done without human visual review.

## Documentation

- [docs/supervised-session-architecture-v2.md](./docs/supervised-session-architecture-v2.md)
- [docs/ui-dom-inspector.md](./docs/ui-dom-inspector.md)
- [docs/README.md](./docs/README.md)
