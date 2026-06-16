# Design Review — Foundations Criteria (Dimensions 1–4)

Measurable, citation-backed audit criteria for the foundational visual dimensions.
Each criterion has a stable **ID** (used in findings), a **measurable test**, and a
**citation**. Agents 1–4 load this file before auditing.

Severity guidance per criterion is a default; agents may adjust based on context
(a 4.4:1 body-text contrast is High; a 4.4:1 on a decorative caption is lower impact).

---

## Dimension 1 — Visual Hierarchy & Layout

### Hierarchy

- **VH-01 — Single clear focal point per view.** Each primary view has one dominant
  element (largest/highest-contrast). More than one competing "loudest" element is a
  finding. *NN/g: visual hierarchy; Refactoring UI "establish a hierarchy".* Severity: Medium.
- **VH-02 — De-emphasize with weight/color, not just size.** Secondary text uses lighter
  weight or muted color rather than only smaller size. Pure size-only de-emphasis is a
  finding. *Refactoring UI "emphasize by de-emphasizing".* Severity: Low.
- **VH-03 — One primary action per view.** At most one high-emphasis (filled) button per
  view/section. Two or more primary buttons competing is a finding. *MD3 buttons;
  NN/g action hierarchy.* Severity: Medium.
- **VH-04 — Size/contrast steps are perceptible.** Adjacent hierarchy levels differ enough
  to read as distinct (e.g., heading vs. body ≥ 1.25× size or a clear weight jump).
  *Refactoring UI type scale.* Severity: Low.

### Layout, Grid & Spacing

- **LY-01 — Spacing on a 4px/8px base scale.** Margins/padding/gaps are multiples of 4
  (ideally 8): 4, 8, 12, 16, 24, 32, 48, 64. Arbitrary values (e.g., 7px, 13px, 25px) are
  findings. *MD3 8dp grid; Refactoring UI spacing system.* Severity: Medium.
- **LY-02 — Consistent spacing scale (not ad-hoc).** The number of distinct spacing values
  is small and systematic. A long tail of one-off values indicates no spacing system.
  *Refactoring UI "define a spacing and sizing system".* Severity: Medium.
- **LY-03 — Line length 45–75 characters.** Body text measure is ~45–75 chars (~66 ideal);
  full-viewport-width paragraphs are a finding. *Butterick; Refactoring UI; ~`max-width: 65ch`.*
  Severity: Medium.
- **LY-04 — Whitespace separates groups (proximity).** Related items are closer than
  unrelated ones; uniform spacing that hides grouping is a finding. *Laws of UX: Law of
  Proximity; Gestalt.* Severity: Medium.
- **LY-05 — Alignment to a consistent grid.** Elements share alignment edges; ragged,
  unaligned blocks are a finding. *Refactoring UI; MD3 layout grid.* Severity: Low.
- **LY-06 — Adequate content density / not cramped.** Touchable rows and text blocks have
  breathing room; visually crowded clusters are a finding. *MD3 density; NN/g.* Severity: Low.

---

## Dimension 2 — Typography

- **TY-01 — Body font size ≥ 16px.** Body copy is ≥ 16px (1rem); < 16px on mobile also
  triggers iOS input zoom. *Refactoring UI; Apple HIG; MD3 body-large 16sp.* Severity: Medium.
- **TY-02 — Line height 1.4–1.6 for body.** Body `line-height` is ~1.5 (1.4–1.6 acceptable);
  tight (< 1.3) or loose (> 1.8) body leading is a finding. *Butterick; WCAG 1.4.12 (≥1.5×);
  Refactoring UI.* Severity: Medium.
- **TY-03 — Limited type scale.** A defined modular scale (e.g., 12/14/16/18/24/30/36/48) is
  used; many near-duplicate sizes (15px, 17px, 19px) indicate no scale. *Refactoring UI;
  MD3 type scale.* Severity: Low.
- **TY-04 — ≤ 2–3 font families.** No more than 2 (occasionally 3) typeface families. More
  is a finding. *Refactoring UI; Butterick.* Severity: Low.
- **TY-05 — Limited weights, with real weight contrast.** A small set of weights; heading vs.
  body has a perceptible weight difference. *Refactoring UI.* Severity: Low.
- **TY-06 — Letter-spacing tuned to size.** Large display text slightly tightened; small
  caps/uppercase slightly loosened. Default tracking on big headings is a finding. *Butterick;
  MD3 tracking.* Severity: Low.
- **TY-07 — Headings tighter line-height than body.** Multi-line headings use ~1.1–1.3, not
  body leading. *Refactoring UI.* Severity: Low.
