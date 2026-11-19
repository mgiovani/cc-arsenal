---
name: frontend-guidelines
description: "React, TypeScript and Tailwind defaults for product UI: semantic design tokens only, one icon wrapper, layered imports enforced by lint, component folders with stories used as tests plus axe, motion only through tokens, no lint or type suppressions, Prettier settings and bun, plus a short design and motion review lens. Use when writing or changing frontend code (components, styles, routes, hooks, lint config) and the project has no stricter rule, or when asked how to structure a React app or whether a screen looks templated. Not for language-agnostic rules (use code-guidelines), Python services (use backend-guidelines), auditing a live UI against WCAG and platform guidelines (use review-design), producing the token contract (use product-design-tokens) or deciding screens and flows (use product-design-spec)."
metadata:
  summary: "Owner's React, TypeScript and Tailwind defaults: tokens, layering, components, motion, a11y, design review"
---

# Frontend Guidelines

The project's own AGENTS.md or CLAUDE.md and its lint config win over this skill. Apply these rules only where the project is silent, and say so when you follow a project rule that differs.

Apply the `code-guidelines` skill first: use the `Skill` tool where available, otherwise read its SKILL.md and the references it routes to, and announce it with a `Using code-guidelines for the language-agnostic rules` line. This skill holds only what is specific to the frontend and repeats none of it.

Before the first edit, read the project's instruction files, any DESIGN.md or token source, the lint and TypeScript config, and one existing component of the kind you are adding. Find the real check commands in `package.json` scripts or the task runner so you can run them at the end.

## Pick the reference

| What you are doing | Read |
|---|---|
| Adding a color, spacing, radius, font size or theme value | [references/tokens-and-theming.md](references/tokens-and-theming.md) |
| Building or changing a component, an icon, a variant or a story | [references/components.md](references/components.md) |
| Deciding where code goes or drawing an import boundary | [references/layering.md](references/layering.md) |
| Fetching data, fixing a slow render, loading a heavy module | [references/react-performance.md](references/react-performance.md) |
| Handling focus, labels, contrast, announcements or keyboard use | [references/accessibility.md](references/accessibility.md) |
| Laying out a screen or judging hierarchy, density and imagery | [references/visual-design.md](references/visual-design.md) |
| Adding or reviewing a transition, an entrance or a press state | [references/motion.md](references/motion.md) |
| Writing UI strings, empty, loading and error states, confirmations | [references/ux-copy-and-states.md](references/ux-copy-and-states.md) |
| Asking whether a screen reads as templated or machine made | [references/anti-slop.md](references/anti-slop.md) |
| Setting up lint, formatting, TypeScript, tests or the package manager | [references/tooling.md](references/tooling.md) |

Read one reference per task. Read a second only when the task crosses both topics, such as a new animated dialog.

## Rules for every task

1. Use semantic tokens only. Write no hex, `rgb()`, `oklch()`, palette name or off-scale pixel value in a class, a style or a stylesheet outside the token source. A raw value starts a second palette that no theme change reaches.
2. Reuse the primitives in `ui/` before writing markup. One primitive per concern, used the same way on every screen, with no per-screen variant.
3. Import every icon through one wrapper component, from one icon set. A second set or a direct import breaks size, weight and lint rules in one move.
4. Import only downward: routes, then features, then entities, then ui, then lib. Lint enforces it, so a wrong import fails the build rather than a review.
5. Give every reusable component a folder with its story, its test and its variants. The story runs as a test and carries an axe check, so accessibility is part of done.
6. Take every duration, curve, scale and distance from motion tokens. Animate only to confirm an input or explain a change.
7. Add no `eslint-disable` and no `ts-ignore`. Fix the cause, or change the rule in the shared config with the reason written there. A suppression hides the next real defect on the same line.
8. Design every state a component can be in: default, hover, focus, active, disabled, loading, empty and error.
9. Verify with the project's own check script, then look at the rendered result at phone and desktop widths. A green lint run says nothing about spacing, overflow or a blank region.

## When projects differ

Two choices differ between the owner's projects. Follow the project in front of you and do not mix them.

- Lint and format: the default is ESLint with Prettier. A project with a `biome.json` uses Biome alone, with no second formatter beside it.
- Package manager: the default is bun. A project with a `pnpm-lock.yaml` or a `packageManager` field naming another tool keeps that tool and its single lockfile.

Visual taste differs too: rounded or square corners, one theme or two, plain CSS or Tailwind. The reference files state the default and say where the project's DESIGN.md decides instead.

## Verify

Run the project's check script (often `bun run check`). It should cover token drift, generated client drift, typecheck, lint, format, import boundaries, build and tests. Then open the screen at about 390 and 1440 pixels wide, with motion settled, and judge the real pixels. Say which checks you could not run.
