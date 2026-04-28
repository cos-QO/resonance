# Protected Files Registry

**Purpose**: Centralized list of files and directories that agents cannot modify
**Enforcement**: `protected-files-check.py` PreToolUse hook
**Last Updated**: 2026-02-02

---

## Overview

This registry defines files and directories that are **protected** from agent modification to maintain system integrity and prevent accidental breaking changes.

**Protection applies to all agents** except `documenter` (system maintainer).

---

## Protected Categories

### 1. System Configuration Files

**Critical**: These files control Claude Code behavior and must not be modified by agents.

```yaml
- claude/settings.json
- claude/.claude-project.json
- .gitignore
- .git/config
```

**Reason**: Configuration changes could break hooks, permissions, or integrations.

---

### 2. Agent Definitions

**Critical**: Agent behavior must remain consistent across sessions.

```yaml
- claude/agents/**/*.md
```

**Examples**:
- `claude/agents/pm.md`
- `claude/agents/developer.md`
- `claude/agents/tester.md`
- `claude/agents/security.md`

**Reason**: Agent modifications could cause unpredictable behavior or role confusion.

**Exception**: `documenter` agent can update agent docs when explicitly requested.

---

### 3. System Hooks

**Critical**: Hooks enforce system policies and must remain intact.

```yaml
- claude/hooks/*.py
- claude/hooks/*.sh
```

**Examples**:
- `claude/hooks/auto-commit.py`
- `claude/hooks/chain-checkpoint.py`
- `claude/hooks/compound-scope-enforcement.py`
- `claude/hooks/protected-files-check.py` (this hook itself!)

**Reason**: Hook modifications could disable enforcement or create security vulnerabilities.

---

### 4. Core Knowledge System

**Critical**: System knowledge must remain authoritative.

```yaml
- claude/knowledge/system/**/*.md
```

**Examples**:
- `claude/knowledge/system/agent-handoff-protocol.md`
- `claude/knowledge/system/todo-tracking-system.md`
- `claude/knowledge/system/subplan-isolation.md`

**Reason**: System knowledge defines protocols that must remain consistent.

**Exception**: `documenter` can update when improvements are needed.

---

### 5. Memory Standards

**Protected**: Standards define conventions that should not change frequently.

```yaml
- claude/memory/standards/security-standards.md
- claude/memory/standards/conventions.md
- claude/memory/standards/folder-structure.md
- claude/memory/standards/protected-files.md  # This file!
```

**Reason**: Frequent standard changes create confusion and inconsistency.

**Exception**: `documenter` or `pm` can update standards with user approval.

---

### 6. Slash Commands

**Protected**: Command definitions must remain stable.

```yaml
- claude/commands/**/*.md
```

**Examples**:
- `claude/commands/mode.md`
- `claude/commands/compound-start.md`
- `claude/commands/git-commit.md`

**Reason**: Command behavior must be predictable and documented.

**Exception**: `documenter` can update command documentation.

---

## Exception: Documenter Agent

The `documenter` agent has **full access** to protected files because it serves as the system maintainer.

**Documenter Responsibilities**:
- Update documentation when improvements needed
- Maintain consistency across system files
- Fix errors in protected documentation
- Update knowledge when protocols evolve

**Documenter Must**:
- Always check with user before modifying protected files
- Document all changes in commit messages
- Test changes don't break existing functionality
- Follow proper review process

---

## Protection Enforcement

### PreToolUse Hook

**File**: `claude/hooks/protected-files-check.py`

**Triggers On**:
- `Write` tool → Any file path
- `Edit` tool → Any file path
- `MultiEdit` tool → Any file path

**Validation Logic**:
```python
def is_protected(file_path: str, agent: str) -> bool:
    """Check if file is protected from this agent."""

    # Documenter has full access
    if agent == "documenter":
        return False

    # Load protected patterns
    protected_patterns = load_protected_patterns()

    # Check if file matches any protected pattern
    for pattern in protected_patterns:
        if matches_glob(file_path, pattern):
            return True

    return False
```

**Action on Violation**:
```
🚫 PROTECTED FILE: {file_path}

This file is protected from modification by {agent} agent.

Protected Category: {category}
Reason: {reason}

If you need to modify this file:
  1. Contact user for approval
  2. Use @documenter agent for documentation updates
  3. Submit request via proper channels

Operation BLOCKED.
```

---

## Protected Patterns (Glob Format)

```yaml
# System Configuration
protected:
  - "claude/settings.json"
  - "claude/.claude-project.json"
  - ".gitignore"
  - ".git/config"

# Agent Definitions
  - "claude/agents/**/*.md"

# System Hooks
  - "claude/hooks/*.py"
  - "claude/hooks/*.sh"

# Core Knowledge
  - "claude/knowledge/system/**/*.md"

# Memory Standards
  - "claude/memory/standards/*.md"

# Slash Commands
  - "claude/commands/**/*.md"

# Skills (optional protection)
  - "claude/skills/**/*.md"
```

---

## Unprotected Files

These files **can be modified** by all agents:

### Memory System (Working Files)

```yaml
allowed:
  # Active plans and TODOs
  - "claude/memory/active/**/*.md"
  - "claude/memory/todos/**/*.md"

  # Handoffs between agents
  - "claude/memory/handoffs/**/*.md"

  # Agent findings and discoveries
  - "claude/memory/compound/*/SUBPLAN-*/findings/**/*.md"

  # Archive (historical records)
  - "claude/memory/archive/**/*.md"

  # Logs and tracking
  - "claude/memory/chain-log.jsonl"
  - "claude/memory/git-commits.md"
  - "claude/memory/watchdog/**/*.yaml"
  - "claude/memory/watchdog/**/*.json"
```

