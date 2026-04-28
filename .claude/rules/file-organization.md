# File Organization

## Root Directory Protection
NEVER add test files, temporary files, or experimental content to project root:
- Tests → designated test directories or `.claude/tests/`
- Temporary files → `.claude/temp/` or system temp
- Documentation → `.claude/memory/` or project `docs/`
- Artifacts → `.claude/artifacts/` before project integration
- Keep root clean — only production-ready project files

## File Creation Discipline
Before creating ANY file or folder:
1. Check existing structure — understand current organization
2. Follow established conventions — use existing naming patterns
3. Place in correct location — follow `.claude/memory/standards/folder-structure.md`
4. Update relevant memory — document new patterns for future reference

## Agent File Access

**All agents can READ+WRITE**: `memory/`, `tests/`, `artifacts/`, `temp/`
**All agents READ-ONLY**: `agents/`, `hooks/`, `skills/`, `rules/`
**Documenter has FULL ACCESS**: all folders (system maintainer role)
