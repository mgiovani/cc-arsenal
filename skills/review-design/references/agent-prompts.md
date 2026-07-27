# Design Review: Agent Prompts (Live + Static)

Per-agent prompts for Phase 3. Each agent gets a **live** branch (analyze the
screenshot + DOM/a11y snapshot captured in Phase 3) and a **static** branch
(grep the codebase). Pass the agent only the branch matching the resolved mode;
in `both` mode, run each agent twice (once per mode) or instruct it to do both
and label findings by mode.

**Shared instructions for every agent (prepend to each prompt):**

```
You are auditing DESIGN QUALITY. Analysis only — never edit code.

1. First Read the relevant references/criteria-*.md for your dimension(s) and use the
   criterion IDs (e.g., CO-06, AC-02) in every finding.
2. Evidence is mandatory:
   - LIVE: cite the screenshot region (e.g., "top nav, primary CTA") AND the DOM ref/
     selector from /tmp/review-design/snapshot.txt. Record measured values.
   - STATIC: cite file:line for every finding and quote the offending snippet.
3. Record the MEASURED value where one applies: contrast ratio (compute from the two
   hex/rgb colors), px/rem size, ms duration, dp target size.
4. Map each finding to: criterion ID + authoritative citation (WCAG SC number / MD3 spec /
   Apple HIG / NN/g article).
5. Classify severity: Critical / High / Medium / Low (see the criterion's default).
6. Give a concrete fix with the TARGET value (e.g., "raise to ≥ 4.5:1", "use 16px",
   "wrap in @media (prefers-reduced-motion: reduce)").
7. Do not invent issues. If a dimension cannot be observed, say so — do not penalize it.

LIVE artifacts:
  /tmp/review-design/page.png        (full-page screenshot — analyze visually)
  /tmp/review-design/snapshot.txt    (interactive elements + accessibility tree)
You may request computed styles for a ref with: agent-browser get styles @<ref>
and a bounding box (for target size) with: agent-browser get box @<ref>

Return structured findings: {criterion_id, dimension, severity, evidence (file:line or
region+ref), measured_value, citation, description, fix}.
```

### Computing contrast ratio from hex/rgb (no browser needed)

Static mode has no rendered page to sample, so compute the WCAG relative-luminance
contrast ratio directly from the two color values found in the CSS/tokens:

1. For each channel (R, G, B in 0-255), normalize `c = channel / 255`.
2. Linearize: if `c <= 0.03928`, `c_lin = c / 12.92`; else `c_lin = ((c + 0.055) / 1.055) ^ 2.4`.
3. Relative luminance `L = 0.2126*R_lin + 0.7152*G_lin + 0.0722*B_lin`.
4. Contrast ratio `= (L_lighter + 0.05) / (L_darker + 0.05)`, using the two colors'
   luminances (lighter on top so the ratio is >= 1).

Report the ratio to two decimal places as the measured value. If a color comes from a
CSS variable/token, resolve it to its concrete hex value first (grep the token definition)
before computing, don't guess the resolved value. When text sits over a gradient or an
image, say contrast can't be reliably computed statically and note it as a coverage gap
instead of estimating.

Then apply the WCAG threshold that matches the text's actual size/weight (CO-06/07/08,
criteria-foundations.md): normal text needs >= 4.5:1, "large text" (>= 24px, or >= 18.66px
bold) needs >= 3:1, and non-text UI (icons, borders, focus indicators) needs >= 3:1. A ratio
that clears the size-appropriate threshold is a pass, even if it would fail the stricter one.

---

## Agent 1: Visual Hierarchy + Layout & Spacing (Dimension 1)

Criteria: VH-01..04, LY-01..06 (criteria-foundations.md).

```
LIVE:
- In the screenshot, identify the dominant focal point. Flag >1 competing focal point (VH-01)
  and >1 high-emphasis/filled primary button (VH-03).
- Check de-emphasis technique (weight/color vs size only) (VH-02) and that hierarchy steps
  are perceptible (VH-04).
- Measure spacing rhythm from the layout / computed styles: are gaps multiples of 4/8? Flag
  off-scale values (LY-01) and a long tail of one-off values (LY-02).
- Estimate body line length in characters; flag full-width paragraphs > ~75ch (LY-03).
- Check proximity/grouping (LY-04) and alignment to a shared grid (LY-05); flag crowding (LY-06).

STATIC (grep CSS/components/tokens):
- Off-scale spacing: rg -n "(margin|padding|gap|top|left|right|bottom)\s*:\s*\d+px" and flag
  px values not in {0,4,8,12,16,20,24,32,40,48,56,64}. Also Tailwind arbitrary values: rg -n "\[[0-9]+px\]".
- Missing max-width on text containers / prose: rg -n "max-w|max-width" in article/prose/content
  components; flag long-form text with no measure cap (LY-03; target max-width ~65ch).
- Multiple primary buttons: rg -n "variant=\"?primary|btn-primary|Button.*primary" per view (VH-03).
- Detect a spacing scale source of truth (tailwind theme.spacing, --space-* tokens); flag raw
  literals used instead of tokens (LY-02).
```

