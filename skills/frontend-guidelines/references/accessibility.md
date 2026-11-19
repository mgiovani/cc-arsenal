# Accessibility

## Contents

- [Contrast and color](#contrast-and-color)
- [Focus and keyboard](#focus-and-keyboard)
- [Targets and text](#targets-and-text)
- [Forms and announcements](#forms-and-announcements)
- [Proving it](#proving-it)

## Contrast and color

Compute contrast, never assert it. Normal text needs 4.5:1. Large text, control borders, icons and focus indicators need 3:1. Treat 7:1 as an opt-in target for a product that commits to it.

- Check every token pair used for text on a surface, in every state (hover, disabled, focus) and in every theme. A pass in light says nothing about dark.
- Measure the real button fill under a label, not the page background.
- "Large text" is 24px regular or about 19px bold. A regular 18px line is normal text.
- Do not lower text opacity to look softer without re-checking the ratio. Hover and focus raise contrast, never lower it.
- Prefer a solid color to a translucent overlay when alpha would make contrast depend on whatever sits behind.
- A control whose edge defines it needs a 3:1 border. A hairline of about 1.2:1 is for decorative dividers only.
- Never carry status in color alone. Pair color with text and an icon or shape, in charts as well: separate series by pattern, marker or direct label, and ship a data table or text summary with each chart.
- A hover-only label is forbidden, since touch and keyboard users never see it.

## Focus and keyboard

- Show a visible focus ring on every interactive element, including inside modals. Use `:focus-visible`, a 2px ring offset outside the box, and never remove an outline without a replacement.
- Every action revealed on `:hover` also appears on `:focus-within`. Reveal with `visibility` or opacity, not `display`, so layout does not jump.
- A sticky header, banner or chat widget must not fully cover the focused control. Set `scroll-padding` to the header height.
- Keep tab order the same as reading order. A visual reorder (`order-*`) does not change either, so keep DOM order logical.
- Use a real `button` for actions, an anchor for navigation, and `nav` and `main` landmarks. A `div` with `onClick` has no keyboard path or role.
- Place a skip link first in the DOM on navigation-heavy pages. Keep heading levels sequential.
- Dialogs trap focus, close on Escape and return focus to the trigger. A tested primitive does all three.
- Every drag-to-reorder or drag-to-resize needs a single-pointer alternative and keyboard operation, such as move up and move down buttons.
- Keyboard-initiated actions work without waiting for an animation.

## Targets and text

- Interactive targets are at least 44 by 44px with at least 8px between neighbors. The visible mark may be smaller than the hit area. WCAG AA asks only for 24px, but the owner's projects hold 44px everywhere.
- Body text is 16px or larger, which also stops mobile browsers zooming on input focus.
- Layouts survive 200% browser zoom and the largest system text size without clipping. Never disable user zoom, and give text containers no fixed width.
- Do not clamp essential text (names, errors, safety copy) to even out cards. Where truncation is unavoidable, expose the full text to keyboard and touch users.
- Every clock value that means a past moment ends in a visible "ago". The word is text, not a hidden label.

## Forms and announcements

- Give every input a visible label bound with `htmlFor` and `id`. A placeholder is an example, never a label.
- Mark an invalid field with `aria-invalid` and point `aria-describedby` at its inline error. Mark required fields in text as well as color.
- After a failed submit with several errors, move focus to a summary that links each field. With one error, focus that field. Do not move focus on blur.
- Use semantic `type` values and `autocomplete` tokens. Allow paste and password managers. Offer a non-cognitive sign-in path where you can.
- Announce status changes in a polite live region. Use `role="alert"` only for an error that must interrupt. A toast announces through its own primitive, so do not wrap it in a second live region. Announce a changed count as one phrase ("3 items in cart").
- Name every icon-only control with `aria-label` or hidden text. A meaningful icon pairs a hidden SVG with visually hidden text.
- Build toggles and chips as native buttons with `aria-pressed` or `aria-selected` that matches the visible state.
- Give a loading control `aria-busy` and hidden loading text, since a spinner alone is silent.

## Proving it

- Run axe in every interactive component's test and set each story to fail on a violation.
- Query by role and accessible name in tests.
- Run `jsx-a11y` recommended in lint. Add a rule that a heading component has content if the project has one.
- Walk the primary flow with the keyboard only: tab order, no traps, focus visible at each step. Spot-check one screen reader before you call a flow done.
- Check light and dark themes, reduced motion and the largest text size as separate passes.
- Say what evidence came from an emulated viewport and what stayed untested on real hardware, such as touch gestures.
