---
name: review-design
description: Perform a comprehensive UX/UI/design quality audit of a live URL or a static
  codebase, mapped to authoritative standards (WCAG 2.2 AA, Material Design 3, Apple
  HIG, Nielsen Norman Group, Refactoring UI, Laws of UX). This skill should be used
  when a user wants to review design quality, audit UX/UI, check visual hierarchy,
  typography, color, accessibility, components, or interaction design. Analysis only -
  identifies issues without modifying code.
metadata:
  author: mgiovani
  version: 1.0.0
disable-model-invocation: true
argument-hint: '[url|pr_number|commit_sha|--all] [--scope dimension] [--mode live|static|both]'
allowed-tools: Read, Grep, Glob, Bash(git *), Bash(gh *), Bash(agent-browser *), Task, TodoWrite, AskUserQuestion
context: fork
agent: general-purpose
---

# Design Review

Comprehensive UX/UI/design quality analysis across **8 audit dimensions**, each mapped to
authoritative standards. This skill performs **analysis only** - it identifies design
issues, explains findings against a cited criterion, and suggests fix approaches without
making code changes.

It supports two input modes:

- **Live mode** — audits a running URL via the `agent-browser` CLI (screenshots + DOM/accessibility snapshot).
- **Static mode** — audits a codebase (CSS/components/design tokens) via Grep.

When both a URL and a codebase target are supplied, it runs both and emits **two separate reports**.

## Audit Taxonomy (8 Dimensions)

| # | Dimension | Key Standards |
|---|-----------|---------------|
| 1 | Visual Hierarchy & Layout | NN/g, Refactoring UI, Laws of UX, MD3 8pt grid |
| 2 | Typography | Butterick, Refactoring UI, MD3, Apple HIG |
| 3 | Color & Theming (incl. Dark Mode) | MD3 color roles, 60-30-10, WCAG 1.4.1/1.4.3 |
| 4 | Depth & Elevation (Shadows) | MD3 elevation, Refactoring UI, Josh Comeau |
| 5 | Components & Affordance (Buttons/Icons) | MD3 buttons/icons, Apple HIG, NN/g |
| 6 | Feedback & States | NN/g visibility-of-status, MD3 state layers |
| 7 | Motion & Microinteractions | NN/g animation, Laws of UX (Doherty), MD3 motion |
| 8 | Accessibility (cross-cutting) | WCAG 2.2 AA |

Measurable criteria for dimensions 1–4 are in [references/criteria-foundations.md](references/criteria-foundations.md);
dimensions 5–8 are in [references/criteria-interaction.md](references/criteria-interaction.md).

## Anti-Hallucination Guidelines

**CRITICAL**: Design reviews must be based on ACTUAL evidence, never assumptions:

1. **Observe before claiming** - Never report an issue without reading the code (static) or viewing the screenshot/snapshot (live)
2. **Evidence-based findings** - Every finding cites a file path + line number (static) OR a screenshot region + DOM ref (live)
3. **Cite a criterion** - Every finding maps to a criterion ID and an authoritative citation (WCAG SC, MD3 spec, etc.)
4. **Measure, don't estimate** - Report actual values (contrast ratio, px size, ms duration), not guesses
5. **Applicable-only scoring** - Only score dimensions that apply to the target; never penalize what cannot be observed
6. **State what was NOT checked** - Every report ends with an explicit coverage gap section
7. **No invented standards** - Only reference real WCAG SCs, MD3 specs, and HIG guidance

## Review Workflow

### Phase 0: Parse Arguments & Resolve Mode

Parse arguments to determine target and mode:

```
Arguments:
- <url>: A live URL to audit (http/https) → live mode
- <pr_number>: Files changed in a PR (e.g., "123", "#123") → static mode
- <commit_sha>: Files changed in a commit (e.g., "abc123") → static mode
- "--all" or a path or no args: Entire codebase → static mode
- "--mode [live|static|both]": Force a mode
- "--scope [dimension]": Focus on one dimension (e.g., typography, color, accessibility)
```

