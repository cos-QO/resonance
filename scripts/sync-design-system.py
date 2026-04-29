#!/usr/bin/env python3
"""
Sync ConnectUI design tokens from queen-one/connect-ui on GitHub.

Fetches the design token source files and regenerates:
  .claude/memory/standards/connectui-design-system.md

Run manually or on a schedule to keep agent context current.

Usage:
  python3 scripts/sync-design-system.py
  python3 scripts/sync-design-system.py --check   # exit 1 if stale, no write
"""
import argparse
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

REPO = "queen-one/connect-ui"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/src/design-tokens"

TOKEN_FILES = [
    "material-colors.ts",
    "palette.ts",
    "typography.ts",
    "spacing.ts",
    "shape.ts",
]

OUTPUT_PATH = Path(".claude/memory/standards/connectui-design-system.md")
STACK_PATH  = Path(".claude/memory/standards/connectui-stack.md")


def fetch(filename: str) -> str:
    url = f"{BASE_URL}/{filename}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.read().decode()
    except Exception as e:
        print(f"  WARNING: could not fetch {filename}: {e}", file=sys.stderr)
        return ""


def extract_hex_colors(material_colors_src: str) -> dict[str, dict[str, str]]:
    """Parse materialColors object from TypeScript source."""
    colors: dict[str, dict[str, str]] = {}
    current_key = None
    for line in material_colors_src.splitlines():
        key_match = re.match(r"\s+(\w+):\s*\{", line)
        if key_match:
            current_key = key_match.group(1)
            colors[current_key] = {}
        hex_match = re.match(r"\s+(\d+):\s*[\"'](#[0-9A-Fa-f]{6})[\"']", line)
        if hex_match and current_key:
            colors[current_key][hex_match.group(1)] = hex_match.group(2)
    return colors


def extract_spacing(spacing_src: str) -> list[tuple[int, int]]:
    """Parse spacing scale from TypeScript source."""
    pairs = []
    for line in spacing_src.splitlines():
        m = re.match(r"\s+(\d+):\s*(\d+),", line)
        if m:
            pairs.append((int(m.group(1)), int(m.group(2))))
    return pairs


def extract_shape(shape_src: str) -> list[tuple[str, int]]:
    """Parse border radius tokens."""
    pairs = []
    for line in shape_src.splitlines():
        m = re.match(r"\s+(\w+):\s*(\d+),", line)
        if m:
            pairs.append((m.group(1), int(m.group(2))))
    return pairs


def extract_typography(typo_src: str) -> dict:
    """Parse typography tokens."""
    result: dict = {"fontFamily": "Poppins", "weights": [], "sizes": []}
    for line in typo_src.splitlines():
        ff = re.search(r'fontFamily:\s*["\'](\w+)["\']', line)
        if ff:
            result["fontFamily"] = ff.group(1)
        wm = re.match(r'\s+(\w+):\s*(\d+),', line)
        if wm and "weight" in wm.group(1).lower():
            result["weights"].append((wm.group(1), int(wm.group(2))))
        sz = re.match(r'\s+"([0-9.]+rem)":\s*(\d+),', line)
        if sz:
            result["sizes"].append((sz.group(1), int(sz.group(2))))
    return result


