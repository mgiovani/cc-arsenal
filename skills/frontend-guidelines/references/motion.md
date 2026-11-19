# Motion

## Contents

- [The default](#the-default)
- [The four-question filter](#the-four-question-filter)
- [Tokens](#tokens)
- [Recipes](#recipes)
- [Reduced motion](#reduced-motion)
- [Review lens](#review-lens)

## The default

The owner's default is functional, short and optional motion. Motion confirms an input or explains a change, and it never decorates. The answer for a daily-use interface is less motion, and an empty list of animations is a valid result.

Motion on data a person reads or acts on, such as a chart or a number, stays off even when it looks good.

## The four-question filter

Run every candidate through these in order. Failing any one drops it, and you record the answer.

1. Frequency. A hundred or more uses a day (shortcuts, command palette, core navigation) never animates. Tens a day (hover, list navigation) gets nothing or near-invisible motion. Occasional surfaces (dialogs, drawers, toasts) get standard motion. Rare and first-time moments (onboarding, success, an empty first run) may carry delight.
2. Purpose. Name one: feedback, spatial continuity, state change, avoiding an abrupt appearance, or explanation. "It looks good" fails.
3. Speed. The duration fits the token bucket for that element.
4. Function. The motion survives interruption and a repeated trigger.

Keyboard-initiated actions are disqualified outright. Repeated hundreds of times, any delay makes them feel disconnected.

## Tokens

Take every duration, curve, scale and distance from tokens. A literal `200ms`, a raw `ease` or a bare `scale(0.97)` in a component is a defect, because it leaves a second motion system that no review catches.

- Three duration buckets: fast (about 120ms: hover, press, focus), base (about 160ms: disclosure, notice) and panel (about 200ms: dialogs and popovers). Nothing in routine UI runs over 300ms. Take the exact values from the project.
- Exits run faster than entrances, around 60 to 70% of the enter time.
- Keep named curves on the root: a strong ease-out for enter and exit, an ease-in-out for movement across the screen, and linear only for loaders, progress and hold fills. Do not use ease-in on UI, since it delays the first moment the user is watching.
- Keep a press scale token (about 0.97) and distance tokens. Zeroing them under reduced motion is then one edit.
- If a JS motion library is in use, read values from one module mirrored from the CSS tokens, with a parity test that fails when they drift.

## Recipes

- Press. A compact control scales to about 0.97 on `:active`, over the fast token. A press never shifts layout.
- Hover. Wrap hover effects in `@media (hover: hover) and (pointer: fine)` so touch screens do not stick a hover state.
- Transition named properties, never `all`. `all` animates properties nobody intended and costs paint time.
- Animate only `transform` and `opacity`. They run on the compositor, while width, height and margin force layout. The accordion exception is a grid row transition from `0fr` to `1fr`.
- Enter from about 0.95 scale with opacity 0, never from `scale(0)`. Use `@starting-style` where supported, and a mount attribute as the fallback.
- A popover scales from its trigger, so set `transform-origin` there. A modal stays centered. A toast or sheet exits along the edge it entered from, using percentage offsets.
- Prefer CSS transitions to keyframes for anything toggled quickly. A transition reverses from its current value, and a keyframe restarts from zero.
- A hold-to-confirm fill for a destructive action runs on its own long token, linear, with a snap back on release.
- Use springs only for drag with momentum and for gestures that can be interrupted. Keep bounce between 0.1 and 0.3.
- No spinner for waits under about 300ms. Use a skeleton of the final shape for content regions and a spinner for a short action.
- Do not drive per-frame motion by setting a custom property on a parent. Write `style.transform` on the moving element.

The owner's projects rejected these on principle: route fades, card stagger, number tweens, a rail sliding in and row hover lift. If a brief asks for a stagger, run it at 30 to 80ms per item, cap the total delay and never block input.

## Reduced motion

Under `prefers-reduced-motion: reduce`, remove travel, scale and parallax and keep opacity and color changes. Zero the distance and scale tokens instead of killing every transition, because fades still carry meaning. No motion may be the only carrier of a state change. Pause looping animation when the tab is hidden or the element is off screen.

## Review lens

When you review motion, name each finding with the gate question it fails and the exact value to use.

- Search for seams that teleport: conditional renders with no bridge (`{open && ...}`), `display: none` toggles and list items that enter or leave. Content popping in is the main target.
- Reject more than you propose. List 2 to 5 rejected candidates, each with the gate question that killed it. Cap proposals at 5 to 7 for a whole app.
- Replay at 2 to 5 times slower speed, then frame by frame. Look for two overlapping states, a stalled curve, a wrong origin and properties out of sync.
- Flag `transition: all`, `scale(0)` entrances, ease-in, a center origin on a popover, hover without the pointer query, durations over 300ms and animation on a keyboard action.
- Say when feel cannot be judged from code. Check a gesture on a real phone, not only an emulator.
