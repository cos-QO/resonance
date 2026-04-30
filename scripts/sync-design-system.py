#!/usr/bin/env python3
"""
Sync ConnectUI design tokens and component catalogue from connect-ui.

Preferred: read from a local clone (--local-path).
Fallback:  fetch from GitHub (requires public repo or GITHUB_TOKEN env var).

Regenerates:
  .claude/memory/standards/connectui-design-system.md  — tokens, palette, components
  .claude/memory/standards/connectui-stack.md          — dependency versions (local only)

Usage:
  python3 scripts/sync-design-system.py --local-path /path/to/connect-ui
  python3 scripts/sync-design-system.py                           # GitHub fallback
  python3 scripts/sync-design-system.py --check --local-path ...  # staleness check
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO   = "queen-one/connect-ui"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

OUTPUT_PATH = Path(".claude/memory/standards/connectui-design-system.md")
STACK_PATH  = Path(".claude/memory/standards/connectui-stack.md")


# ── Source readers ────────────────────────────────────────────────────────────

def read_local(local_path: Path, rel: str) -> str:
    p = local_path / rel
    if p.exists():
        return p.read_text(encoding="utf-8")
    return ""


def fetch_github(rel: str) -> str:
    token = os.environ.get("GITHUB_TOKEN", "")
    req = urllib.request.Request(f"{BASE_URL}/{rel}")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode()
    except Exception as e:
        print(f"  WARNING: could not fetch {rel}: {e}", file=sys.stderr)
        return ""



# ── Token parsers ─────────────────────────────────────────────────────────────


def extract_spacing_array(theme_src: str) -> List[int]:
    """Parse `spacing: [0, 4, 8, ...]` from theme.ts — returns list of px values."""
    m = re.search(r'spacing:\s*\[([^\]]+)\]', theme_src)
    if not m:
        return []
    return [int(v.strip()) for v in m.group(1).split(",") if v.strip().isdigit()]


def extract_typography_variants(theme_src: str) -> List[Tuple[str, str, int]]:
    """Parse named typography variants — returns [(variant, fontSize, fontWeight), ...]."""
    results: List[Tuple[str, str, int]] = []
    current_variant = None
    current_size = None
    current_weight = None
    depth = 0
    in_typography = False

    for line in theme_src.splitlines():
        if re.search(r'\btypography\s*:\s*\{', line) and not in_typography:
            in_typography = True
            depth = 1
            continue
        if in_typography:
            depth += line.count('{') - line.count('}')
            if depth <= 0:
                break
            # New variant (e.g. "h1: {" or "body1: {")
            vm = re.match(r'\s+(h[1-6]|body[123]|subtitle[123]|button[12]?|caption|overline|chipLabel)\s*:\s*\{', line)
            if vm:
                if current_variant and current_size:
                    results.append((current_variant, current_size, current_weight or 400))
                current_variant = vm.group(1)
                current_size = None
                current_weight = None
            sz = re.search(r'fontSize:\s*["\']([0-9.]+px)["\']', line)
            if sz and current_variant:
                current_size = sz.group(1)
            wt = re.search(r'fontWeight:\s*(\d+)', line)
            if wt and current_variant:
                current_weight = int(wt.group(1))

    if current_variant and current_size:
        results.append((current_variant, current_size, current_weight or 400))
    return results


def extract_queen_palette(theme_src: str) -> Dict[str, str]:
    """Pull the queen: { n: '#hex', ... } value block from theme.ts.

    Skips TypeScript interface/declare blocks (which also contain `queen: {`)
    and targets the actual palette values inside createTheme().
    """
    palette: Dict[str, str] = {}
    in_queen = False
    in_ts_decl = False
    depth = 0

    for line in theme_src.splitlines():
        # Track when we're inside a TypeScript declaration block
        if re.search(r'\b(interface|declare)\b', line):
            in_ts_decl = True
        if in_ts_decl:
            depth += line.count('{') - line.count('}')
            if depth <= 0:
                in_ts_decl = False
                depth = 0
            continue

        if re.search(r'\bqueen\s*:\s*\{', line) and not in_queen:
            in_queen = True
            depth = 1
            continue

        if in_queen:
            depth += line.count('{') - line.count('}')
            if depth <= 0:
                break
            m = re.match(r'\s+(\w+)\s*:\s*"(#[0-9A-Fa-f]{6})"', line)
            if m:
                palette[m.group(1)] = m.group(2)
    return palette


def scan_components(local_path: Path) -> Dict[str, List[str]]:
    """Scan src/components/ for Orion components and a broader component list."""
    result: Dict[str, List[str]] = {"orion": [], "shared": []}
    components_dir = local_path / "src" / "components"
    if not components_dir.exists():
        return result

    for entry in sorted(components_dir.iterdir()):
        name = entry.name
        if name.startswith("."):
            continue
        if name.startswith("Orion"):
            if entry.is_dir():
                # Expand subdirectory (e.g. OrionComponents/)
                for child in sorted(entry.iterdir()):
                    if child.suffix == ".tsx" and child.stem.startswith("Orion"):
                        result["orion"].append(child.stem)
            else:
                result["orion"].append(name.replace(".tsx", ""))
        else:
            result["shared"].append(name.replace(".tsx", "") if name.endswith(".tsx") else name)
    return result


def read_package_versions(local_path: Path) -> Dict[str, str]:
    """Extract key dependency versions from package.json."""
    pkg = local_path / "package.json"
    if not pkg.exists():
        return {}
    try:
        data = json.loads(pkg.read_text())
        all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        keys = [
            "react", "@mui/material", "@tanstack/react-router",
            "@tanstack/react-query", "@tanstack/react-form",
            "zustand", "firebase", "typescript", "vite",
            "@storybook/react-vite",
        ]
        return {k: all_deps[k] for k in keys if k in all_deps}
    except Exception:
        return {}


# ── Document generators ───────────────────────────────────────────────────────

def generate_design_system_md(
    queen_palette: Dict,
    spacing: List,
    typo_variants: List,
    components: Dict,
    local_path: Optional[Path],
) -> str:
    today = date.today().isoformat()
    source_note = f"local clone at `{local_path}`" if local_path else f"{REPO} on GitHub"

    lines = [
        "# ConnectUI Design System Reference",
        "",
        f"**Source**: {source_note}",
        f"**Last Updated**: {today}",
        "**Stack**: React + MUI v7 + Queen One design system",
        "",
        "---",
        "",
        "## Component Structure",
        "",
        "Components live in `src/components/`. Orion components are Queen-custom styled wrappers.",
        "",
    ]

    if components.get("orion"):
        lines += [
            "### Orion Components (Queen custom — check before building new ones)",
            "| Component |",
            "|-----------|",
        ]
        for c in components["orion"]:
            name = c.replace(".tsx", "")
            lines.append(f"| `{name}` |")

    lines += [
        "",
        "---",
        "",
        "## Color Palette",
        "",
        "**Never hardcode hex values** — always reference theme palette tokens.",
        "",
    ]

    if queen_palette:
        lines += [
            "### Queen Palette (`theme.palette.queen[N]`)",
            "| Scale | Hex |",
            "|-------|-----|",
        ]
        for scale, hex_ in sorted(queen_palette.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
            lines.append(f"| {scale} | `{hex_}` |")

    lines += [
        "",
        "### Standard Palette References",
        "- `theme.palette.primary.main` — `#7F1BF6` (Queen violet)",
        "- `theme.palette.secondary.main` — `#EC407A` (Queen pink)",
        "- `theme.palette.text.primary` — `#252327`",
        "- `theme.palette.text.secondary` — `#7C7B7D`",
        "- `theme.palette.background.default` — `#FFFFFB`",
        "- `theme.palette.alert.info/success/warning/error`",
    ]

    lines += [
        "",
        "---",
        "",
        "## Typography",
        "",
        "- **Primary font**: Poppins",
        "- **Font family string**: `Poppins, Arial, sans-serif`",
        "",
    ]

    if typo_variants:
        lines += ["### Variants", "| Variant | Size | Weight |", "|---------|------|--------|"]
        for variant, size, weight in typo_variants:
            lines.append(f"| `{variant}` | {size} | {weight} |")

    if spacing:
        lines += [
            "",
            "---",
            "",
            "## Spacing Scale",
            "",
            "**CRITICAL**: ConnectUI uses a CUSTOM spacing scale — NOT `n * 8px`.",
            "Use integer index `n` in `sx` props (e.g. `mt: 2` = 8px, `mt: 3` = 12px).",
            "",
            "| Index (n) | px |",
            "|-----------|-----|",
        ]
        for i, px in enumerate(spacing):
            lines.append(f"| {i} | {px}px |")
        lines.append("")
        lines.append("For values outside this scale: use pixel strings (`gap: '6px'`).")

    lines += [
        "",
        "---",
        "",
        "## Key Conventions",
        "",
        "- **No barrel imports** — direct file imports: `import { X } from './X/X'`, never from `index`",
        "- **Integer spacing only** — no decimals in `m`, `p`, `borderRadius` sx props",
        "- **shouldForwardProp** required on all styled components with custom props",
        "- **Never hardcode hex** — reference theme palette tokens (`theme.palette.queen[400]` etc.)",
        "- **MUI v7** — use `slotProps` (not deprecated `InputProps`, `MenuProps`)",
        "- **pnpm only** — never npm or yarn",
        "- **Strict TypeScript** — no `any`, explicit return types on exported functions",
        "- **Feature flags**: `VITE_FF_*` prefix, access via `import.meta.env.VITE_FF_*`",
        "",
        "---",
        "",
        "## Storybook Patterns",
        "",
        "Every new component needs a `.stories.tsx` file with:",
        "- `STORYBOOK_PROPS` as `const` tuple",
        "- `tags: ['autodocs']` in meta",
        "- Orion story title: `\"Orion Components/Orion [Name]\"`",
        "- Up to 5 sub-stories based on real usage in the repo",
    ]

    return "\n".join(lines) + "\n"


def generate_stack_md(versions: Dict) -> str:
    """Update the stack doc with exact pinned dependency versions."""
    today = date.today().isoformat()
    lines = [
        "# ConnectUI Technology Stack",
        "",
        f"**Last Updated**: {today}",
        "**Source**: `package.json` (auto-synced)",
        "",
        "---",
        "",
        "## Core Dependencies (pinned versions)",
        "",
        "| Package | Version |",
        "|---------|---------|",
    ]
    for pkg, ver in sorted(versions.items()):
        lines.append(f"| `{pkg}` | `{ver}` |")

    lines += [
        "",
        "---",
        "",
        "## Architecture",
        "",
        "| Layer | Technology |",
        "|-------|-----------|",
        "| Language | TypeScript strict (no `any`) |",
        "| Runtime | Node 20+ |",
        "| Package manager | **pnpm only** (never npm/yarn) |",
        "| Bundler | Vite |",
        "| UI | React + MUI v7 + Queen One design system |",
        "| Routing | TanStack Router v1 (file-based, `src/routes/`) |",
        "| Server state | TanStack Query v5 |",
        "| Form state | TanStack Form v1 + Zod |",
        "| Client state | Zustand + Immer |",
        "| Backend | Firebase (Auth, Firestore, Storage) |",
        "| Tests | Vitest + Playwright |",
        "| Components | Storybook |",
        "",
        "## State Hierarchy (use in this order)",
        "",
        "1. **React Query** — server state (`useQuery`, `useMutation`)",
        "2. **React Query cache** — derived global client state",
        "3. **useState / useReducer** — component-local state",
        "4. **TanStack Form** — form state (with Zod validation)",
        "5. **Zustand** — cross-component client state",
        "",
        "## Project Structure",
        "",
        "```",
        "src/",
        "  components/     shared + Orion components",
        "  features/       feature-scoped code (components, hooks, queries)",
        "  hooks/          shared/generic hooks only",
        "  routes/         TanStack Router file-based routes",
        "  routeTree.gen.ts  AUTO-GENERATED — never edit",
        "  theme.ts        MUI theme override (authoritative design tokens)",
        "  stories/        cross-feature Storybook stories",
        "```",
        "",
        "## Anti-patterns",
        "",
        "- No Context API for server state (React Query handles this)",
        "- No prop drilling beyond 2 levels",
        "- No Redux",
        "- No `routeTree.gen.ts` edits",
        "- No barrel imports (`index.ts` re-exports)",
    ]
    return "\n".join(lines) + "\n"


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-path", help="absolute path to local connect-ui repo")
    parser.add_argument("--check", action="store_true", help="exit 1 if stale, no write")
    args = parser.parse_args()

    local_path = Path(args.local_path).resolve() if args.local_path else None

    if local_path:
        print(f"Reading from local path: {local_path}")
    else:
        print(f"Fetching from GitHub: {REPO}")

    # All design tokens live in src/theme.ts
    theme_src = ""
    if local_path:
        theme_src = read_local(local_path, "src/theme.ts")
    if not theme_src:
        theme_src = fetch_github("src/theme.ts")
    if not theme_src:
        print("ERROR: could not read src/theme.ts from local path or GitHub", file=sys.stderr)
        return 1

    # Parse tokens from theme.ts
    queen_palette  = extract_queen_palette(theme_src)
    spacing        = extract_spacing_array(theme_src)
    typo_variants  = extract_typography_variants(theme_src)

    # Scan components (local only)
    components: Dict[str, List[str]] = {"orion": [], "shared": []}
    if local_path:
        components = scan_components(local_path)

    # Read package versions (local only)
    versions: Dict[str, str] = {}
    if local_path:
        versions = read_package_versions(local_path)

    new_design_md = generate_design_system_md(
        queen_palette, spacing, typo_variants, components, local_path
    )

    def _strip_date(s: str) -> str:
        return re.sub(r"\*\*Last Updated\*\*:.*", "", s)

    if args.check:
        stale = False
        if OUTPUT_PATH.exists():
            if _strip_date(OUTPUT_PATH.read_text()) != _strip_date(new_design_md):
                stale = True
                print("connectui-design-system.md is stale", file=sys.stderr)
            else:
                print("connectui-design-system.md is up to date")
        else:
            stale = True
            print("connectui-design-system.md is missing", file=sys.stderr)
        return 1 if stale else 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(new_design_md)
    print(f"Updated: {OUTPUT_PATH}")

    if versions:
        new_stack_md = generate_stack_md(versions)
        STACK_PATH.write_text(new_stack_md)
        print(f"Updated: {STACK_PATH}")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
