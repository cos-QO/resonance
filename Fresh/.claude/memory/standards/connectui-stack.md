# ConnectUI Technology Stack

**Last Updated**: 2026-04-30
**Source**: `package.json` (auto-synced)

---

## Core Dependencies (pinned versions)

| Package | Version |
|---------|---------|
| `@mui/material` | `^7.1.0` |
| `@storybook/react-vite` | `^10.1.11` |
| `@tanstack/react-form` | `^1.12.3` |
| `@tanstack/react-query` | `^5.77.2` |
| `@tanstack/react-router` | `^1.120.5` |
| `react` | `^19.2.3` |
| `typescript` | `~5.8.3` |
| `vite` | `^6.3.5` |

---

## Architecture

| Layer | Technology |
|-------|-----------|
| Language | TypeScript strict (no `any`) |
| Runtime | Node 20+ |
| Package manager | **pnpm only** (never npm/yarn) |
| Bundler | Vite |
| UI | React + MUI v7 + Queen One design system |
| Routing | TanStack Router v1 (file-based, `src/routes/`) |
| Server state | TanStack Query v5 |
| Form state | TanStack Form v1 + Zod |
| Client state | Zustand + Immer |
| Backend | Firebase (Auth, Firestore, Storage) |
| Tests | Vitest + Playwright |
| Components | Storybook |

## State Hierarchy (use in this order)

1. **React Query** — server state (`useQuery`, `useMutation`)
2. **React Query cache** — derived global client state
3. **useState / useReducer** — component-local state
4. **TanStack Form** — form state (with Zod validation)
5. **Zustand** — cross-component client state

## Project Structure

```
src/
  components/     shared + Orion components
  features/       feature-scoped code (components, hooks, queries)
  hooks/          shared/generic hooks only
  routes/         TanStack Router file-based routes
  routeTree.gen.ts  AUTO-GENERATED — never edit
  theme.ts        MUI theme override (authoritative design tokens)
  stories/        cross-feature Storybook stories
```

## Anti-patterns

- No Context API for server state (React Query handles this)
- No prop drilling beyond 2 levels
- No Redux
- No `routeTree.gen.ts` edits
- No barrel imports (`index.ts` re-exports)