def generate_md(colors: dict, spacing: list, shape: list, typo: dict) -> str:
    today = date.today().isoformat()
    v = colors.get("violet", {})
    p = colors.get("pink", {})
    o = colors.get("onyx", {})

    lines = [
        "# ConnectUI Design System Reference",
        "",
        f"**Source**: {REPO} (auto-synced from design tokens)",
        f"**Last Updated**: {today}",
        "**Stack**: React + MUI v7 + Queen One Orion Design System",
        "",
        "---",
        "",
        "## Color Palette",
        "",
        "Always use theme palette tokens — never hardcode hex values.",
        "",
        "### Brand Colors",
        "| Color | Scale | Hex |",
        "|-------|-------|-----|",
    ]

    for scale, hex_ in sorted(v.items(), key=lambda x: int(x[0])):
        suffix = ""
        if scale == "400":
            suffix = " ← **primary.main**"
        elif scale == "600":
            suffix = " ← primary.dark"
        lines.append(f"| violet | [{scale}] | `{hex_}`{suffix} |")

    for scale, hex_ in sorted(p.items(), key=lambda x: int(x[0])):
        suffix = " ← **secondary.main**" if scale == "400" else ""
        lines.append(f"| pink | [{scale}] | `{hex_}`{suffix} |")

    for scale, hex_ in sorted(o.items(), key=lambda x: int(x[0])):
        suffix = ""
        if scale == "50":
            suffix = " ← white / contrastText"
        elif scale == "600":
            suffix = " ← text.primary"
        lines.append(f"| onyx | [{scale}] | `{hex_}`{suffix} |")

    primary_main = v.get("400", "#7700EE")
    secondary_main = p.get("400", "#EC407A")
    white = o.get("50", "#FFFFFF")
    text_primary = o.get("600", "#252327")

    lines += [
        "",
        "### Semantic Palette",
        "| Token | Hex |",
        "|-------|-----|",
        f"| `primary.main` | `{primary_main}` |",
        f"| `secondary.main` | `{secondary_main}` |",
        f"| `text.primary` | `{text_primary}` |",
        f"| `text.contrastText` | `{white}` |",
        "",
        "---",
        "",
        "## Typography",
        "",
        f"- **Primary font**: {typo.get('fontFamily', 'Poppins')} (body, inputs, all text)",
        "- **Secondary font**: Cabinet Grotesk (labels, some headings)",
        "- **Base size**: 16px (1rem)",
        "",
        "### Font Weights",
        "| Name | Value |",
        "|------|-------|",
    ]

    for name, val in typo.get("weights", []):
        lines.append(f"| {name} | {val} |")

    lines += [
        "",
        "### Font Sizes",
        "| rem | px |",
        "|-----|----|",
    ]
    for rem, px in typo.get("sizes", []):
        lines.append(f"| {rem} | {px}px |")

    lines += [
        "",
        "---",
        "",
        "## Spacing Scale",
        "",
        "**CRITICAL**: ConnectUI uses a CUSTOM spacing scale. `theme.spacing(n)` does NOT equal `n * 8px`.",
        "Use integer values only — never decimals.",
        "",
        "| n | px |",
        "|---|----|",
    ]
    for n, px in spacing:
        lines.append(f"| {n} | {px}px |")

    lines += [
        "",
        "For spacing not in this scale: use `gap`, `rowGap`, `columnGap` with pixel strings (e.g. `gap: '6px'`).",
        "",
        "---",
        "",
        "## Shape (Border Radius)",
        "",
        "| Name | px |",
        "|------|----|",
    ]
    for name, px in shape:
        lines.append(f"| {name} | {px}px |")

    lines += [
        "",
        "---",
        "",
        "## Orion Components",
        "",
        "Custom styled components in `src/orion/OrionComponents/`. Always check these before building new ones.",
        "",
        "| Component | Purpose |",
        "|-----------|---------|",
        "| `OrionBorderCard` | Card with border styling |",
        "| `OrionIconButton` | Icon-only button |",
        "| `OrionInput` | Form text input with TanStack Form integration |",
        "| `OrionPageHeader` | Page title + breadcrumb + description + actions |",
        "| `OrionPopoverMenu` | Popover/dropdown menu |",
        "| `OrionSnackbar` | Toast notification |",
        "| `OrionSwitch` | Toggle switch |",
        "| `OrionToggleButtonGroup` | Multi-option toggle |",
        "",
        "## MUI Components (re-exports)",
        "",
        "`src/orion/MuiComponents/` — exported as const, no function wrappers.",
        "Import directly: `import { MuiButton } from '../MuiComponents/MuiButton'`",
        "",
        "---",
        "",
        "## Key Conventions",
        "",
        "- **No barrel imports** — direct file imports only",
        "- **Integer spacing only** — no decimals in sx spacing props",
        "- **shouldForwardProp** required on styled components with custom props",
        "- **Cabinet Grotesk** for labels; **Poppins** for body/inputs",
        "- **Never hardcode hex** — reference theme palette tokens",
        "- **MUI v7** — use `slotProps` instead of deprecated `InputProps` etc.",
        "",
        "---",
        "",
        "## Storybook Patterns",
        "",
        "Every new component needs a `.stories.tsx` with:",
        "- `STORYBOOK_PROPS` as `const` tuple",
        "- `tags: ['autodocs']` in meta",
        '- MUI title: `"MUI Components/Mui [Name]"`',
        '- Orion title: `"Orion Components/Orion [Name]"`',
        "- Up to 5 sub-stories based on real repo usage",
    ]

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="check for staleness only")
    args = parser.parse_args()

    print("Fetching ConnectUI design tokens from GitHub...")
    sources = {f: fetch(f) for f in TOKEN_FILES}

    if all(not v for v in sources.values()):
        print("ERROR: all fetches failed — check network / repo access", file=sys.stderr)
        return 1

    colors = extract_hex_colors(sources.get("material-colors.ts", ""))
    spacing = extract_spacing(sources.get("spacing.ts", ""))
    shape = extract_shape(sources.get("shape.ts", ""))
    typo_src = sources.get("typography.ts", "")
    typo: dict = {"fontFamily": "Poppins", "weights": [], "sizes": []}
    for line in typo_src.splitlines():
        wm = re.match(r'\s+(\w+):\s*(\d+),', line)
        if wm:
            name = wm.group(1)
            val = int(wm.group(2))
            if any(w in name.lower() for w in ("light", "regular", "medium", "semibold", "bold")):
                typo["weights"].append((name, val))
        sz = re.match(r'\s+"([0-9.]+rem)":\s*(\d+),', line)
        if sz:
            typo["sizes"].append((sz.group(1), int(sz.group(2))))

    new_content = generate_md(colors, spacing, shape, typo)

    if args.check:
        if OUTPUT_PATH.exists():
            existing = OUTPUT_PATH.read_text()
            # Compare everything except the date line
            def strip_date(s: str) -> str:
                return re.sub(r"\*\*Last Updated\*\*:.*", "", s)
            if strip_date(existing) == strip_date(new_content):
                print("Design system reference is up to date.")
                return 0
        print("Design system reference is stale or missing.", file=sys.stderr)
        return 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(new_content)
    print(f"Updated: {OUTPUT_PATH}")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
