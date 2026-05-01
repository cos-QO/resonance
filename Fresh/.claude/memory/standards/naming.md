# Naming Conventions — ConnectUI

**Source**: `connect-ui-main/src/` — verified from real codebase

## Files and folders

| Type | Convention | Example |
|---|---|---|
| React component file | PascalCase `.tsx` | `ListCard.tsx` |
| Hook file | camelCase `.ts` | `useLists.ts` |
| Utility file | camelCase `.ts` | `formatDate.ts` |
| Feature folder | PascalCase | `src/features/DragonTiles/` |
| Component folder | PascalCase | `src/components/OrionComponents/` |
| Route file | TanStack Router convention | `_auth.settings.$siteId.lists.tsx` |

## Identifiers

| Type | Convention | Example |
|---|---|---|
| Component | PascalCase | `ListsPage`, `OrionSwitch` |
| Styled component | PascalCase, descriptive | `StyledContainer`, `HeaderSection` |
| Hook | `use` prefix + PascalCase | `useLists`, `useDeleteList` |
| Props interface | `<Component>Props` | `OrionInputProps`, `WizardContainerProps` |
| Event handler | `handle` prefix | `handleChange`, `handleBlur` |
| Boolean state | `is` / `has` / `show` prefix | `isLoading`, `hasError`, `showModal` |
| Constants | SCREAMING_SNAKE_CASE | `STORYBOOK_PROPS`, `VITE_FF_FEATURE` |

## MUI component overrides

Orion custom components follow `Orion<ComponentName>` pattern:
- `OrionSwitch` (not `CustomSwitch` or `QueenSwitch`)
- `OrionToggleButtonGroup`
- `OrionInput`

Styled layout components within a file are descriptive:
- `StyledContainer`, `HeaderSection`, `SearchSection`, `LoadingCard`