### Project Files (Code and Tests)

```yaml
allowed:
  # Source code
  - "src/**/*"
  - "lib/**/*"
  - "app/**/*"

  # Tests
  - "tests/**/*"
  - "test/**/*"
  - "__tests__/**/*"

  # Build and configuration
  - "package.json"
  - "tsconfig.json"
  - "webpack.config.js"
  - "babel.config.js"

  # Documentation (project-level)
  - "README.md"
  - "docs/**/*.md"
  - "CHANGELOG.md"

  # Temporary files
  - "claude/temp/**/*"
  - "claude/artifacts/**/*"
```

---

## Violation Handling

### When Violation Occurs

1. **Hook blocks operation** (exit code 1)
2. **Error message displayed** to agent
3. **Violation logged** to `claude/memory/violations.log`
4. **User notified** (if in interactive session)

### Violation Log Format

**File**: `claude/memory/violations.log`

```
[2026-02-02T10:15:30Z] PROTECTED FILE VIOLATION
Agent: developer
File: claude/settings.json
Operation: Write
Category: System Configuration
Action: BLOCKED
Reason: Configuration changes could break system integrity
```

---

## Override Mechanism

In rare cases where protected file modification is legitimately needed:

### Option 1: Use Documenter Agent

```bash
# Request documenter to make change
Task(subagent_type='documenter', prompt='
  Update claude/agents/pm.md to add new fast-path pattern.
  User approved this change.
  Pattern: "deploy X" → @deployer agent
')
```

### Option 2: Manual User Edit

```bash
# User edits file directly
vim claude/settings.json

# Or using IDE
code claude/settings.json
```

### Option 3: Temporary Override (Not Recommended)

```python
# In protected-files-check.py
OVERRIDE_ENABLED = True  # Set to True to disable protection

# WARNING: Only for debugging/emergency
# Re-enable protection after change
```

---

## Best Practices

### For Agents

1. **Read protected files freely** - Protection only blocks writes
2. **Propose changes to user** - Ask user to modify protected files
3. **Use documenter agent** - For documentation updates
4. **Never bypass protection** - Always follow proper channels

### For Documenter Agent

1. **Ask user first** - Even with full access, confirm changes
2. **Document changes** - Clear commit messages
3. **Test thoroughly** - Ensure changes don't break functionality
4. **Follow standards** - Maintain consistency

### For Users

1. **Respect protections** - Protections exist for good reasons
2. **Review before overriding** - Understand risks
3. **Use documenter agent** - Proper channel for updates
4. **Keep standards updated** - Add new protections as needed

---

## Maintenance

### Adding New Protections

1. Update this file with new pattern
2. Test pattern matches correctly
3. Document reason for protection
4. Restart Claude Code to reload patterns

### Removing Protections

1. Verify protection no longer needed
2. Update this file
3. Document reason for removal
4. Restart Claude Code to reload patterns

---

## Testing Protection

### Test Protected File

```bash
# Test if file is protected
python3 claude/hooks/protected-files-check.py test \
  --file-path claude/settings.json \
  --agent developer

# Expected: BLOCKED
```

### Test Allowed File

```bash
# Test if file is allowed
python3 claude/hooks/protected-files-check.py test \
  --file-path claude/memory/active/PLAN-001.md \
  --agent developer

# Expected: ALLOWED
```

### Test Documenter Exception

```bash
# Test documenter has access
python3 claude/hooks/protected-files-check.py test \
  --file-path claude/settings.json \
  --agent documenter

# Expected: ALLOWED (documenter exception)
```

---

## Integration Points

### With Compound Scope Enforcement

Protected files check runs **before** compound scope enforcement:

```
Agent attempts Write →
  ↓
Protected files check (this hook) →
  ↓
If protected → BLOCK
  ↓
If not protected → Continue to compound scope check (if active) →
  ↓
If compound scope OK → Allow operation
```

### With Auto-Commit Hook

Protected files are automatically excluded from commits:

```python
# In auto-commit.py
protected_files = load_protected_patterns()

# Exclude from git add
for file in changed_files:
    if not is_protected(file):
        git_add(file)
```

---

## Security Considerations

**Why Protection is Critical**:

1. **System Stability** - Protected files define core behavior
2. **Consistency** - Standards must remain stable
3. **Security** - Hook modifications could disable safeguards
4. **Debugging** - Easier to diagnose issues when system files unchanged
5. **Collaboration** - Multiple agents don't conflict on system files

**Protection is NOT**:
- A replacement for version control
- A substitute for code review
- Protection from user modifications
- A guarantee against all errors

**Protection IS**:
- A safeguard against accidental agent modifications
- A consistency mechanism
- A system integrity tool
- A clear boundary between protected and working files

---

## Summary

**Protected Files**: Configuration, agents, hooks, system knowledge, standards, commands

**Unprotected Files**: Memory (active/todos/handoffs), project code, tests, documentation

**Exception**: Documenter agent has full access

**Enforcement**: PreToolUse hook blocks write operations

**Override**: Via documenter agent or manual user edit

**Purpose**: Maintain system integrity and prevent accidental breaking changes

---

**Status**: Active
**Enforcement**: Automatic (via hook)
**Maintained By**: System + Documenter Agent
**Review Frequency**: As needed
