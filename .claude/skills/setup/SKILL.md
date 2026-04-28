---
name: setup
description: Fix paths, validate MCP servers, and configure the orchestration system after installing .claude/ into a new project. Use after copying .claude/ folder or when MCP/hooks are broken.
argument-hint: [fix | check]
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
disable-model-invocation: true
---
# /setup — Post-Installation Configuration

Run this after copying `.claude/` into a new project to fix paths, validate MCP, and ensure everything works.

## Modes

### `/setup` or `/setup fix` (default)
Full fix — detect and repair all path issues.

### `/setup check`
Dry run — report issues without fixing.

## Workflow

### Step 1: Detect Project Root
```
project_root = find the directory containing .claude/
Confirm: "Project root: {project_root}"
```

### Step 2: Validate & Fix settings.json Permissions
Invalid MCP permission rules (patterns in parens like `mcp__filesystem__write_file(.claude/**)`) produce a "Settings Warning" on every startup. Claude Code only accepts MCP rules without paths — e.g. `mcp__filesystem__*` or `mcp__filesystem__write_file`.

Run the fixer (always, in both `fix` and `check` modes):
```bash
# check mode — report only
python3 .claude/scripts/fix-permissions.py --check

# fix mode — apply (creates settings.json.bak-<timestamp>)
python3 .claude/scripts/fix-permissions.py --fix
```

Behavior:
- **allow** entries with parens → removed (covered by `mcp__<server>__*`).
- **deny** entries with parens → replaced with un-parenthesized hard-deny + deduped.
- Backup written before any change.
- If fixes were applied, tell the user to **restart Claude Code** before continuing — the current session is still running with the old (skipped) rules.

### Step 3: Validate .mcp.json
Check if `.mcp.json` exists at the project root (NOT inside .claude/).

```
If .mcp.json missing at project root:
  - Check if .claude/.mcp.json or .claude/mcp.json exists
  - Copy it to project root as .mcp.json
  - Report: "Copied .mcp.json to project root"

If .mcp.json exists:
  - Parse JSON — report if invalid
  - For each MCP server:
    - Check if command exists (npx, node, python3, etc.)
    - For servers with file paths: verify paths exist
    - Report status per server
```

### Step 4: Fix Hardcoded Paths in Standards
Standards files may contain paths from the source project. Fix them:

```
For each file in .claude/memory/standards/:
  - Check for hardcoded absolute paths (e.g., /Users/*/Documents/*)
  - Replace project_root references with actual current project root
  - Specifically fix:
    - standards/tree.md → regenerate project_root field
    - standards/conventions.md → regenerate project_root field
```

### Step 5: Validate Hooks
```
For each hook script referenced in settings.json:
  - Check the .py file exists in .claude/hooks/
  - Check it has execute permission
  - Fix permissions if needed (chmod +x)
  - Report status per hook
```

### Step 6: Validate settings.json structure
```
Check .claude/settings.json:
  - Parse JSON — report if invalid
  - Verify hook commands reference correct paths
  - Check $CLAUDE_PROJECT_DIR usage in hook commands
  (Step 2 already repaired invalid MCP permission rules.)
```

### Step 7: Validate Plugin Config
```
If .claude/.claude-plugin/plugin.json exists:
  - Parse JSON — report if invalid
  - Verify hooks.json exists and is valid

If using plugin mode (--plugin-dir):
  - Verify ${CLAUDE_PLUGIN_DIR} variables in hooks.json
```

### Step 8: Validate Agent Memory
```
Check .claude/agent-memory/:
  - pm/MEMORY.md exists
  - developer/MEMORY.md exists
  - tester/MEMORY.md exists
  - Report if any are missing (create empty if needed)
```

### Step 9: Clean Stale Data
```
If .claude/memory/active/execution-tracker.json exists:
  - Warn: "Active execution tracker found from previous project"
  - Ask user: keep or remove?

If .claude/memory/todos/ has files:
  - Warn: "Active TODOs found from previous project"
```

## Output Format

```markdown
# Setup Report

**Project**: {project_root}
**Mode**: fix / check

| Check | Status | Details |
|-------|--------|---------|
| Permission rules | OK/FIXED | [invalid MCP rules removed/rewritten] |
| .mcp.json | OK/FIXED/MISSING | [location, servers found] |
| Standards paths | OK/FIXED | [files updated] |
| Hook scripts | OK/FIXED | [permissions, missing] |
| settings.json | OK/WARN | [parse status] |
| Plugin config | OK/SKIP | [if present] |
| Agent memory | OK/CREATED | [which agents] |
| Stale data | OK/WARN | [tracker, TODOs] |

## Actions Taken
[List of fixes applied, or issues to fix manually]

## Next Steps
- **If permissions were fixed, restart Claude Code** (current session still has the old rules loaded)
- Run `/prepare` to analyze the project and populate standards
- Run `/init-extend` to merge architecture into CLAUDE.md
```

## Task
$ARGUMENTS
