# ConnectUI Design System Reference

**Source**: local clone at `/Users/cos/Documents/Projects/QueenOne/ConnectUI/connect-ui-main`
**Last Updated**: 2026-04-30
**Stack**: React + MUI v7 + Queen One design system

---

## Component Structure

Components live in `src/components/`. Orion components are Queen-custom styled wrappers.

### Orion Components (Queen custom — check before building new ones)
| Component |
|-----------|
| `OrionAlert` |
| `OrionAnimatedIconButton` |
| `OrionInput` |
| `OrionSnackbar` |
| `OrionSwitch` |
| `OrionToggleButtonGroup` |
| `OrionIconButton` |
| `OrionCampaignIcon` |
| `OrionCartIcon` |
| `OrionClickIcon` |
| `OrionClockIcon` |
| `OrionCodeEditorIcon` |
| `OrionCodeIcon` |
| `OrionDeleteIcon` |
| `OrionDollarIcon` |
| `OrionDragHandleIcon` |
| `OrionEditIcon` |
| `OrionEmailIcon` |
| `OrionEmojiEmotionsIcon` |
| `OrionLaptopIcon` |
| `OrionOpenMailIcon` |
| `OrionOutlineIcon` |
| `OrionPencilIcon` |
| `OrionPeopleIcon` |
| `OrionRedoIcon` |
| `OrionSearchIcon` |
| `OrionSendIcon` |
| `OrionSendInstantIcon` |
| `OrionSmartphoneIcon` |
| `OrionSmsIcon` |
| `OrionTrendingDownIcon` |
| `OrionTrendingUpIcon` |
| `OrionUndoIcon` |
| `OrionUploadIcon` |
| `OrionVisibilityIcon` |
| `OrionWalletIcon` |
| `OrionWarningIcon` |

---

## Color Palette

**Never hardcode hex values** — always reference theme palette tokens.

### Queen Palette (`theme.palette.queen[N]`)
| Scale | Hex |
|-------|-----|
| 0 | `#FDFBFE` |
| 50 | `#F5F1F8` |
| 100 | `#F1E9F9` |
| 150 | `#E9E2EF` |
| 200 | `#E6DCF0` |
| 300 | `#DED5E8` |
| 400 | `#D4CBDE` |
| 500 | `#CBC1D6` |
| 600 | `#BFB5CB` |
| 700 | `#B9AFC4` |
| 800 | `#B1A6BF` |
| 900 | `#ABA0B8` |
| 1000 | `#A398B0` |
| 1100 | `#ABA0B8` |
| 1200 | `#9484A2` |

### Standard Palette References
- `theme.palette.primary.main` — `#7F1BF6` (Queen violet)
- `theme.palette.secondary.main` — `#EC407A` (Queen pink)
- `theme.palette.text.primary` — `#252327`
- `theme.palette.text.secondary` — `#7C7B7D`
- `theme.palette.background.default` — `#FFFFFB`
- `theme.palette.alert.info/success/warning/error`

---

## Typography

- **Primary font**: Poppins
- **Font family string**: `Poppins, Arial, sans-serif`

### Variants
| Variant | Size | Weight |
|---------|------|--------|
| `h1` | 96px | 300 |
| `h2` | 60px | 300 |
| `h3` | 48px | 400 |
| `h4` | 34px | 500 |
| `h5` | 24px | 600 |
| `h6` | 20px | 600 |
| `subtitle1` | 16px | 600 |
| `subtitle2` | 12px | 600 |
| `subtitle3` | 12px | 500 |
| `body1` | 14px | 400 |
| `body2` | 12px | 400 |
| `body3` | 10px | 400 |
| `button` | 14px | 500 |
| `button2` | 12px | 500 |
| `caption` | 12px | 400 |
| `overline` | 12px | 400 |
| `chipLabel` | 13px | 400 |

---

## Spacing Scale

**CRITICAL**: ConnectUI uses a CUSTOM spacing scale — NOT `n * 8px`.
Use integer index `n` in `sx` props (e.g. `mt: 2` = 8px, `mt: 3` = 12px).

| Index (n) | px |
|-----------|-----|
| 0 | 0px |
| 1 | 4px |
| 2 | 8px |
| 3 | 12px |
| 4 | 16px |
| 5 | 20px |
| 6 | 24px |
| 7 | 40px |
| 8 | 48px |
| 9 | 56px |
| 10 | 64px |
| 11 | 80px |
| 12 | 88px |
| 13 | 104px |
| 14 | 120px |

For values outside this scale: use pixel strings (`gap: '6px'`).

---

## Key Conventions

- **No barrel imports** — direct file imports: `import { X } from './X/X'`, never from `index`
- **Integer spacing only** — no decimals in `m`, `p`, `borderRadius` sx props
- **shouldForwardProp** required on all styled components with custom props
- **Never hardcode hex** — reference theme palette tokens (`theme.palette.queen[400]` etc.)
- **MUI v7** — use `slotProps` (not deprecated `InputProps`, `MenuProps`)
- **pnpm only** — never npm or yarn
- **Strict TypeScript** — no `any`, explicit return types on exported functions
- **Feature flags**: `VITE_FF_*` prefix, access via `import.meta.env.VITE_FF_*`

---

## Storybook Patterns

Every new component needs a `.stories.tsx` file with:
- `STORYBOOK_PROPS` as `const` tuple
- `tags: ['autodocs']` in meta
- Orion story title: `"Orion Components/Orion [Name]"`
- Up to 5 sub-stories based on real usage in the repo
