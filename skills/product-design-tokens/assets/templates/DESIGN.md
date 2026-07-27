---
# OPTIONAL alpha prose layer for the token system.
# Google Labs design.md format: github.com/google-labs-code/design.md (Apache-2.0).
design_md_spec_version: "alpha"        # PIN the exact version you generated against.
canonical_source: "./tokens.dtcg.json" # DTCG JSON is the source of truth; this file is derived.
generated_by: "product-design-tokens"
---

> ⚠️ **ALPHA: the format WILL change.** The Google Labs `design.md` spec is self-described
> as alpha with no stability guarantee. Treat `tokens.dtcg.json` (W3C DTCG 2025.10) as the
> canonical, durable source; regenerate this file when the pinned spec version changes. Never
> let this prose be the only record of a token: every value here must exist in the DTCG JSON.

# {{Product}}: Design language

## Foundation

Brief prose describing the intent behind the system: the brand feeling, the base grid, the
type scale rationale. Values are illustrative: the authoritative numbers live in the DTCG file.

- **Colour:** primary `{color.semantic.primary}`, surfaces `{color.semantic.bg-default}` /
  `{color.semantic.surface-muted}`, text `{color.semantic.text-default}` /
  `{color.semantic.text-muted}`. Status roles (`status-error`, `status-success`) are **never**
  conveyed by colour alone (WCAG 1.4.1): always paired with an icon or label.
- **Spacing:** 4px base scale (`space.1` … `space.8`).
- **Radius:** `radius.sm` / `radius.md` / `radius.full`.
- **Type:** `font.family.sans`, weights `regular` / `semibold`, sizes `body` / `h1`.

## Themes / modes

Describe light/dark (and high-contrast if present) as overrides of the semantic layer, not new
primitives. Each mode MUST keep every rendered foreground/background pair at WCAG 2.2 AA: see
`contrast-report.md`.

## Motion (if applicable)

Prefer **Material 3 Expressive** spring semantics (stiffness / damping), not fixed
duration+easing only; Jetpack Compose is the reference implementation. For Apple surfaces using
the **Liquid Glass** translucent material, pair every translucent surface with an explicit
contrast check against the content behind it.

## Provenance

- DTCG export: `./tokens.dtcg.json` (pinned to https://www.designtokens.org/tr/2025.10/)
- Contrast report: `./contrast-report.md`
- Reused design system (if any): {{shadcn | Tailwind | MUI | native | none (greenfield)}}
