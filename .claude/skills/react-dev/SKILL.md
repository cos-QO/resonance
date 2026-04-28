---
name: react-dev
description: React and frontend UI specialization — components, hooks, Server Components, Next.js, Tailwind, accessibility (WCAG 2.1 AA). Use for UI/frontend work. For TypeScript-only logic use /typescript-dev. Routed by PM or invoked directly for frontend tasks.
context: fork
agent: developer
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, mcp__context7__resolve-library-id, mcp__context7__get-library-docs
---
# React/Frontend Development Mode

You are now in **React specialization mode**. Before writing any code:

## 1. Load Project Conventions
```bash
Read /.claude/memory/standards/conventions.md
```

## 2. Query Context7 for Latest Docs
Based on the task, query relevant library documentation:
- **React**: For hooks, Server Components, Suspense, transitions
- **Next.js**: For App Router, Server Actions, ISR, middleware
- **TailwindCSS**: For utility classes, responsive design, custom config
- **React Testing Library**: For component testing patterns

## 3. React Standards
- Functional components only (no class components)
- Custom hooks for reusable logic (`use` prefix)
- Proper dependency arrays in useEffect/useMemo/useCallback
- Use Server Components by default, Client Components only when needed
- Collocate component, styles, and tests
- Use `React.Suspense` for async boundaries
- Prefer controlled components for forms

## 4. Accessibility
- Semantic HTML elements (`nav`, `main`, `section`, not `div` soup)
- ARIA labels on interactive elements
- Keyboard navigation support
- Color contrast ratios (WCAG 2.1 AA)
- Focus management for modals/dialogs

## 5. Performance
- Lazy load routes and heavy components
- Use `React.memo` only when measured performance issue exists
- Image optimization (next/image or srcset)
- Avoid layout shifts (explicit dimensions)

## Task
$ARGUMENTS