**Mode resolution:**
- A URL argument (or `--mode live`) → **live** audit.
- A PR / commit / `--all` / path (or `--mode static`) → **static** audit.
- Both a URL and a codebase target present (or `--mode both`) → run **both**, emit two reports.

For static PR/commit scope, get changed files:
```bash
# For PR
gh pr view <pr_number> --json files --jq '.files[].path'
# For commit
git diff-tree --no-commit-id --name-only -r <commit_sha>
```

### Phase 1: Discovery

Use an Explore agent (model: `haiku`) to detect the design system and tooling:

```
Use Task tool with Explore agent (model: haiku):
- prompt: "Discover the project's design system and front-end stack:
    1. Detect CSS approach: Tailwind, CSS Modules, styled-components, vanilla CSS, Sass
    2. Detect component/design system: Material UI, Chakra, Radix, shadcn/ui, Ant Design, custom
    3. Find design tokens: tailwind.config.*, theme files, CSS custom properties (:root { --* }), tokens.json
    4. Find existing a11y tooling: eslint-plugin-jsx-a11y, axe, pa11y, Storybook a11y addon
    5. Detect dark-mode support: prefers-color-scheme, .dark class, data-theme
    6. List the key UI directories (components/, styles/, app/, pages/)
    Return: a stack + design-system summary with the token source of truth."
- subagent_type: "Explore"
```

**For live mode**, confirm the URL is reachable and `agent-browser` is installed:
```bash
agent-browser --version || echo "agent-browser not installed (npm install -g agent-browser)"
```
If `agent-browser` is missing, tell the user how to install it (`npm install -g agent-browser && agent-browser install`) and offer to fall back to static mode.

### Phase 2: Initialize Progress Tracking

Use TodoWrite to track progress across the 8 dimensions plus capture, consolidation, and report generation. One todo per dimension.

### Phase 3: Capture, then Spawn Parallel Audit Agents

**Live mode — capture first** (the agents analyze these artifacts):
```bash
mkdir -p /tmp/review-design
agent-browser open <url>
agent-browser snapshot -i > /tmp/review-design/snapshot.txt   # interactive elements + a11y tree
agent-browser screenshot /tmp/review-design/page.png --full     # full-page screenshot
# Optional, for inspected elements:
# agent-browser get styles @<ref>   # computed CSS
# agent-browser get box @<ref>      # bounding box (for touch-target size)
```
Capture additional viewports/pages if the user names them. Always `agent-browser close` when done.

**Then spawn 6 parallel Explore agents** (model: `sonnet`) covering the 8 dimensions. For the full per-agent prompts (live screenshot/snapshot analysis AND static grep patterns), see [references/agent-prompts.md](references/agent-prompts.md).

**Agent assignments:**
- **Agent 1**: Visual Hierarchy + Layout & Spacing (Dimension 1)
- **Agent 2**: Typography (Dimension 2)
- **Agent 3**: Color + Dark Mode (Dimension 3)
- **Agent 4**: Depth/Shadows + Components/Affordance (Dimensions 4, 5)
- **Agent 5**: Feedback & States + Motion/Microinteractions (Dimensions 6, 7)
- **Agent 6**: Accessibility — WCAG 2.2 AA (Dimension 8, cross-cutting)

Each agent must:
1. Read the relevant criteria reference for its dimensions (criteria-foundations.md or criteria-interaction.md)
2. **Live**: visually analyze the screenshot and cross-reference the DOM/a11y snapshot
   **Static**: Grep CSS/components/tokens for measurable failures, then Read each match to verify
3. Record the **measured value** (contrast ratio, px, ms, dp) as evidence
4. Map each finding to a **criterion ID + citation** (WCAG SC / MD3 / HIG / NN/g)
5. Classify severity (Critical/High/Medium/Low)
6. Provide a concrete fix (2-3 approaches with the target value)

### Phase 4: Consolidate & Analyze Findings

After all agents complete:

