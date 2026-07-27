---
name: product-design-tokens
description: >-
  Authors a durable design-token contract: a W3C DTCG 2025.10 JSON file
  ($value/$type, {group.token.path} aliases) as the canonical source, adopting
  the project's existing design system first and enforcing WCAG 2.2 AA contrast
  (never meaning by colour alone). An optional Google-Labs DESIGN.md alpha layer
  is version-pinned, runtime-probed, and always paired with the DTCG JSON. Use
  for "define our design tokens", "create a DTCG token file", or "set up our
  colour palette with contrast checks". Not for the screen structure (use
  product-design-spec), a UX/accessibility critique (use review-design), or
  generating logo/hero art (use codex-imagegen). Writes no application code.
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: true
argument-hint: "<idea | repo path | existing tokens/config> [--with-design-md]"
context: fork
agent: general-purpose
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(git *), Bash(gh *), Bash(python *), Bash(uv run *), Bash(npx *), Task, WebSearch, WebFetch, Skill
---

# Product Design Tokens

Produce the *token contract* a themed UI is built from: a valid, WCAG-checked **DTCG 2025.10 JSON
file** that stays the single source of truth. This skill **writes no application code** and never
draws assets; it authors and validates the tokens. Output lands under `docs/specs/design/tokens/`.

## Input

$ARGUMENTS

Read the source first: an existing repo (scan for a design system before anything else), a design
spec / screen inventory from `product-design-spec`, a brand brief, or a plain idea. `--with-design-md`
also emits the optional alpha DESIGN.md prose layer.

## Prerequisites & fallback

Sibling skills are invoked via the `Skill` tool where available; **with no `Skill` tool, apply the
named sibling's documented rules inline** (each delegation below states the fallback in-sentence).
Design-system detection uses the `Task` tool with an `Explore`/haiku subagent; **no `Task` tool?**
Run the detection inline, sequentially, with Grep/Glob/Read. The optional `@google/design.md` CLI is
**probed at runtime, never assumed**: the DTCG JSON is emitted whether or not it runs.

## Lean by default

**Default to a single `docs/specs/design/tokens/tokens.dtcg.json`.** Split a layer (semantic,
component) into its own file only when it outgrows the single file. `contrast-report.md` sits
alongside it; DESIGN.md only when asked.

- **Cost stop-condition:** if the request implies a large tree (multi-brand × multi-theme ×
  per-component tokens for dozens of components), **stop and ask** before emitting it: scope it
  down or confirm the tree first. Never auto-generate a 30-file token set.

## Reuse first (top of the ladder)

Inventing a brand from scratch is the **last resort, greenfield-only**. Before writing any token:

1. **Detect an existing design system**: scan for `tailwind.config.*`, shadcn (`components.json`,
   `@/components/ui`), MUI theme, CSS custom properties, or a native platform system.
2. **Adopt / extend it**: express the existing values as DTCG tokens (alias into them; add only
   what the change needs). Do not replace a working system with a new invented palette.
3. Only with genuinely no system present do you seed a new core palette.

State which path you took in one line.

## Workflow

Four phases: **Detect → Draft → Validate → Hand off.**

### Phase: Detect

Scan the repo for an existing design system (spawn an `Explore`/haiku agent, or do it inline):

```
Task (Explore, haiku): "Find this repo's design system: tailwind.config.*, components.json / shadcn
ui dir, MUI theme, CSS custom properties (:root { --... }), or a native platform system. Return the
tool, the token values found (colour/spacing/radius/type), and the file paths, invent nothing."
```

Decide **reuse vs. greenfield** from what you find. If a spec from `product-design-spec` is present,
read its screen inventory so the semantic tokens cover what the screens actually render.

### Phase: Draft

Create the single canonical file from the skeleton and fill it:

```bash
cp skills/product-design-tokens/assets/templates/tokens.dtcg.json docs/specs/design/tokens/tokens.dtcg.json
```

- **DTCG 2025.10 shape** (full detail: `references/standards.md`): a token is any object with a
  `$value`; groups carry an inheritable `$type`; aliases are `{group.token.path}`. Pin to
  **https://www.designtokens.org/tr/2025.10/**: **never `/tr/drafts/`**.
