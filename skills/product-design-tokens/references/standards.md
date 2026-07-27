# Standards & platform contracts

The durable, currently-correct contracts this skill targets. When any of these conflicts with an
older habit (design.md-as-format, WCAG 3.0/APCA, plain "Material Design 3", pre-2025 HIG), the
contract below wins.

## Token format: W3C DTCG 2025.10 (STABLE)

- Canonical spec: **https://www.designtokens.org/tr/2025.10/**: the stable release. **Never**
  cite or implement `/tr/drafts/`; the draft explicitly forbids implementation.
- A **token** is any object with a `$value`. A **group** is an object without one; it may carry
  `$type` and `$description`, and its `$type` is **inherited** by descendant tokens.
- **Aliases** are `{group.token.path}` strings (dot-separated), e.g. `"{color.base.blue-600}"`.
  An alias resolves to the referenced token's value. No circular chains.
- Reserved dollar-keys: `$value`, `$type`, `$description`, `$extensions`, `$deprecated`.
- Value shapes used here:
  - `color` → the canonical DTCG 2025.10 form is the structured object
    `{ "colorSpace": "srgb", "components": [r,g,b] }` with components in `[0,1]` (an optional `hex`
    key may sit *inside* that object as a fallback). A bare top-level `#hex` string is **NOT** a
    conformant 2025.10 `$value`; this repo's `contrast.py` accepts one only as a convenience, and
    `dtcg_validate.py` does not check value shapes, so do not rely on it. Use **OKLCH for
    exploration** but export an sRGB/hex-compatible value so `contrast.py` and downstream tools can
    read it.
  - `dimension` → `{ "value": <number>, "unit": "px" | "rem" }` (only px/rem).
  - `fontFamily` → a string or an array of strings. `fontWeight` → a number `[1,1000]` or a
    named string (`"bold"` = 700).
- **DTCG JSON is ALWAYS the source of truth.** Any other artifact (DESIGN.md, Tailwind/CSS export)
  is derived from it.

## Optional design.md layer (ALPHA: probe, pin, never assume)

- Google Labs `design.md` (github.com/google-labs-code/design.md, Apache-2.0) is **alpha**; its
  authors warn the format **will change**. Support it only as an optional prose layer:
  1. **Probe the CLI at runtime** (`npx @google/design.md --version` or equivalent): never assume
     it is installed or that any subcommand name is stable.
  2. **Pin** the spec/CLI version you generated against (in the DESIGN.md frontmatter).
  3. **Always emit `tokens.dtcg.json` alongside**: DESIGN.md is never the sole durable record.
- Do not hardcode `lint/export --format …` subcommands as a stable contract; discover them from
  the probed CLI's help output.

## Accessibility: WCAG 2.2 AA (exclude 3.0 / APCA)

Target **WCAG 2.2 Level AA** (W3C Recommendation, Oct 2023; EU EAA / US DOJ backed). Do **not**
"upgrade" guidance to **WCAG 3.0** (unfinished Working Draft, no conformance model) or its
**APCA** contrast method; keep the 2.2 contrast ratios below.

Contrast (SC 1.4.3 / 1.4.11): normal text **≥ 4.5:1**, large text (≥24px, or ≥18.66px bold) and
UI components / graphical objects **≥ 3:1**. Never carry meaning by **colour alone** (SC 1.4.1).

The **9 success criteria new since WCAG 2.1** (2.2 also removed 4.1.1 Parsing): checklist them;
legacy 2.1-era checklists silently miss these, and the target-size and focus ones are token-relevant:

| SC | Name | Level | Token relevance |
|---|---|---|---|
| 2.4.11 | Focus Not Obscured (Minimum) | AA | focus-ring offset / sticky-header spacing tokens |
| 2.4.12 | Focus Not Obscured (Enhanced) | AAA |  |
| 2.4.13 | Focus Appearance | AAA | focus-ring width & contrast tokens |
| 2.5.7 | Dragging Movements | AA | provide a non-drag alternative |
| 2.5.8 | Target Size (Minimum) | AA | **min interactive target 24×24 CSS px** (`size.target-min`) |
| 3.2.6 | Consistent Help | A | help-affordance placement |
| 3.3.7 | Redundant Entry | A |  |
| 3.3.8 | Accessible Authentication (Minimum) | AA | no cognitive-function test to log in |
| 3.3.9 | Accessible Authentication (Enhanced) | AAA |  |

AA conformance requires meeting every **A and AA** criterion (including the A/AA rows above); the
three **AAA** rows are aspirational. Hand the full audit in context to **review-design**.

## Platform currency

- **Material 3 Expressive** (rolled out 2025–2026): motion tokens are **spring-based
  (stiffness / damping)**, not fixed duration+easing only; use the 35-new-shapes + shape-morph
  library; **Jetpack Compose** is the reference implementation (the View-based
  material-components-android library is in maintenance). Cite "Material 3 Expressive", not plain
  "Material Design 3".
- **Apple Liquid Glass** (WWDC25, OS-26 generation): the current material language, replacing
  pre-2025 flat/translucency guidance. Every translucent-surface recommendation carries a
  **MANDATORY WCAG 2.2 AA contrast check** against the content behind it (dynamic tint is a known
  contrast-failure risk).

## Component documentation: convention, not a schema

No settled machine-readable component-spec standard exists on par with DTCG. **DSDS**
(designsystemdocspec.org, ~v0.15.2 draft, single maintainer, self-described **unendorsed**) is an
emerging candidate only: do not present it as authoritative. Default component docs to
**convention**: purpose, props/states, a11y notes, usage examples, do/don't, versioning/changelog.

## Handoff: a live pipeline, not a one-shot document

Recommend the live pipeline for in-session work: **Figma Code Connect → Dev Mode MCP → AI editor →
human polish**, reconciled against the versioned `tokens.dtcg.json` as the durable source of truth,
not a one-time "handoff" export.
