# Tokens and Theming

## Contents

- [Two tiers](#two-tiers)
- [One source, generated output](#one-source-generated-output)
- [Color roles](#color-roles)
- [Spacing, radius and elevation](#spacing-radius-and-elevation)
- [Type](#type)
- [Themes](#themes)
- [Tailwind specifics](#tailwind-specifics)

## Two tiers

Primitives hold raw values. Semantic tokens name a role and point at a primitive. Components and product code read semantic tokens only, never a primitive or a palette name.

The reason is reach: a rebrand or a theme change then edits one layer and touches no component. A card that uses a gray ramp step directly is the defect this tier split exists to prevent.

Name tokens by role (surface, action, focus, status), not by value (blue-800). A value name stops being true the day the theme changes. Keep the project's own scale keys and do not rename them to a framework's default vocabulary.

## One source, generated output

Keep tokens in one source file, ideally W3C DTCG JSON, and generate the CSS custom properties from it. Never edit the generated file by hand and exclude it from lint and format.

- Gate the build on a check script (`tokens:check`) that regenerates in memory and fails on drift. It must never write to the tree, or a clean build hides a stale commit.
- Fail the generator on an unresolved alias. A typo in a token path otherwise ships as an invalid value and the build still passes.
- When a token or a component changes in one layer, propagate it to every other layer in the same change.
- Promote a value to a token only when it is reused. Do not build a system for one local exception.

## Color roles

- Pair every surface with its foreground token so text color is never picked by eye. A change to one of the pair changes the other in the same edit.
- Text or an icon on a solid fill uses the on-accent token, and it keeps that color through hover, pressed and disabled states.
- Muted text tokens exist for decoration and non-text use in some systems. If the project forbids a token for text, never use it for text at any size.
- Avoid pure black and pure white. Use a tinted ink and a tinted lightest surface so contrast stays high without glare.
- Color is scarce and carries meaning. A status color keeps one meaning across the product, and danger color is spent on failure and irreversible actions only.
- Never put gray text on a colored surface. Derive secondary text from the surface hue.
- For a new palette, prefer OKLCH and cut chroma near white and black so ramps do not blow out.

## Spacing, radius and elevation

- All spacing is a multiple of 4px from one named scale. A 2px optical nudge uses a half-step token, never a bare value.
- Give each spacing step one meaning, such as 4px label to value, 8px between sibling buttons, 16px card padding, 32px between sections. Steps with two meanings drift.
- Decide corner radius once, in tokens. Two of the owner's projects use square corners (every radius token resolves to 0). One uses a small scale with nested radius equal to outer radius minus the gap. Follow the project, and never set a radius in a component.
- Elevation comes from a surface ramp (canvas, content, floating) plus a hairline. Shadows appear only on floating layers, from one elevation scale. A flat surface at rest with a hover shadow is decoration.
- Use named z-index layers (base, sticky, overlay, modal, tooltip). Arbitrary values such as 9999 start stacking wars.
- Use logical properties (`ms`, `me`, `ps`, `pe`, `start`, `end`) instead of left and right, so a layout survives a direction change.

## Type

- One family, usually the platform sans. A second face needs one job, such as hero headings, and never appears in labels or buttons.
- Four sizes and two weights (400 and 500) are enough for product UI. More steps read as mush, and a missing weight forces emphasis through size or position.
- Body text is 16px at minimum. A 14px caption size is for secondary metadata only, and nothing goes smaller.
- Use two line heights (about 1.2 for display, 1.5 for reading) and tighten tracking on display sizes only.
- Cap prose near 65 characters, within 45 to 75. Use `text-wrap: balance` on headings and `pretty` on body copy.
- Use tabular numerals for prices, counts, timers and table columns so digits do not jitter.
- Sizes are a fixed scale in product UI. Fluid `clamp()` sizing is for marketing displays.

## Themes

Ship one theme unless the project asks for two. Two of the owner's projects are single-theme (one dark, one light) and say so as a closed design decision, so do not add a toggle.

When a project has two themes, compose each one. Remap only the semantic layer, re-derive neutrals as real dark surfaces, lighten and desaturate accents for dark, and set `color-scheme` so browser controls follow. Inverting the light palette gives muddy contrast.

Set the stored theme before first paint with a small inline script wrapped in try/catch. Reading it in a mount effect flashes the wrong theme.

## Tailwind specifics

- Register tokens in the theme block (`@theme`) so real utilities exist, and use no config file when the project is CSS-first. Importing the same theme through two compilations duplicates every token.
- Write full class strings. A class built as `text-${color}-500` is invisible to the scanner and silently produces no style. Map variants to complete strings instead.
- Prefer utilities inline and extract a component when a class group repeats across files. Use `@apply` only for a base repeated in many files.
- Drive state styling from `aria-*` and `data-*` attributes, so a style can never drift from the real state.
- In plain CSS projects the same rules hold with `var(--color-semantic-*)` and `var(--space-N)`. No hex appears in component CSS.
