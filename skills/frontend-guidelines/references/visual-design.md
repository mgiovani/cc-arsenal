# Visual Design

## Contents

- [The owner's default](#the-owners-default)
- [Layout checks](#layout-checks)
- [Type and color checks](#type-and-color-checks)
- [Data screens](#data-screens)
- [Other aesthetics](#other-aesthetics)
- [How to judge it](#how-to-judge-it)

## The owner's default

The design sources you may have seen disagree on taste: minimal against rich, shadow against flat, gradient against none. Do not average them. In the owner's projects the choice is the same, and it is the default when the project is silent:

- Density over decoration. An operator scans many rows, so the screen shows work, not ornament.
- Flat at rest. Surfaces separate by a step in tone and a hairline. Shadows belong to floating layers.
- One type family, two weights, four sizes. Hierarchy comes from size, spacing and position.
- Color is scarce and carries meaning. The brand itself can be unhued, with the primary action a plain filled control.
- No gradients, no glass as decoration, no stock photography. The product's own screens are the imagery.

Where the project's DESIGN.md says something else, it wins, and the checks below still apply with its values. A restrained design is not automatically a good one: restraint needs a distinct voice, or it reads as a template.

## Layout checks

Each check names the failure and why it matters.

- Squint test. Blur the screen. The primary element, the secondary element and the main groups should still appear in that order. If they do not, hierarchy is carried by decoration.
- Group by proximity first. Add a container or divider only when spacing and alignment cannot do the job. A card nested in a card for layout alone is noise.
- One dominant element per screen. A confident headline followed by section headings nearly as large flattens the hierarchy.
- Skeleton test. Strip the copy from a section. If the structure no longer says what the section is for, the boldness was in the words.
- Rhythm needs contrast between tight and generous intervals. Give a heading more space above than below.
- One primary action per decision point, with secondary actions clearly weaker and the rest in a menu.
- Pick the container width once and use it across pages. Widths that differ per page read as drift.
- Responsive means restructuring: reorder, collapse, reflow or reveal. Shrinking everything in proportion is not a responsive layout. Choose breakpoints where the content breaks, starting narrow.
- Density follows frequency of use and decision complexity. A dense table can run wide, and prose cannot.
- Repeated cards are not automatically equivalent. Check that the structure fits the content before you repeat it.

## Type and color checks

- Each role (display, heading, body, metadata, label) is recognizable at a glance. Adjacent sizes or weights too close together cannot carry different jobs.
- Emphasis comes from weight or size. Gradient or colored emphasis inside a heading is a tell.
- Paragraph rhythm comes from spacing or a first-line indent, never both.
- Color roles stay locked. Brand marks the frame, titles and focus. Action fills controls. Danger marks failure and irreversible actions. A role used for a second meaning stops communicating the first.
- A status color is spent on one state. If danger appears on a healthy screen, it no longer means danger.
- On a dark surface, blend a raster with `lighten`, not `screen`. Ship it re-encoded (WebP plus a fallback), not as the master file.

## Data screens

- Color belongs on data, not chrome. Most of a data screen's pixels are neutral.
- A KPI is a number set in type, not a tile with an icon in a tinted circle. Values run roughly 16 to 40px, and one answer figure may be larger than its siblings.
- Right-align numbers in tabular figures and show a sign on every change. Fix the decimals per metric.
- Match the chart to the question: lines for change over time, bars for a period or a ranking, a thin ring only for a share of five parts or fewer, a progress bar for a target. Keep the chart plain: few gridlines, no y-axis line, no legend for a single series, one hue.
- Annotate the event behind a spike with a thin marker and a short label.
- Totals sum the values as printed, and every relative figure names its baseline in the same phrase.
- A surface takes a border or a shadow, never both.

## Other aesthetics

A brief may ask for an editorial, expressive or marketing look. The surface mode decides how far the visual world reaches.

- Operate surfaces (tools, dashboards) lend only type, palette, density and one signature move. The world never supplies the layout, navigation or controls.
- Read surfaces let the frame carry the world, with a calm reading column inside it.
- Persuade and experience surfaces let the world carry structure, but the parts still work as parts: navigation reads as navigation, text on a painted surface stays legible, and the primary action is unmistakable.

Even then, run the anti-slop checks. A rich design passes them by making decisions, not by avoiding them.

When the project asks for design options, give two to four that really differ and let the user choose. Otherwise recommend one.

## How to judge it

Judge rendered pixels, not source. Capture at about 390 and 1440 pixels wide, settle animations first, and confirm the capture is not blank or half-loaded. Compare against the approved reference when one exists. Budget about two visual rounds, batching fixes between looks, and do not certify your own patch by describing it: only a fresh capture counts as evidence.
