Analyze the current supervised UI task.

## Before starting

Read these files:
- `.claude/memory/standards/connectui-component-map.md` — decision tree + Figma → token mapping
- `.claude/memory/standards/connectui-design-system.md` — palette, typography, spacing
- `.claude/rules/frontend.md` — MUI patterns and what not to do

## Steps

1. Read the Linear issue and all comments
2. Inspect the Figma reference via `mcp__figma__get_figma_data`
3. For every UI element in the Figma:
   - Map colors → theme palette tokens (use the mapping table in connectui-component-map.md)
   - Map text styles → MUI typography variants
   - Map spacing values → spacing scale indexes
   - Run the decision tree: Orion component → MUI component → styled() → new Orion
4. Inspect the relevant feature folder and any similar existing screens
5. Produce the output below

## Output

- **Requirement summary**
- **Layout summary** (structure, breakpoints)
- **Reusable component map** — each element mapped to: component name, import path, key props
- **Token guidance** — exact palette keys, typography variants, spacing indexes
- **Gaps** — what needs styled() or a new Orion component
- **Deviations** — Figma values that don't map to existing tokens (flag, don't hardcode)
- **Implementation plan** — ordered build steps
- **Open questions**

## Rules

- Check Orion components first — always
- No hardcoded hex values — map to tokens
- No barrel imports — identify the exact file path for each component
- Do not write implementation code
- Stop and wait for human approval before build starts
