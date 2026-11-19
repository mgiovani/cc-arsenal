# Anti-slop

## Contents

- [How to use these checks](#how-to-use-these-checks)
- [Decoration](#decoration)
- [Structure](#structure)
- [Type, icons and imagery](#type-icons-and-imagery)
- [Content](#content)
- [Motion](#motion)
- [Gates](#gates)

## How to use these checks

Each line says what makes a screen read as templated and why. A tell is a prompt to decide, not a ban. It passes when the project's tokens or brief call for it and you can say why. A design that could belong to any other product in its category has not been decided.

Stripping tells without putting a decision in their place leaves an empty page with good manners. Fill the space with the product's own content, a larger type step or a real picture.

## Decoration

This reads as templated when:

- Text carries a gradient fill. Emphasis comes from weight or size, and a gradient makes contrast depend on the stop under each letter.
- A purple to blue gradient or a default violet accent leads the page. Those are what app builders ship out of the box, so the page says nothing about this product. Use the project's brand token.
- Blur or glass decorates a surface. Blur is fine when it does a bounded job, such as a modal backdrop or a sticky bar over scrolling content. Test text contrast over the real backdrop.
- A card stacks several emphasis devices: a heavy shadow, a hover scale and a saturated border. Give each element one emphasis.
- A colored border thicker than 1px runs down one side of a card, callout or alert. It is the most recognizable template stripe.
- A hard offset shadow appears outside a neobrutalist brief, or a zero-offset colored glow stands in for depth.
- Imitation material is drawn in CSS (bevel, emboss, stamped metal) for a surface the page never renders.
- A hover lift or shadow ramp sits on every card. It signals clickability on cards that do nothing.
- A sparkline, progress ring or rounded soft-shadow box stands in for real content.
- One medium radius sits on every element. Pick square or round once, in tokens.

## Structure

This reads as templated when:

- Three or more identical cards each show an icon, a heading and a line of text. Repeated modules belong to archives (a menu, a schedule), not to a feature argument.
- A KPI is a tile with a number, a small label and a green percentage pill. Set key figures as type.
- A small label sits above every heading as pure decoration. Owner's projects use an eyebrow where it carries information, such as state or risk beside a warning icon, so it passes when it does that job and fails when it only labels the heading.
- Sections are numbered 01, 02, 03 though the sequence carries no information.
- A page runs hero, logo wall, features, testimonial, pricing and call to action in stock order. Let the argument set the order.
- One layout shape repeats in every section.
- A dashboard opens with a welcome banner, a tinted sidebar with a colored active pill, rainbow chart palettes, zebra tables under uppercase headers and pagination under a short list.
- Card within card exists only to space things.
- A custom control rebuilds a platform one for flavor: odd scrollbars, bespoke switches, non-standard dialogs.

## Type, icons and imagery

This reads as templated when:

- The face was never chosen. A font is a decision recorded in tokens, so use the project's face and do not swap it for a favorite. Do not add a second display face to label or button text.
- Monospace is a costume for "technical". It belongs to code, data and measurement.
- Icons come from two sets, appear as emoji or Unicode glyphs, or mix filled and outline at one level.
- A geometric mask or a polygon `clip-path` approximates a photograph's edge. Derive a real cutout.
- A gray box or gradient fills the place where a picture or a real name belongs.
- Tiny tracked capitals, hairline rules, crosshairs and coordinates act as ornament on a product screen.
- A centered stack of headline, paragraph and two buttons sits over a screenshot.

## Content

This reads as templated when:

- The copy uses genre verbs, a negation then correction shape ("not X, but Y"), a three-word tricolon or a headline that needs a colon to name the product.
- Placeholder text ships: lorem ipsum, bracketed fields, "Acme", "John Doe", or `alt="image"`. Decorative images take `alt=""`.
- Proof is invented: customers, logos, quotes, star ratings or round user counts.
- A middle dot or arrow separates two words in UI text ("Home · Docs"). Use real structure such as a nav list or breadcrumbs.
- A page title is the editor default.
- Promotional filler ("industry-leading", "state-of-the-art") stands where a concrete claim with a number would go.
- Every screen carries the same status chips and badges, so none of them mean anything.

## Motion

This reads as templated when every section fades and rises, one entrance preset runs on every block, a hover lift sits on every card, bounce easing appears on interface elements, or a loop runs with no meaning. See [motion.md](motion.md) for the filter. Content must stay visible when a script fails.

## Gates

- Run the project's detector when it has one (an impeccable or stopslop run over UI strings and styles). It proves nothing banned was found, not that the design is good, so still judge the screenshots.
- Triage each finding one of three ways: fix it, add the narrowest ignore with the evidence in its reason, or ask the user once. Ignore one rule for one value in one file before a whole rule or a whole file.
- Keep ignores in the committed config. Generated and vendored files are excluded, and material you may not rewrite is excluded with a reason. Inconvenient material is not.