---

## Agent 2: Typography (Dimension 2)

Criteria: TY-01..08 (criteria-foundations.md).

```
LIVE:
- From computed styles, read body font-size (flag < 16px, TY-01), line-height (flag outside
  1.4–1.6 for body, TY-02), heading line-height (TY-07), and letter-spacing on display text (TY-06).
- Count distinct font sizes (flag many near-duplicates, TY-03), font families (flag > 3, TY-04),
  and weights (TY-05).

STATIC (grep):
- Small body text: rg -n "font-size:\s*(1[0-5]px|0?\.[0-9]+rem|1[0-5]sp)" and Tailwind text-xs/
  text-sm on body copy (TY-01; target ≥ 16px / text-base).
- Tight/loose leading: rg -n "line-height:\s*(1(\.[0-2])?|2(\.[0-9])?)\b" (TY-02; target ~1.5).
- Font family sprawl: rg -n "font-family" and Tailwind font-* ; count unique families (TY-04).
- Fixed px-only type system where zoom matters: rg -n "font-size:\s*\d+px" prevalence (TY-08;
  prefer rem/em).
- Look for a type-scale token source (tailwind fontSize, --font-size-*); flag ad-hoc sizes (TY-03).
```

---

## Agent 3: Color + Dark Mode (Dimension 3)

Criteria: CO-01..08, DM-01..05 (criteria-foundations.md). Compute contrast ratios.

```
LIVE:
- For each prominent text block, sample text vs background color and COMPUTE the WCAG contrast
  ratio. Flag body < 4.5:1 (CO-06), large text < 3:1 (CO-07), icons/borders/focus < 3:1 (CO-08).
- Assess 60-30-10 balance and accent flooding (CO-01); semantic role consistency (CO-03).
- If a dark theme exists, capture it (toggle .dark / prefers-color-scheme) and check: base not
  #000 (DM-01), body text not pure #FFF (DM-02), accents desaturated (DM-03), elevation via
  lighter surface (DM-04), contrast still passes (DM-05).

STATIC (grep):
- Hardcoded colors outside token files: rg -n "#[0-9a-fA-F]{3,8}\b|rgba?\(" --glob '!**/{tokens,theme,colors}.*'
  in component files (CO-02).
- Pure black/white in dark theme: rg -n "#000\b|#000000|background:\s*black" in dark/.dark blocks (DM-01);
  rg -n "#fff\b|#ffffff|color:\s*white" for body text on dark (DM-02).
- Dark mode support presence: rg -n "prefers-color-scheme|\.dark|data-theme|dark:" ; if styling exists
  but no dark variant, note as gap.
- For any text/bg color PAIR you can resolve from tokens, compute contrast and flag AA failures
  (CO-06/07/08). Quote the token names and the computed ratio.
```

---

## Agent 4: Depth/Shadows + Components & Affordance (Dimensions 4, 5)

Criteria: DE-01..06, CP-01..06, IC-01..04 (foundations + interaction).

```
LIVE:
- Shadows: inspect cards/menus/modals. Flag pure-black shadows (DE-01), inconsistent light
  direction (DE-02), and elevation that doesn't scale with importance (DE-03/04).
- Buttons: check affordance (CP-01), emphasis hierarchy & single primary (CP-02), label clarity
  (CP-05), shape/radius consistency (CP-06). Use `agent-browser get box @<ref>` to MEASURE target
  size; flag < 44×44px / 48×48dp (CP-03) and tight spacing between targets (CP-04).
- Icons: icon-only without label/aria-label (IC-01, cross-check snapshot), mixed icon styles
  (IC-02), alignment (IC-03), icon contrast < 3:1 (IC-04).

STATIC (grep):
- Black shadows: rg -n "box-shadow:[^;]*rgba?\(\s*0\s*,\s*0\s*,\s*0" (DE-01; tint the shadow).
- Inconsistent/ad-hoc shadows: rg -n "box-shadow" ; flag values not from an elevation token set (DE-03).
- Tiny targets: rg -n "(height|width|min-height|min-width):\s*([0-3]?[0-9])px" on button/a/[role=button]
  and Tailwind h-* w-* below 11 (44px) (CP-03).
- >1 primary button per view: rg -n "primary" button usages (CP-02).
- Icon-only buttons missing labels: rg -n "<button[^>]*>\s*<(svg|Icon|i )" without aria-label/text (IC-01).
- Mixed icon libraries: rg -n "lucide|heroicons|react-icons|@mui/icons|feather|fontawesome" (IC-02).
```

