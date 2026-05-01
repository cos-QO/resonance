# ConnectUI Component Map — Decision Tree + Import Patterns + Figma Mapping

**Source**: `connect-ui-main/src/` (local clone)
**Last Updated**: 2026-05-01

---

## Component Decision Tree

When building any UI element, follow this order:

```
Is there an Orion component for this?
  YES → use it (see Orion Components below)
  NO ↓

Is there a standard MUI component that covers it?
  YES → use it with sx tokens and theme palette
  NO ↓

Do you need a custom layout or container?
  YES → styled(Box) or styled(Paper) with shouldForwardProp
  NO ↓

Is this a reusable primitive that will appear in multiple places?
  YES → new Orion component in src/components/OrionComponents/ + Storybook story
  NO → build inline with sx props, don't abstract prematurely
```

---

## Orion Components

All live in `src/components/OrionComponents/`. Import directly from the file.

| Component | File | Use for |
|---|---|---|
| `OrionInput` | `OrionComponents/OrionInput.tsx` | Form text inputs (wraps TextField + TanStack Form) |
| `OrionSwitch` | `OrionComponents/OrionSwitch.tsx` | Toggle switches with Queen checkmark thumb |
| `OrionToggleButtonGroup` | `OrionComponents/OrionToggleButtonGroup.tsx` | Pill-style tab selectors |
| `OrionAlert` | `OrionComponents/OrionAlert.tsx` | Inline alerts |
| `OrionSnackbar` | `OrionComponents/OrionSnackbar.tsx` | Toast notifications |
| `OrionIconButton` | `OrionComponents/OrionIconButton.tsx` / `src/components/OrionIconButton/` | Icon-only action buttons |
| `OrionAnimatedIconButton` | `OrionComponents/OrionAnimatedIconButton.tsx` | Animated icon buttons |

Import pattern — always direct, never from index:
```tsx
import { OrionSwitch } from '@/components/OrionComponents/OrionSwitch'
import { OrionToggleButtonGroup } from '@/components/OrionComponents/OrionToggleButtonGroup'
import { OrionInput } from '@/components/OrionComponents/OrionInput'
```

---

## Orion Icons

All in `src/components/OrionIcons/`. Use over MUI icons when a Queen version exists.

```tsx
import { OrionEditIcon } from '@/components/OrionIcons/OrionEditIcon'
import { OrionDeleteIcon } from '@/components/OrionIcons/OrionDeleteIcon'
import { OrionSearchIcon } from '@/components/OrionIcons/OrionSearchIcon'
```

Full list: OrionCampaignIcon, OrionCartIcon, OrionClickIcon, OrionClockIcon,
OrionCodeEditorIcon, OrionCodeIcon, OrionDeleteIcon, OrionDollarIcon,
OrionDragHandleIcon, OrionEditIcon, OrionEmailIcon, OrionEmojiEmotionsIcon,
OrionLaptopIcon, OrionOpenMailIcon, OrionOutlineIcon, OrionPencilIcon,
OrionPeopleIcon, OrionRedoIcon, OrionSearchIcon, OrionSendIcon,
OrionSendInstantIcon, OrionSmartphoneIcon, OrionSmsIcon,
OrionTrendingDownIcon, OrionTrendingUpIcon, OrionUndoIcon,
OrionUploadIcon, OrionVisibilityIcon, OrionWalletIcon, OrionWarningIcon

---

## Custom Component Pattern

When building a custom container or section layout:

```tsx
import { Box, Paper } from '@mui/material'
import { styled } from '@mui/material/styles'

// No custom props → no shouldForwardProp needed
const PageContainer = styled(Box)(({ theme }) => ({
  minHeight: '100vh',
  padding: theme.spacing(4),
  backgroundColor: theme.palette.background.default,
  maxWidth: '1400px',
  margin: '0 auto',
}))

// Custom props → shouldForwardProp required
const StatusCard = styled(Paper, {
  shouldForwardProp: (prop) => prop !== 'isActive',
})<{ isActive?: boolean }>(({ theme, isActive }) => ({
  padding: theme.spacing(3),
  backgroundColor: isActive ? theme.palette.queen[100] : theme.palette.queen[200],
  borderRadius: theme.shape.borderRadius,
}))
```

---

## Figma → Token Mapping

When reading a Figma frame, translate values to theme tokens before writing code.

### Colors

