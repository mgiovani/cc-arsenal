# Design Review: Report Templates

Two templates: a **live** report (`design-report-live.md`) and a **static** report
(`design-report-static.md`). They share structure; the difference is the evidence type
(screenshot region + DOM ref vs. file:line) and the header metadata.

Every finding MUST have: criterion ID, evidence, measured value (where applicable),
citation, severity, and a concrete fix. No placeholder text.

---

## Live Report Template

```markdown
# Design Review Report: Live

**Target URL**: <url>
**Viewport(s)**: <e.g., 1440×900 desktop, 390×844 mobile>
**Date**: YYYY-MM-DD
**Captured artifacts**: page.png, snapshot.txt
**Dimensions audited**: <list / all 8>
**Total findings**: N

## Executive Summary

[2–3 sentences on overall design quality and the most impactful issues.]

### Severity Breakdown
- **Critical**: N
- **High**: N
- **Medium**: N
- **Low**: N

### Dimension Scores (applicable-only)
| Dimension | Score | Applicable criteria | Passed | Notes |
|-----------|-------|---------------------|--------|-------|
| 1. Visual Hierarchy & Layout | X/Y | Y | X | |
| 2. Typography | X/Y | Y | X | |
| 3. Color & Theming | X/Y | Y | X | |
| 4. Depth & Elevation | X/Y | Y | X | |
| 5. Components & Affordance | X/Y | Y | X | |
| 6. Feedback & States | X/Y | Y | X | |
| 7. Motion & Microinteractions | X/Y | Y | X | |
| 8. Accessibility (WCAG 2.2 AA) | X/Y | Y | X | |

> Dimensions that could not be observed are marked "N/A" and excluded from scoring.

## Findings by Dimension

### Dimension 3: Color & Theming (N findings)

#### Finding: Body text fails AA contrast
- **Criterion**: CO-06 (also AC-05)
- **Severity**: High
- **Evidence**: Hero subheading, "top-center" region, DOM ref `@e7` (snapshot.txt)
- **Measured value**: contrast 3.1:1 (text #8A8A8A on #FFFFFF)
- **Citation**: WCAG 2.2 SC 1.4.3 (AA): normal text requires ≥ 4.5:1
- **Description**: The subheading grey on white reads at 3.1:1, below the 4.5:1 AA threshold.
- **Fix**:
  1. Darken text to ≥ #595959 (≥ 4.5:1 on white).
  2. Or increase size to ≥ 24px to qualify for the 3:1 large-text threshold.
  3. Tokenize as `--text-secondary` with a verified-contrast value.

[Repeat per finding, grouped by dimension...]

## What Was NOT Checked

- [Pages/states/viewports not captured, e.g., authenticated areas, modals, error states]
- [Dimensions marked N/A and why]
- [Dynamic behaviors not exercised]

## Prioritized Recommendations
### Immediate (Critical/High)
1. [Finding ref]: [action]
### Short-term (Medium)
1. [Finding ref]: [action]
### Polish (Low)
1. [Finding ref]: [action]

## References
- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- Material Design 3: https://m3.material.io/
- Apple HIG: https://developer.apple.com/design/human-interface-guidelines
- Nielsen Norman Group: https://www.nngroup.com/articles/
- Refactoring UI: https://www.refactoringui.com/
- Laws of UX: https://lawsofux.com/
```

---

## Static Report Template

Identical to the live report with these header/evidence differences:

```markdown
# Design Review Report: Static

**Scope**: [PR #123 | Commit abc123 | Entire Codebase | <path>]
**Date**: YYYY-MM-DD
**Design system**: <detected in Phase 1, e.g., Tailwind + shadcn/ui; tokens in tailwind.config.ts>
**Files reviewed**: N  (with issues: M)
**Dimensions audited**: <list / all 8>
**Total findings**: N

## Executive Summary
[...]
### Severity Breakdown / ### Dimension Scores
[same tables as live]

## Findings by Dimension

### Dimension 8: Accessibility (N findings)

#### Finding: Focus outline suppressed without replacement
- **Criterion**: AC-02
- **Severity**: High
- **Evidence**: `src/components/Button.css:42`
  ```css
  button:focus { outline: none; }   /* no :focus-visible replacement */
  ```
- **Measured value**: 0 visible focus indicator
- **Citation**: WCAG 2.2 SC 2.4.7 Focus Visible; SC 2.4.11 Focus Not Obscured
- **Description**: Focus outline is removed globally with no `:focus-visible` style, leaving
  keyboard users with no visible focus.
- **Fix**:
  1. Add `button:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }`.
  2. Ensure the indicator meets ≥ 3:1 non-text contrast (SC 1.4.11).

[Repeat per finding, grouped by dimension...]

## What Was NOT Checked
- [Runtime-only states not visible in source]
- [Dimensions/criteria not assessable statically, e.g., live contrast on dynamic content]
- [Files outside scope]

## Prioritized Recommendations
[same structure as live]

## Design Tooling Recommendations
Based on this analysis, consider:
- **a11y linting**: eslint-plugin-jsx-a11y, axe-core / @axe-core/playwright
- **Contrast/CI**: pa11y-ci, Lighthouse CI, Storybook a11y addon
- **Design tokens**: consolidate hardcoded colors/spacing/shadows into a token source of truth
- **Reduced motion**: add a global `@media (prefers-reduced-motion: reduce)` guard

## References
[same as live]
```

---

## Scoring rule (applicable-only)

For each dimension: `score = passed_applicable_criteria / total_applicable_criteria`.
- A criterion is "applicable" only if the target contains the relevant surface (e.g., DM-*
  applies only if a dark theme exists; MO-* only if there's animation).
- Never count non-applicable criteria as failures.
- If an entire dimension is non-observable, mark it **N/A** and exclude it from the average.
- Report an overall score as the mean of applicable dimension scores, and state how many
  dimensions were N/A.

## Note on thresholds

Numeric thresholds cited in findings (spacing scale, contrast ratios, target sizes, animation
durations/easing in MO-01..07) are the criteria file's defaults, not hard limits from the
target's own design system. If the project defines its own tokens (e.g., a documented 300ms
transition standard, a different spacing base), prefer those over the default and say so in
the finding.