---

## Agent 5: Feedback & States + Motion/Microinteractions (Dimensions 6, 7)

Criteria: FB-01..09, MO-01..07 (criteria-interaction.md).

```
LIVE:
- Trigger/observe interactive elements (where safe): confirm hover, focus, active, disabled
  states exist (FB-02) and focus is visible (FB-03). Note missing loading/empty/error/success
  feedback (FB-01, FB-04, FB-06, FB-07, FB-09).
- Observe animations: measure duration (flag > 500ms routine / > 1000ms blocking, MO-02), easing
  (flag linear, MO-03), purpose (MO-04), and that nothing flashes > 3×/s (MO-05).

STATIC (grep):
- Missing state styles: for each interactive component, rg -n ":hover|:focus|:active|:disabled|
  data-\[state" ; flag elements with no hover/active/disabled (FB-02) or focus handling (FB-03).
- No reduced-motion guard: rg -n "@keyframes|animation:|transition:" then rg -n "prefers-reduced-motion" ;
  if animations exist but no reduced-motion block, flag (MO-01 / AC-11).
- Slow durations: rg -n "(transition|animation)[^;]*\b([6-9][0-9]{2}|[0-9]{4,})ms\b|\b([1-9](\.[0-9]+)?)s\b"
  and flag routine UI > 500ms (MO-02).
- Linear easing: rg -n "(transition|animation)[^;]*linear" (MO-03; spinners exempt).
- Loading/empty/error handling: rg -n "isLoading|loading|Spinner|Skeleton|EmptyState|error|toast|
  Snackbar|aria-busy|aria-live" to gauge feedback coverage (FB-01/04/05/06/07/09).
- Destructive without confirm/undo: rg -n "delete|remove|destroy" handlers lacking confirm/undo (FB-08).
```

---

## Agent 6: Accessibility (Dimension 8, WCAG 2.2 AA, cross-cutting)

Criteria: AC-01..12 (criteria-interaction.md).

```
LIVE:
- From snapshot.txt (accessibility tree): flag images without alt text / icon buttons without
  accessible names (AC-01), inputs without associated labels (AC-06), and mismatches between
  visible label and accessible name (AC-10).
- Tab through the page mentally from the snapshot's focus order: flag illogical order or
  unreachable controls (AC-03) and missing/suppressed focus indicators (AC-02).
- Recompute contrast for text and UI (AC-05). Check color-only signaling (AC-04), heading
  structure/landmarks (AC-08), and reduced-motion (AC-11).

STATIC (grep):
- Images without alt: rg -n "<img(?![^>]*\balt=)" (AC-01).
- Icon buttons without names: rg -n "<button(?![^>]*aria-label)[^>]*>\s*<(svg|Icon)" (AC-01).
- Suppressed focus: rg -n "outline:\s*(none|0)\b" then rg -n ":focus-visible" ; flag suppression
  without a visible replacement (AC-02).
- Inputs without labels: rg -n "<input|<select|<textarea" and cross-check for <label for>/aria-label/
  aria-labelledby; flag placeholder-only labeling (AC-06).
- Non-semantic controls: rg -n "<div[^>]*onClick|<span[^>]*onClick" without role/tabindex (AC-03/08).
- Heading structure: rg -n "<h[1-6]" ; flag multiple <h1> or skipped levels (AC-08).
- Color-only state: rg -n "color:\s*(red|green)|text-red-|text-green-" used as the sole status cue (AC-04).
- Reduced motion: rg -n "prefers-reduced-motion" presence vs animation usage (AC-11).
- Drag-only interactions: rg -n "onDrag|draggable|dnd" lacking a pointer alternative (AC-12).
```

---

## Notes on grep portability

- Patterns are written for ripgrep (`rg`); they also work with `Grep`. PCRE look-arounds
  (`(?!…)`) require `rg -P` / Grep's default PCRE2.
- Always **Read** each match to confirm context before reporting: grep finds candidates,
  not confirmed findings.
- Prefer the project's token source of truth (discovered in Phase 1) when judging "hardcoded
  vs tokenized" criteria (CO-02, DE-03, LY-02).
