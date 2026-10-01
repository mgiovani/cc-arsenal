---
name: project-illustrator
description: Create or refine a cohesive visual identity for a software project through mascots, logos, README heroes, social cards, circular thumbnails, and supporting illustrations. Use when project artwork must share one recognizable character, palette, composition language, and production-quality finish. Not for architecture or flow diagrams.
metadata:
  summary: "A cohesive art system for a project: mascot, heroes, social cards and thumbnails with one character"
  author: mgiovani
  version: 1.0.0
---

# Project Illustrator

Build a project art system that stays recognizable at every size. A tiny avatar has to read as clearly as a wide README hero, and so does whatever illustration follows later. Base every decision on the product and its existing identity rather than on generic technology imagery.

## 1. Discover the identity

Inspect the target repository before writing a prompt:

- Read the README and product copy to learn the problem, mechanism, audience, and tone.
- Search `assets/`, `public/`, `static/`, documentation, social cards, favicons, and app icons for existing brand material.
- Inspect the actual candidates. Do not treat a framework or template icon as project branding.
- Record the current output paths, dimensions, formats, and every place the artwork is referenced.

If the project already has a logo or mascot, preserve its defining silhouette, anatomy, colors, and personality. Improve execution and consistency without replacing its identity.

If it has no identity, turn the product's mechanism into a character or visual action. Prefer a specific idea that explains the project over a mascot holding unrelated developer props.

Read [references/art-direction.md](references/art-direction.md) for the default visual language, asset specifications, and review checklist.

## 2. Establish one canonical mascot

When no mascot has been approved, generate three clearly different high-resolution concepts. Vary the central metaphor, silhouette, or staging while keeping the same art direction. Do not produce superficial color swaps.

Keep each concept:

- square and at least 1024px;
- readable inside a circular crop;
- centered with generous breathing room;
- limited to one clear action or idea;
- free of labels, slogans, mock UI, and decorative clutter.

Show the three options together at a useful review size and name them plainly: Option 1, Option 2, and Option 3. Pause for the user's selection before creating dependent heroes or illustration sets. The selection is a creative dependency, not a permission gate.

When the user supplies or selects an image, treat it as the canonical character reference. Use image editing or reference-image generation for every later asset so proportions and facial features do not drift.

## 3. Extend the selected identity

Generate the requested hero, social card, thumbnail, or supporting scene from the canonical mascot.

For a hero:

- use a spacious 3:1 composition by default, with text on the left and the mascot scene on the right;
- keep the project name dominant and the subline visibly smaller;
- keep a short subline on one line when the canvas has room;
- omit skill counts, version numbers, star counts, and other facts that become stale unless the user explicitly requests them;
- ground authority claims in supplied facts and use direct, human language rather than hype;
- match the typography, scale, margins, and visual rhythm of an approved sibling hero when the user wants a series.

Prefer composing exact title and subline text as an editable, deterministic text layer after generating the illustration. If text must be baked into the generated image, transcribe it exactly and reject misspellings, broken words, awkward line breaks, and inconsistent letterforms.

For supporting illustrations, keep the same character model and show one product-relevant action per image. Reuse visual motifs deliberately; do not paste the same pose into every scene.

## 4. Generate at master size

Use the available raster image generator. Use the `codex-imagegen` skill (Codex `gpt-6-sol` + GPT Image 2.5 Sunburst `gpt-image-2.5-sunburst`) via a skill tool where available, otherwise apply its generation and pixel-inspection procedure inline. The user's request to generate artwork authorizes the initial concept batch; ask only when a real provider cost or unavailable credential remains unresolved.

Generate and retain large masters before deriving smaller files:

- mascot or logo master: square, at least 1024px;
- hero master: 3:1, preferably at least 2160×720;
- social card: derive at the platform's exact aspect ratio;
- circular thumbnail: derive from the square master, never from the hero.

Keep approved masters and earlier options available. Do not enlarge a small thumbnail and call it a master.

## 5. Inspect and repair

Open every output and inspect the pixels before integrating it. Check identity, anatomy, object function, typography, composition, and target-size readability using the checklist in the art-direction reference.

When the user likes a composition and asks for a local correction, edit that image and preserve everything else. Do not substitute a new concept. Examples include reducing texture on one side, fixing a hand, removing one slogan, or changing only the subline size.

Reject and repair an asset when:

- the mascot's defining anatomy or silhouette changed;
- limbs, props, openings, or contact points do not work physically;
- texture obscures the face or small-size readability;
- the circular crop removes an important feature;
- the hero contains stale facts, invented claims, malformed text, or generic filler decoration.

## 6. Integrate and verify

Write final assets to the repository's established locations and update only real references. Preserve expected filenames when replacing existing artwork unless the user requested a rename.

Derive the fixed-size crops with the script rather than by hand. It needs [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`) and installs Pillow itself:

```bash
uv run <skill-dir>/scripts/derive_assets.py <master> <out-dir> [--focus 0.5,0.5] [--only thumbnail avatar]
```

It writes PNGs: `social-card` 1200×630, `thumbnail` 256×256 (circular, transparent corners), `avatar` 512×512, `favicon-32` and `apple-touch-icon` 180×180. Crops are centered unless `--focus X,Y` (fractions of the master) moves them. Derive the thumbnail, avatar and icons from the square mascot master and the social card from the hero master. If it prints `WARNING ... upscaled` and exits 1, the master is too small: regenerate a larger one instead of shipping the upscale. Without `uv`, crop and resize to the same sizes with any image tool.

Then check the outputs. Copy this list and tick it:

```
- [ ] Open every derived file and confirm the pixel size matches the list above
- [ ] Social card: title and mascot survive the crop; if not, rerun with --focus
- [ ] Thumbnail: face and defining feature are inside the circle, corners are transparent
- [ ] Favicon and apple-touch icon: silhouette still reads at 32px
```

If a check fails, adjust `--focus` or repair the master and rerun the script, at most 3 rounds, then report what still fails.

Convert to web formats such as WebP from the derived PNGs without deleting the master. Inspect the integrated result at its real display sizes, including the smallest thumbnail and responsive hero crop. Check both light and dark surfaces when the project supports them.

Report:

- the selected concept and the identity features preserved;
- master and derived asset paths with dimensions;
- where each asset is used;
- the visual checks performed and any remaining limitation.
