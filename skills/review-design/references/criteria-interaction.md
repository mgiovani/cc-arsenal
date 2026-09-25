# Design Review: Interaction Criteria (Dimensions 5-8)

Measurable, citation-backed audit criteria for the interaction dimensions.
Each criterion has a stable ID and a measurable test, cited to its source.
Agents 4-6 load this file before auditing. Every citation below is WCAG 2.2 unless noted; only the success criterion (SC) number is given.

---

## Dimension 5: Components & Affordance (Buttons & Icons)

### Buttons

| ID | Criterion | Citation | Severity |
| --- | --- | --- | --- |
| CP-01 | Buttons look clickable. They read as distinct from plain text through a fill or border (or some other clear shape). Flag flat text that's indistinguishable from a link or label. | NN/g "flat design affordances"; MD3 button types | Medium |
| CP-02 | Emphasis hierarchy among actions: primary (filled) > secondary (tonal/outlined) > tertiary (text). Flag all-buttons-identical-emphasis, or more than one filled primary per view. | MD3 button hierarchy | Medium |
| CP-03 | Minimum target size: interactive controls are ≥ 44×44px (Apple HIG) / ≥ 48×48dp (MD3). Hit areas smaller than that should be flagged. | Apple HIG; MD3; SC 2.5.8 (24×24 min AA) | High (Critical if < 24px) |
| CP-04 | Adequate spacing between targets: adjacent tap targets have spacing (~8dp) to avoid mis-taps. | MD3; WCAG 2.5.8 spacing exemption | Medium |
| CP-05 | Action labels are verbs/specific: buttons say what they do ("Save changes"), not "OK"/"Submit" where ambiguous. | NN/g; Apple HIG writing | Low |
| CP-06 | Consistent button shape/radius/padding: corner radius and padding are tokenized and consistent across the app. | MD3 shape system; Refactoring UI | Low |

### Icons

| ID | Criterion | Citation | Severity |
| --- | --- | --- | --- |
| IC-01 | Icons paired with text labels: icon-only buttons are limited to universally understood glyphs; otherwise pair with a label or `aria-label`. | NN/g "icon usability"; Apple HIG | Medium |
| IC-02 | Consistent icon set/style: pick one icon family and weight, on one grid. Mixing outline and filled styles, or different stroke widths, breaks this criterion. | MD3 system icons; Apple HIG SF Symbols | Low |
| IC-03 | Optical sizing/alignment: icons sit on a consistent grid (e.g., 24dp) and are optically centered with adjacent text. | MD3 icon grid | Low |
| IC-04 | Icons meet non-text contrast: meaningful icons ≥ 3:1 vs. background. | SC 1.4.11 | High |

---

## Dimension 6: Feedback & States

| ID | Criterion | Citation | Severity |
| --- | --- | --- | --- |
| FB-01 | Visibility of system status: the system always shows what's happening, loading, saving, success, error, within a reasonable time. Silent actions should be flagged. | NN/g Heuristic #1; Laws of UX: Doherty Threshold | High |
| FB-02 | All interactive states present: interactive elements define a default state plus hover, focus, active/pressed, and disabled. Gaps here (most often hover or disabled) are worth flagging. | MD3 state layers; NN/g | Medium |
| FB-03 | Distinct focus state (keyboard): a visible focus indicator exists and is not removed without replacement (see AC-02). | SC 2.4.7 / 2.4.11 | High |
| FB-04 | Loading feedback for waits > ~1s: operations over ~1s show a spinner/skeleton/progress; over ~10s show progress plus allow cancel where possible. | NN/g response-time limits (0.1s / 1s / 10s); Doherty Threshold (~400ms) | Medium |
| FB-05 | Skeletons/optimistic UI for perceived speed: prefer skeletons over blank/spinner for content loads where feasible. | NN/g; MD3 loading | Low |
| FB-06 | Errors are clear and specific, with a path to recovery: the message says what went wrong and how to fix it, placed near the offending field. A generic "Error occurred" counts as a finding. | NN/g error-message guidelines; Heuristic #9 | Medium |
| FB-07 | Empty states are designed: empty lists/first-run show guidance, not a blank area. | NN/g empty states | Low |
| FB-08 | Destructive actions confirm or are undoable: delete/irreversible actions confirm or offer undo. | NN/g Heuristic #3 (user control); MD3 snackbar undo | Medium |
| FB-09 | Success confirmation: completed actions are acknowledged (toast/inline), not silent. | NN/g visibility of status | Low |