1. **Collect** findings from the 6 agents
2. **Deduplicate** across agents (same element/criterion = one finding)
3. **Prioritize by severity**:
   - **Critical**: WCAG AA failure blocking use (contrast < 3:1 on text, no keyboard focus, missing form labels), unusable touch targets
   - **High**: WCAG AA contrast failures (< 4.5:1 body text), missing focus-visible, no reduced-motion support, broken hierarchy
   - **Medium**: Off-grid spacing, un-tinted shadows, weak typographic scale, missing hover/active states
   - **Low**: Polish — minor inconsistency, sub-optimal line length, icon-label spacing
4. **Map to dimension**: Group findings under the 8 dimensions
5. **Applicable-only score**: For each dimension that applies, score = passed criteria / applicable criteria. Skip dimensions that cannot be observed and say so.
6. **Statistics**: total findings, by severity, by dimension; elements/files reviewed vs. those with issues

### Phase 5: Generate Report(s)

Generate a markdown report per the template in [references/report-template.md](references/report-template.md).

- Live audit → `design-report-live.md`
- Static audit → `design-report-static.md`
- Both modes → produce **both** files.

### Phase 6: Verification & Quality Gate

Before presenting, verify every finding has:
1. Evidence — `file:line` (static) or screenshot region + DOM ref (live)
2. A measured value where one applies (ratio / px / ms / dp)
3. A criterion ID + authoritative citation
4. A concrete fix with the target value
5. A justified severity
6. No duplicates, no placeholder text ("TODO", "[example]", "lorem")
7. An explicit "What Was NOT Checked" section
8. Applicable-only scoring (no penalty for unobservable dimensions)

## Usage

```bash
# Live audit of a running site
review-design --url https://example.com
review-design https://example.com

# Static audit of the codebase
review-design --all --mode static
review-design 123                  # PR #123 changed files
review-design abc123def            # a commit

# Both: live + static (two reports)
review-design https://staging.example.com --all --mode both

# Focus a single dimension
review-design --url https://example.com --scope accessibility
review-design --all --scope typography
```

## Scope Options

`--scope` focuses the audit on one dimension: `hierarchy`, `layout`, `typography`,
`color`, `dark-mode`, `depth`, `components`, `feedback`, `motion`, `accessibility`.
If omitted, all 8 dimensions are audited.

## Additional Resources

- [references/criteria-foundations.md](references/criteria-foundations.md) — measurable criteria for dimensions 1–4 (hierarchy, layout, typography, color, depth)
- [references/criteria-interaction.md](references/criteria-interaction.md) — measurable criteria for dimensions 5–8 (components, feedback, motion, accessibility)
- [references/agent-prompts.md](references/agent-prompts.md) — per-agent prompts (live + static) and grep patterns
- [references/report-template.md](references/report-template.md) — live and static report templates

## What This Skill Does

- Audits UX/UI/design quality across 8 standards-mapped dimensions
- Works against a live URL (agent-browser) or a static codebase (grep)
- Measures real values (contrast, sizes, durations) as evidence
- Maps every finding to a criterion ID + authoritative citation
- Produces severity-ranked, fix-oriented report(s)

## What This Skill Does NOT Do

- Does not modify any code or design files
- Does not auto-fix issues or commit changes
- Does not run a full automated a11y scanner (axe/pa11y) — it reasons from evidence
- Does not evaluate native mobile (SwiftUI/Compose/Flutter) static patterns (web-first; future extension)
- Does not guarantee 100% issue detection

## Limitations

- **Heuristic + measured**: combines tool measurements with expert heuristics; some judgment calls remain
- **Live mode needs a reachable URL** and the `agent-browser` CLI installed
- **Static mode is pattern-based**: dynamic/runtime states may be missed
- **Screenshot analysis** depends on render fidelity at the captured viewport
- **Expert review recommended** for high-stakes or regulated interfaces

## Standards References

- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [Material Design 3](https://m3.material.io/)
- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines)
- [Nielsen Norman Group](https://www.nngroup.com/articles/)
- [Refactoring UI](https://www.refactoringui.com/)
- [Laws of UX](https://lawsofux.com/)
