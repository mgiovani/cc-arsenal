# Design Review: Interaction Criteria (Dimensions 5-8)

Measurable, citation-backed audit criteria for the interaction dimensions.
Each criterion has a stable **ID**, a **measurable test**, and a **citation**.
Agents 4–6 load this file before auditing.

---

## Dimension 5: Components & Affordance (Buttons & Icons)

### Buttons

- **CP-01: Buttons look clickable (affordance).** Buttons are visually distinct from text
  (fill, border, or clear shape). Flat text indistinguishable from a link/label is a finding.
  *NN/g "flat design affordances"; MD3 button types.* Severity: Medium.
- **CP-02: Emphasis hierarchy among actions.** Primary (filled) > secondary (tonal/outlined)
  > tertiary (text). All buttons identical-emphasis, or > 1 filled primary per view, is a
  finding. *MD3 button hierarchy.* Severity: Medium.
- **CP-03: Minimum target size.** Interactive controls are ≥ 44×44px (Apple HIG) / ≥ 48×48dp
  (MD3). Smaller hit areas are a finding. *Apple HIG; MD3; WCAG 2.2 SC 2.5.8 (24×24 min AA).*
  Severity: High (Critical if < 24px).
- **CP-04: Adequate spacing between targets.** Adjacent tap targets have spacing (~8dp) to
  avoid mis-taps. *MD3; WCAG 2.5.8 spacing exemption.* Severity: Medium.
- **CP-05: Action labels are verbs/specific.** Buttons say what they do ("Save changes"),
  not "OK"/"Submit" where ambiguous. *NN/g; Apple HIG writing.* Severity: Low.
- **CP-06: Consistent button shape/radius/padding.** Corner radius and padding are
  tokenized and consistent across the app. *MD3 shape system; Refactoring UI.* Severity: Low.

### Icons

- **IC-01: Icons paired with text labels.** Icon-only buttons are limited to universally
  understood glyphs; otherwise pair with a label or `aria-label`. *NN/g "icon usability";
  Apple HIG.* Severity: Medium.
- **IC-02: Consistent icon set/style.** One icon family/weight/grid; mixing outline + filled
  + different stroke widths is a finding. *MD3 system icons; Apple HIG SF Symbols.* Severity: Low.
- **IC-03: Optical sizing/alignment.** Icons sit on a consistent grid (e.g., 24dp) and are
  optically centered with adjacent text. *MD3 icon grid.* Severity: Low.
- **IC-04: Icons meet non-text contrast.** Meaningful icons ≥ 3:1 vs. background.
  *WCAG 2.2 SC 1.4.11.* Severity: High.

---

## Dimension 6: Feedback & States

- **FB-01: Visibility of system status.** The system always shows what's happening
  (loading, saving, success, error) within a reasonable time. Silent actions are a finding.
  *NN/g Heuristic #1; Laws of UX: Doherty Threshold.* Severity: High.
- **FB-02: All interactive states present.** Interactive elements define default, **hover**,
  **focus**, **active/pressed**, and **disabled** states. Missing hover/active/disabled is a
  finding. *MD3 state layers; NN/g.* Severity: Medium.
- **FB-03: Distinct focus state (keyboard).** A visible focus indicator exists and is not
  removed without replacement (see AC-02). *WCAG 2.2 SC 2.4.7 / 2.4.11.* Severity: High.
- **FB-04: Loading feedback for waits > ~1s.** Operations over ~1s show a spinner/skeleton/
  progress; over ~10s show progress + allow cancel where possible. *NN/g response-time limits
  (0.1s / 1s / 10s); Doherty Threshold (~400ms).* Severity: Medium.
- **FB-05: Skeletons/optimistic UI for perceived speed.** Prefer skeletons over blank/spinner
  for content loads where feasible. *NN/g; MD3 loading.* Severity: Low.
- **FB-06: Errors are clear, specific, and recoverable.** Error messages say what went wrong
  and how to fix it, near the offending field. Generic "Error occurred" is a finding. *NN/g
  error-message guidelines; Heuristic #9.* Severity: Medium.
- **FB-07: Empty states are designed.** Empty lists/first-run show guidance, not a blank
  area. *NN/g empty states.* Severity: Low.
- **FB-08: Destructive actions confirm / are undoable.** Delete/irreversible actions confirm
  or offer undo. *NN/g Heuristic #3 (user control); MD3 snackbar undo.* Severity: Medium.
- **FB-09: Success confirmation.** Completed actions are acknowledged (toast/inline), not
  silent. *NN/g visibility of status.* Severity: Low.

---