- **Layer the colours:** a primitive `base` palette, then a `semantic` layer that aliases it
  (UI consumes semantic). OKLCH is fine for *exploration*, but export an sRGB/hex-compatible value.
- **Status colours are never colour-alone** (WCAG 1.4.1): annotate each to pair with an icon/label.
- **Brand art that informs the palette** goes to `codex-imagegen` (produce the prompt; don't draw
  the asset here: via the `Skill` tool where available, else write the prompt for the user to run).
- **DESIGN.md is optional and derived.** Only with `--with-design-md`: probe the CLI at runtime,
  pin the alpha version in its frontmatter, add the ALPHA banner, and **always** keep
  `tokens.dtcg.json` alongside as canonical (template: `assets/templates/DESIGN.md`).
- **Platform tokens:** motion → **Material 3 Expressive** spring (stiffness/damping), not fixed
  duration+easing; translucency → **Apple Liquid Glass** with a mandatory contrast check. See
  `references/standards.md`.

### Phase: Validate

```bash
python skills/product-design-tokens/scripts/dtcg_validate.py --tokens docs/specs/design/tokens/tokens.dtcg.json
python skills/product-design-tokens/scripts/contrast.py       --tokens docs/specs/design/tokens/tokens.dtcg.json
```

- `dtcg_validate.py` must print **VALID** (every token has a resolvable `$type`, every alias
  resolves, no cycles). Fix any error before proceeding.
- `contrast.py` writes the contrast table: **0 failing pairs is the gate.** A pair below its AA
  threshold is a **blocker**: darken/lighten a token and re-run; never approve a failing or a
  colour-alone palette. Save its output to `docs/specs/design/tokens/contrast-report.md`.
- **In-context accessibility sign-off** (the palette rendered in real screens) goes to
  `review-design` for the WCAG 2.2 AA audit (via the `Skill` tool where available, otherwise apply
  its WCAG 2.2 AA checklist, the 9 criteria new since 2.1 in `references/standards.md`, inline).

### Phase: Hand off

- State the single readiness verdict: DTCG **VALID**, contrast **0 failures**, reuse-vs-greenfield
  path, and whether a DESIGN.md/alpha layer was produced.
- Report the written path(s). Recommend the **live pipeline** (Figma Code Connect → Dev Mode MCP →
  AI editor → human polish) reconciled against the versioned `tokens.dtcg.json`, not a one-shot
  handoff export. Name the downstream consumer: `implement-feature` builds the themed UI from these.

## Anti-hallucination

- **Reuse before invent:** scan for an existing design system before proposing any new brand token.
- Pin DTCG to **`/tr/2025.10/`**, never `/tr/drafts/`; the DTCG JSON is **always** the canonical
  source: DESIGN.md is never the sole record.
- Never invent colour-psychology claims or approve a palette that fails contrast or carries meaning
  by colour alone. Run `contrast.py` before declaring done.
- Target **WCAG 2.2 AA** explicitly; do **not** introduce WCAG 3.0 / APCA.
- The `@google/design.md` CLI and its subcommands are **probed at runtime**, never assumed; pin the
  version you generated against.

## References

- `references/standards.md`: DTCG 2025.10 (stable URL), WCAG 2.2 AA + the 9 new-since-2.1 criteria
  (3.0/APCA excluded), Material 3 Expressive, Apple Liquid Glass, DSDS (emerging/unendorsed), the
  live handoff pipeline.
- `assets/templates/`: `tokens.dtcg.json` (canonical skeleton), `DESIGN.md` (optional alpha),
  `contrast-report.md`.
- `scripts/dtcg_validate.py` · `scripts/contrast.py`

## Boundaries

- Screen structure, flows, and states → `product-design-spec`.
- The requirements themselves → `product-prd`.
- Auditing an existing/rendered design's UX or accessibility → `review-design`.
- Rendering the actual logo / hero / mascot art → `codex-imagegen` (or `nanobanana`).
- Building the themed UI → `implement-feature`.
- This skill only authors and validates the token contract. Writes no application code.
