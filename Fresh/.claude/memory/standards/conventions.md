# ConnectUI Conventions

**Source**: `connect-ui-main/src/` — verified from real codebase

## Imports

- **No barrel imports** — always import from the specific file, never from `index.ts`
- Path alias `@/` maps to `src/`

```tsx
// ✓ Correct
import { OrionSwitch } from '@/components/OrionComponents/OrionSwitch'
import { ListCard } from './components/ListCard'

// ✗ Wrong
import { OrionSwitch } from '@/components/OrionComponents'
```

## Component files

- One component per file, filename matches component name
- Feature-scoped components live in `src/features/<Feature>/components/`
- Shared components live in `src/components/`
- Orion primitives live in `src/components/OrionComponents/`

## TypeScript

- Strict mode — no `any`, explicit return types on exported functions
- Props interfaces named `<ComponentName>Props`
- Custom styled-component props filtered with `shouldForwardProp`

```tsx
const Card = styled(Paper, {
  shouldForwardProp: (prop) => prop !== 'isActive',
})<{ isActive?: boolean }>(({ theme, isActive }) => ({ ... }))
```

## Styling

- `styled()` from `@mui/material/styles` — not `@emotion/styled`
- `sx` prop for one-off overrides, `styled()` for reusable styled variants
- No inline `style={{}}`, no CSS files, no Tailwind
- No hardcoded hex — always use theme tokens

## Routing

- TanStack Router, file-based routes in `src/routes/`
- Never edit `src/routeTree.gen.ts` — auto-generated

## State

1. React Query for server state
2. React Query cache for derived global state
3. `useState` / `useReducer` for local state
4. TanStack Form + Zod for form state
5. Zustand for cross-component client state

## Package manager

pnpm only. Never npm or yarn.

## Feature flags

`VITE_FF_*` prefix. Access via `import.meta.env.VITE_FF_*`.