| Figma value / label | Theme token |
|---|---|
| `#7F1BF6` / Primary violet | `theme.palette.primary.main` or `'primary.main'` |
| `#51138E` / Primary dark | `theme.palette.primary.dark` |
| `#EC407A` / Secondary pink | `theme.palette.secondary.main` or `'secondary.main'` |
| `#252327` / Text primary | `theme.palette.text.primary` or `'text.primary'` |
| `#7C7B7D` / Text secondary | `theme.palette.text.secondary` or `'text.secondary'` |
| `#ACABAD` / Text disabled | `theme.palette.text.disabled` |
| `#FFFFFB` / Background | `theme.palette.background.default` or `'background.default'` |
| `#EFEFF0` / Paper | `theme.palette.background.paper` or `'background.paper'` |
| `#FDFBFE` / Queen 0 | `theme.palette.queen[0]` |
| `#F5F1F8` / Queen 50 | `theme.palette.queen[50]` |
| `#F1E9F9` / Queen 100 | `theme.palette.queen[100]` |
| `#E9E2EF` / Queen 150 | `theme.palette.queen[150]` |
| `#E6DCF0` / Queen 200 | `theme.palette.queen[200]` |
| `#DED5E8` / Queen 300 | `theme.palette.queen[300]` |
| `#D4CBDE` / Queen 400 | `theme.palette.queen[400]` |
| `#EF5350` / Error | `theme.palette.error.main` |
| `#1D987C` / Success | `theme.palette.success.main` |
| `#5085EF` / Info | `theme.palette.info.main` |
| `#FFCA28` / Warning | `theme.palette.warning.main` |
| Alert info bg `#F5F0F9` | `theme.palette.alert.info` |
| Alert success bg `#E7FFFA` | `theme.palette.alert.success` |
| Alert warning bg `#FFFADE` | `theme.palette.alert.warning` |
| Alert error bg `#F9DAE6` | `theme.palette.alert.error` |

**Never hardcode a hex that appears in this table.**

### Typography

| Figma text style | MUI variant |
|---|---|
| Display / Hero large | `h1` (96px/300) |
| Hero | `h2` (60px/300) |
| Title large | `h3` (48px/400) |
| Title | `h4` (34px/500) |
| Section heading | `h5` (24px/600) |
| Card heading | `h6` (20px/600) |
| Label / Strong body | `subtitle1` (16px/600) |
| Small label | `subtitle2` (12px/600) |
| Medium small label | `subtitle3` (12px/500) |
| Body / Default text | `body1` (14px/400) |
| Small body | `body2` (12px/400) |
| Tiny body | `body3` (10px/400) |
| Button text large | `button` (14px/500) |
| Button text small | `button2` (12px/500) |
| Caption | `caption` (12px/400) |
| Chip label | `chipLabel` (13px/400) |

### Spacing

| Figma spacing value | spacing() call |
|---|---|
| 4px | `theme.spacing(1)` |
| 8px | `theme.spacing(2)` |
| 12px | `theme.spacing(3)` |
| 16px | `theme.spacing(4)` |
| 20px | `theme.spacing(5)` |
| 24px | `theme.spacing(6)` |
| 40px | `theme.spacing(7)` |
| 48px | `theme.spacing(8)` |

Values between scale steps (e.g. 6px, 10px): use pixel strings `gap: '6px'`.

### Figma components → ConnectUI

| Figma component name | Use |
|---|---|
| Switch / Toggle | `OrionSwitch` |
| Text input / Field | `OrionInput` (form) or `TextField` (uncontrolled) |
| Tab group / Segmented control | `OrionToggleButtonGroup` |
| Alert / Banner | `OrionAlert` |
| Toast / Notification | `OrionSnackbar` |
| Icon button | `OrionIconButton` |
| Button | `Button` from MUI (pill shape pre-applied via theme) |
| Chip / Tag | `Chip` from MUI (dark bg pre-applied via theme) |
| Card / Surface | `Paper` with elevation prop (elevation → queen palette) |
| Checkbox | `Checkbox` from MUI |
| Select / Dropdown | `Select` from MUI with `slotProps` |
| Dialog / Modal | `Dialog` from MUI (white bg pre-applied via theme) |
| Progress bar | `LinearProgress` from MUI (orion variant available) |
| Loading skeleton | `Skeleton` from MUI (queen variant available) |

---

## Analysis Checklist (run before planning)

When given a Figma link, before writing the plan:

1. Read every frame/component name in the Figma
2. For each element, identify the token (color → palette key, spacing → scale index)
3. Map each UI element to the decision tree above
4. Flag anything that requires a new Orion component
5. Flag any color/spacing that is NOT in the token tables (potential deviation)
6. Confirm import path for each component