## Dimension 7: Motion & Microinteractions

- **MO-01: Respect `prefers-reduced-motion`.** Non-essential animation is reduced/removed
  under `@media (prefers-reduced-motion: reduce)`. Animations with no reduced-motion handling
  are a finding. *WCAG 2.2 SC 2.3.3; MDN reduced-motion.* Severity: High.
- **MO-02: Durations in the 200–500ms band.** UI transitions feel responsive: ~150–200ms for
  small elements, ~250–400ms for larger; **> 500ms** for routine UI is sluggish, **< 100ms**
  feels instant/janky. *MD3 motion duration tokens; NN/g animation duration; Doherty Threshold.*
  Severity: Medium (High if > 1000ms on a blocking transition).
- **MO-03: Natural easing, not linear.** Movement uses ease-in-out / standard easing curves,
  not `linear` (except continuous spinners). *MD3 easing; NN/g.* Severity: Low.
- **MO-04: Motion has purpose.** Animation guides attention, shows relationships, or gives
  feedback, not decoration that delays the user. Gratuitous motion is a finding. *NN/g "animation
  purpose"; MD3 motion principles.* Severity: Low.
- **MO-05: No flashing > 3×/sec.** Nothing flashes more than three times per second.
  *WCAG 2.2 SC 2.3.1 (seizure safety).* Severity: Critical.
- **MO-06: Microinteraction feedback is immediate.** Toggles, likes, button presses give
  instant visual response (state layer/ripple) before any async result. *MD3 state layers;
  NN/g microinteractions.* Severity: Low.
- **MO-07: Animation is interruptible.** Users can act during/over an animation; it never
  blocks input. *NN/g.* Severity: Low.

---

## Dimension 8: Accessibility (WCAG 2.2 AA, cross-cutting)

- **AC-01: Text alternatives.** All meaningful images have `alt`; decorative images have
  empty `alt=""`. Icon buttons have `aria-label`/visible label. *WCAG 2.2 SC 1.1.1.*
  Severity: High.
- **AC-02: Focus visible & not suppressed.** A keyboard focus indicator is visible;
  `outline: none`/`outline: 0` without a `:focus-visible` replacement is a finding. The
  indicator meets size/contrast (≥ 3:1, not fully obscured). *WCAG 2.2 SC 2.4.7, 2.4.11,
  2.4.13.* Severity: High.
- **AC-03: Keyboard operable & logical order.** All interactive elements are reachable and
  operable by keyboard; DOM/tab order matches visual order; no keyboard traps. *WCAG 2.2 SC
  2.1.1, 2.4.3.* Severity: High.
- **AC-04: Color is not the only signal.** Status/links/required fields use text/icon/shape
  in addition to color. *WCAG 2.2 SC 1.4.1.* Severity: High.
- **AC-05: Contrast (text & non-text).** Meets CO-06 (4.5:1 body), CO-07 (3:1 large), CO-08
  (3:1 UI/icons). *WCAG 2.2 SC 1.4.3, 1.4.11.* Severity: High/Critical.
- **AC-06: Form labels & associations.** Every input has a programmatic `<label for>` /
  `aria-label` / `aria-labelledby`; placeholder is not the only label. *WCAG 2.2 SC 1.3.1,
  3.3.2, 4.1.2.* Severity: High.
- **AC-07: Touch target size (AA).** Pointer targets ≥ 24×24px (or adequate spacing).
  *WCAG 2.2 SC 2.5.8.* Severity: Medium (see CP-03 for the stricter 44/48 guideline).
- **AC-08: Semantic structure & landmarks.** One `<h1>`, no skipped heading levels, native
  landmarks (`<nav>/<main>/<header>`), native controls over `<div onclick>`. *WCAG 2.2 SC
  1.3.1; 4.1.2.* Severity: Medium.
- **AC-09: Resize/reflow.** Text resizes to 200% and content reflows at 320px wide without
  loss of content/function or horizontal scrolling. *WCAG 2.2 SC 1.4.4, 1.4.10.* Severity: Medium.
- **AC-10: Visible labels match accessible names.** The accessible name contains the visible
  label text. *WCAG 2.2 SC 2.5.3 Label in Name.* Severity: Medium.
- **AC-11: Reduced motion honored.** Mirrors MO-01. *WCAG 2.2 SC 2.3.3.* Severity: High.
- **AC-12: Dragging & accessible auth (WCAG 2.2 new).** Drag actions have a single-pointer
  alternative (SC 2.5.7); auth doesn't require a cognitive memory test without alternative
  (SC 3.3.8). *WCAG 2.2.* Severity: Medium.