---

## Dimension 7: Motion & Microinteractions

| ID | Criterion | Citation | Severity |
| --- | --- | --- | --- |
| MO-01 | Respect `prefers-reduced-motion`: non-essential animation is reduced or removed under `@media (prefers-reduced-motion: reduce)`. Animation with no reduced-motion handling fails this check. | SC 2.3.3; MDN reduced-motion | High |
| MO-02 | Durations in the 200-500ms band: UI transitions feel responsive, ~150-200ms for small elements and ~250-400ms for larger; over 500ms for routine UI is sluggish, under 100ms feels instant/janky. | MD3 motion duration tokens; NN/g animation duration; Doherty Threshold | Medium (High if > 1000ms on a blocking transition) |
| MO-03 | Natural easing, not linear: movement uses ease-in-out / standard easing curves, not `linear` (except continuous spinners). | MD3 easing; NN/g | Low |
| MO-04 | Motion has purpose: animation should guide attention or clarify a relationship, giving feedback rather than acting as decoration that slows the user down. Gratuitous motion is a finding. | NN/g "animation purpose"; MD3 motion principles | Low |
| MO-05 | No flashing more than 3×/sec: nothing flashes more than three times per second. | SC 2.3.1 (seizure safety) | Critical |
| MO-06 | Microinteraction feedback is immediate: toggles, likes, button presses give instant visual response (state layer/ripple) before any async result. | MD3 state layers; NN/g microinteractions | Low |
| MO-07 | Animation is interruptible: users can act during/over an animation; it never blocks input. | NN/g | Low |

---

## Dimension 8: Accessibility (WCAG 2.2 AA, cross-cutting)

| ID | Criterion | Citation | Severity |
| --- | --- | --- | --- |
| AC-01 | Text alternatives: all meaningful images have `alt`; decorative images have empty `alt=""`; icon buttons have `aria-label`/visible label. | SC 1.1.1 | High |
| AC-02 | Focus visible and not suppressed: a keyboard focus indicator is visible, and it meets size/contrast (≥ 3:1, not fully obscured). Flag `outline: none`/`outline: 0` used without a `:focus-visible` replacement. | SC 2.4.7, 2.4.11, 2.4.13 | High |
| AC-03 | Keyboard operable and logical order: all interactive elements are reachable and operable by keyboard; DOM/tab order matches visual order; no keyboard traps. | SC 2.1.1, 2.4.3 | High |
| AC-04 | Color is not the only signal: status/links/required fields use text/icon/shape in addition to color. | SC 1.4.1 | High |
| AC-05 | Contrast (text and non-text): meets CO-06 (4.5:1 body), CO-07 (3:1 large), CO-08 (3:1 UI/icons). | SC 1.4.3, 1.4.11 | High/Critical |
| AC-06 | Form labels and associations: every input has a programmatic `<label for>` / `aria-label` / `aria-labelledby`; placeholder is not the only label. | SC 1.3.1, 3.3.2, 4.1.2 | High |
| AC-07 | Touch target size (AA): pointer targets ≥ 24×24px (or adequate spacing). | SC 2.5.8 | Medium (see CP-03 for the stricter 44/48 guideline) |
| AC-08 | Semantic structure and landmarks: one `<h1>`, no skipped heading levels, native landmarks (`<nav>/<main>/<header>`), native controls over `<div onclick>`. | SC 1.3.1; 4.1.2 | Medium |
| AC-09 | Resize/reflow: text resizes to 200% and content reflows at 320px wide without loss of content/function or horizontal scrolling. | SC 1.4.4, 1.4.10 | Medium |
| AC-10 | Visible labels match accessible names: the accessible name contains the visible label text. | SC 2.5.3 Label in Name | Medium |
| AC-11 | Reduced motion honored: mirrors MO-01. | SC 2.3.3 | High |
| AC-12 | Dragging and accessible auth (WCAG 2.2 new): drag actions have a single-pointer alternative (SC 2.5.7); auth doesn't require a cognitive memory test without an alternative (SC 3.3.8). | WCAG 2.2 | Medium |
