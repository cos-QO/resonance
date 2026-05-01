---
paths:
  - "src/components/**"
  - "src/features/**"
  - "**/*.tsx"
  - "**/*.ts"
---
# Frontend Rules — ConnectUI / Queen One

## Stack
React 19 + MUI v7 + Queen One Orion design system. TypeScript strict. Vite. pnpm only.

## Component resolution order — always follow this sequence

1. **Orion component exists?** → use it (OrionSwitch, OrionInput, OrionAlert, OrionSnackbar, OrionToggleButtonGroup, OrionIconButton, OrionAnimatedIconButton)
2. **Standard MUI component covers it?** → use it with `sx` tokens, no overrides
3. **Custom layout/container needed?** → `styled(Box)` or `styled(Paper)` with `shouldForwardProp`
4. **New reusable UI primitive?** → new Orion component in `src/components/OrionComponents/` + Storybook story

Never skip steps. Never build custom when Orion exists.

## Import patterns

```tsx
// Orion components — direct file import, never from index
import { OrionSwitch } from '@/components/OrionComponents/OrionSwitch'
import { OrionInput } from '@/components/OrionComponents/OrionInput'
import { OrionToggleButtonGroup } from '@/components/OrionComponents/OrionToggleButtonGroup'

// MUI components + styling
import { Box, Typography, Button, Chip } from '@mui/material'
import { styled } from '@mui/material/styles'
import { useTheme } from '@mui/material'
```

No barrel imports. Never `from '@/components/OrionComponents'` — always the specific file.

## Styling: styled() pattern

```tsx
// Always from @mui/material/styles, not @emotion/styled
import { styled } from '@mui/material/styles'

// Custom props require shouldForwardProp
const Container = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isActive' && prop !== 'variant',
})<{ isActive?: boolean }>(({ theme, isActive }) => ({
  padding: theme.spacing(4),           // → 16px
  backgroundColor: isActive
    ? theme.palette.queen[100]
    : theme.palette.background.default,
  borderRadius: theme.shape.borderRadius,
}))

// No custom props → no shouldForwardProp needed
const Header = styled(Box)(({ theme }) => ({
  marginBottom: theme.spacing(6),      // → 24px
  display: 'flex',
  gap: theme.spacing(2),               // → 8px
}))
```

## Styling: sx prop pattern

```tsx
// Use semantic token shortcuts when possible
<Box sx={{ color: 'text.primary', bgcolor: 'background.default' }} />

// Use theme.palette for queen palette and custom colors
<Box sx={{ bgcolor: (theme) => theme.palette.queen[150] }} />

// Never hardcode hex values in sx
// ✗ sx={{ color: '#7F1BF6' }}
// ✓ sx={{ color: 'primary.main' }}
```

## Spacing

Custom scale — NOT n×8px. Use integer indexes:
- `theme.spacing(1)` = 4px
- `theme.spacing(2)` = 8px
- `theme.spacing(3)` = 12px
- `theme.spacing(4)` = 16px
- `theme.spacing(6)` = 24px
- `theme.spacing(7)` = 40px

For values not in the scale, use pixel strings: `gap: '6px'`

## Typography

```tsx
// Always use Typography variants, never custom font-size in sx
<Typography variant="h5">Section title</Typography>   // 24px/600
<Typography variant="body1">Body text</Typography>    // 14px/400
<Typography variant="subtitle1">Label</Typography>    // 16px/600
<Typography variant="caption">Small note</Typography> // 12px/400
```

## MUI v7 patterns

```tsx
// slotProps — NOT the deprecated InputProps / MenuProps
<TextField
  slotProps={{
    input: { endAdornment: <SearchIcon /> },
  }}
/>

<Select
  slotProps={{ paper: { elevation: 0 } }}
/>
```

## Paper elevation → queen palette

MUI Paper elevation maps to the queen palette (defined in theme.ts):
- elevation 0–1 → `queen[100]`
- elevation 2–3 → `queen[200]`
- elevation 4–5 → `queen[300]`
- elevation 6–7 → `queen[400]`

Use `<Paper elevation={N}>` instead of setting `backgroundColor` manually.

## What to never do

- No hardcoded hex values anywhere
- No inline `style={{}}` props — use `sx` or `styled()`
- No CSS files or CSS modules — MUI only
- No barrel imports from `index.ts`
- No Tailwind
- No `any` in TypeScript
- No editing `routeTree.gen.ts`
- No npm or yarn — pnpm only
