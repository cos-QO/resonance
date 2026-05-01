---
paths:
  - "src/components/**"
  - "src/pages/**"
  - "**/*.tsx"
  - "**/*.jsx"
  - "**/*.css"
  - "**/*.scss"
---
# Frontend Rules

## React Patterns
- Server Components where possible (no useState/useEffect needed)
- Client components only for interactivity (useState, useEffect, event handlers)
- Composition over inheritance
- Extract reusable hooks for shared stateful logic

## Accessibility
- Semantic HTML elements (nav, main, section, article)
- ARIA labels on interactive elements
- Keyboard navigation support
- Color contrast ratios (WCAG AA minimum)

## Styling
- Use project design system tokens (don't hardcode values)
- No inline styles — use CSS modules, Tailwind, or styled-components per project convention
- Responsive design: mobile-first approach