- **TY-08 — Numeric/relative units, not fixed px for user text where zoom matters.** Prefer
  `rem`/`em` so text scales with user settings; large fixed-`px`-only systems are a finding.
  *WCAG 1.4.4 Resize Text.* Severity: Medium.

---

## Dimension 3 — Color & Theming (incl. Dark Mode)

### Color usage

- **CO-01 — 60-30-10 balance.** A dominant neutral (~60%), secondary (~30%), and a small
  accent (~10%). Accent color flooding the UI is a finding. *Interior-design 60-30-10; MD3
  surface/primary roles.* Severity: Low.
- **CO-02 — Color is tokenized, not hardcoded.** Colors come from tokens/theme variables;
  raw hex/rgb literals scattered across components are a finding. *MD3 color roles; design
  tokens.* Severity: Medium.
- **CO-03 — Semantic color roles.** Success/warning/error/info use consistent, distinguishable
  hues that aren't the only signal (see AC-04). *MD3 color roles; NN/g.* Severity: Low.
- **CO-04 — Saturated colors not used for large areas of text background.** Avoid vibrating
  fully-saturated backgrounds behind text. *Refactoring UI "don't use grey text on colored
  backgrounds"* (use a tinted shade of the bg). Severity: Low.
- **CO-05 — Greys are tinted, not pure neutral, when brand-warm/cool.** Optional polish:
  greys carry a slight hue toward the brand. *Refactoring UI.* Severity: Low.

### Contrast (also enforced under Accessibility)

- **CO-06 — Body text contrast ≥ 4.5:1.** Normal text vs. its background ≥ 4.5:1.
  *WCAG 2.2 SC 1.4.3 (AA).* Severity: High (Critical if < 3:1).
- **CO-07 — Large text contrast ≥ 3:1.** Text ≥ 24px (or ≥ 18.66px bold) ≥ 3:1.
  *WCAG 2.2 SC 1.4.3 (AA).* Severity: High.
- **CO-08 — Non-text/UI contrast ≥ 3:1.** Icons, input borders, focus indicators, and other
  meaningful UI boundaries ≥ 3:1 against adjacent colors. *WCAG 2.2 SC 1.4.11.* Severity: High.

### Dark mode

- **DM-01 — Avoid pure black (#000) surfaces.** Dark theme base is an elevated dark grey
  (e.g., ~#121212), not #000, to reduce halation. *MD3 dark theme; Material dark surface
  #121212.* Severity: Medium.
- **DM-02 — Avoid pure white body text on dark.** Use high-emphasis off-white (~87% opacity
  white) rather than #FFF for large bodies. *MD3 dark theme emphasis (87/60/38%).* Severity: Low.
- **DM-03 — Desaturate accents on dark.** Brand/accent colors are lightened/desaturated for
  dark surfaces to keep ≥ 4.5:1 and reduce vibration. *MD3 dark theme; Material tonal palette.*
  Severity: Medium.
- **DM-04 — Elevation via lighter surface, not just shadow, in dark mode.** Higher surfaces
  get a lighter overlay because shadows read weakly on dark. *MD3 dark elevation overlays.*
  Severity: Low.
- **DM-05 — Contrast holds in both themes.** CO-06/07/08 are met in light AND dark.
  *WCAG 1.4.3 in each theme.* Severity: High.

---

## Dimension 4 — Depth & Elevation (Shadows)

- **DE-01 — Shadows are tinted, not pure black.** `box-shadow` uses a dark tinted color or
  low-alpha that matches the scene, not `rgba(0,0,0,…)` straight black. Pure-black shadows
  read muddy. *Refactoring UI "shadows"; Josh Comeau designing shadows.* Severity: Medium.
- **DE-02 — Consistent light source.** All shadows share one direction (typically offset
  downward, `y` positive, small/zero `x`). Mixed directions are a finding. *Refactoring UI;
  Josh Comeau.* Severity: Low.
- **DE-03 — Elevation scale is systematic.** A small set of elevation levels (e.g., MD3
  levels 0–5) maps to component roles (card < menu < dialog). Ad-hoc shadow values are a
  finding. *MD3 elevation tokens.* Severity: Low.
- **DE-04 — Larger blur + spread for higher elevation; softer = closer.** Higher elements
  cast larger, softer shadows. Tiny harsh shadows on a modal (or huge shadows on a resting
  card) are findings. *Refactoring UI; MD3 elevation.* Severity: Low.
- **DE-05 — Layered shadows for realism (optional).** Two-layer shadows (tight + ambient)
  read more natural than a single shadow. *Josh Comeau; Refactoring UI.* Severity: Low.
- **DE-06 — Elevation not the ONLY affordance.** Interactive elevation changes pair with
  another cue (color/state layer), not shadow alone. *MD3 state layers.* Severity: Low.
