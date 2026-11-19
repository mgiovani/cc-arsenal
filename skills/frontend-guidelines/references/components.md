# Components

## Contents

- [Folder shape](#folder-shape)
- [Writing the component](#writing-the-component)
- [Variants](#variants)
- [Icons](#icons)
- [Controls and overlays](#controls-and-overlays)
- [Stories and tests](#stories-and-tests)
- [Layout checks for cards](#layout-checks-for-cards)

## Folder shape

Each reusable component lives in a PascalCase folder with five files. Route files are exempt.

```
Button/
  Button.tsx
  Button.variants.ts
  Button.stories.tsx
  Button.test.tsx
  index.ts
```

`index.ts` exports the component, its props type and its variants. A plain-CSS project without Tailwind swaps `Button.variants.ts` for a stylesheet beside the component, and keeps the other four.

In logic folders such as `lib/` and `entities/`, use kebab-case file names and colocate `*.test.ts` next to the source.

## Writing the component

- Write a named function component with an exported props interface. Use named exports only, no default exports, and no `React.FC`.
- Extend the native element's props (`ComponentProps<'button'>`) and spread the rest, so every native attribute works.
- Take `ref` as a plain prop. Do not add a new `forwardRef` wrapper in current React.
- Default `type` to `'button'` on buttons. A bare button inside a form submits it.
- Use a discriminated union when one variant needs an extra prop, such as an icon-only variant that requires `aria-label`. The type then rejects the unlabelled case.
- Use string-literal unions for variants and states, not enums.
- Answer one question in the usage notes: what single thing does this communicate? A component that needs a longer answer does two jobs, so split it.
- Reuse first. Zero variants per screen and zero hand-copied versions of what a primitive already does.
- Show a loading control with `aria-busy` and `aria-disabled` and hidden loading text. The native `disabled` attribute drops focus and breaks password managers.
- Define no component inside another component. Each parent render creates a new type, so React remounts it and loses focus and state.

## Variants

- Put variants in a `tv` or `cva` table with a base string, `variant` and `size` maps and `defaultVariants`. A new look is a new key, never an ad-hoc class at a call site.
- Merge with a `cn` helper and pass the consumer `className` last, so overrides win without specificity hacks.
- Use a per-instance `className` for a one-off tweak. Promote it to a named variant when it repeats.
- Give each action tier a distinct look: filled primary, outlined secondary, borderless utility. One primary per decision point, and the same action looks the same everywhere.

## Icons

- Use one icon set. The owner's projects use Phosphor at light weight, drawn as `currentColor` with no stroke attribute.
- Render every icon through one `Icon` wrapper that takes a name and a size token. Ban direct imports of the set with a `no-restricted-imports` rule, except inside the wrapper.
- Allow three sizes, from tokens: inline, action and status. A fourth size is a defect.
- An icon replaces a label, never a value. A metadata row carries at most two icons, and a dense table row carries none.
- A decorative icon beside text is `aria-hidden`. A meaningful icon pairs a hidden SVG with visually hidden text.
- Never use emoji or a Unicode glyph as an icon.

## Controls and overlays

- Use the platform control when it does the job: `<dialog>` with `showModal()`, `<input type="date">`. A house component beats a native widget when one exists.
- Some projects ban the native `<select>` and ship a custom listbox. Use the project's listbox, with combobox roles, arrow keys, Escape returning focus, and 44px rows.
- Build dialogs, menus, tabs, popovers and accordions on a tested primitive set (Radix). Hand-rolled versions miss focus trapping, Escape and focus return.
- Use an alert dialog to confirm an irreversible action and a plain dialog for forms. Use a menu for action lists and a popover for free content.
- Overlays must escape clipping ancestors: use `<dialog>`, the popover API or a portal, never an absolutely positioned box inside `overflow: hidden`.
- Reach for a modal last. Inline or progressive options usually fit the task better.
- Pass `asChild` when a primitive trigger wraps your own button, so no button nests inside a button. Use it only where the primitive exposes it.
- Use the project's heading component with its level context, not literal `h2` to `h6` tags. Use `h1` once per page.

## Stories and tests

- Write one story per concept, with a `play` function that asserts the outcome. Title them `Group/Export`. Every story runs as a test.
- Set `a11y: { test: 'error' }` on each story, and run an axe check in each interactive component's test. A violation then fails the run instead of a warning nobody reads.
- Cover the state cycle in stories: default, hover, focus, disabled, loading, error. When several states apply, priority runs disabled, loading, active, focus, hover, default.
- Query by role and accessible name, not by class or test id. The query doubles as an accessibility check.
- Write story copy in the product's real domain language. Generic names and lorem ipsum make a story look like a template.
- A project without Storybook keeps the same bar: a colocated test per component with an axe run and a state table.

## Layout checks for cards

- Every row inside a card starts at the same x position. Push a trailing item right with `margin-inline-start: auto`.
- Cards in one row share one height, and the trailing element in each uses `margin-top: auto`. Do not use `align-items: start` on a grid of cards.
- Keep card anatomy fixed and in order: padding, header, title, metadata, actions. A rule line in one card of a set that otherwise shares the structure is a defect.
- Give flex and grid children `min-width: 0` so text can shrink. Never fix a button width to its English label.
