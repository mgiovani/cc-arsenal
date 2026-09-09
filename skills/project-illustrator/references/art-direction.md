# Art Direction

Use this reference when defining prompts, reviewing options, or deriving final assets.

## Approved visual references

Inspect these images before generating when the user asks for the established CC Arsenal project-art style. Supply the most relevant references to the image generator. Use them for finish, palette discipline, proportions, spacing, and typography; do not copy one project's mascot into another.

- [Water Gate mascot](visuals/water-gate-mascot.webp) and [hero](visuals/water-gate-hero.webp): product mechanism expressed as one clear action, blue identity color within the shared print treatment.
- [cc-wellness mascot](visuals/cc-wellness-mascot.webp) and [hero](visuals/cc-wellness-hero.webp): quiet character staging, generous space, restrained palette, and clean 3:1 hierarchy.
- [StopSlop mascot](visuals/stopslop-mascot.webp) and [hero](visuals/stopslop-hero.webp): project-specific robot, purposeful action, and a direct one-line promise without borrowed product comparisons.
- [AI Arsenal mascot](visuals/ai-arsenal-mascot.webp) and [hero](visuals/ai-arsenal-hero.webp): recognizable multi-tool silhouette, stable hero copy without counts, and a smaller one-line authority subline.

These examples define a family resemblance rather than a fixed character. Preserve a target project's own accent color and mascot when it already has one.

## Default visual language

Use this treatment when the project has no stronger established style:

- warm cream paper background;
- near-black outlines and typography;
- warm gray secondary objects;
- one project-specific accent color, with restrained magenta as a useful shared accent;
- bold, simple silhouettes that survive a 64px circular crop;
- editorial risograph texture: visible grain, controlled halftones, and subtle ink misregistration;
- clean negative space and one readable action.

Texture should support the print character without making surfaces dirty. Keep faces and focal details quiet. Avoid all-over white speckles, random scratches, glossy 3D rendering, neon gradients, glass panels, floating particles, excessive sparkles, and piles of unrelated interface icons.

The result should feel drawn for this product. A robot, octopus, droplet, animal, or object character must express the product's actual behavior through its shape or action.

## Identity sheet

Before generating dependent assets, state the canonical character in a compact reusable brief:

- silhouette and body proportions;
- exact facial features;
- limbs and allowed anatomy;
- primary, secondary, and accent colors;
- outline weight and texture density;
- temperament and typical poses;
- features that must never change.

Repeat this identity brief in every generation prompt and supply the approved image as a reference whenever the tool supports it.

## Composition specifications

### Square mascot

- Minimum master size: 1024×1024.
- Keep all important features inside the central 72% of the canvas.
- Leave enough outer paper to survive a circular mask.
- Prefer a single silhouette with at most one meaningful prop.
- Preview at 64×64 before approval.

### README hero

- Default ratio: 3:1, preferably 2160×720 or larger.
- Keep approximately half the canvas calm enough for title and subline.
- Use consistent outer margins and align the title and subline to one edge.
- Keep the subline smaller than the title and avoid wrapping a short sentence.
- Keep the mascot large enough to read, but away from likely responsive crop edges.
- Do not bake a count or version into the image unless it is intentionally maintained.

### Social card

- Derive a separate crop for the platform rather than stretching the README hero.
- Preserve safe margins for link-preview cropping.
- Verify title legibility at feed size.

## Prompt ingredients

A useful prompt identifies:

1. The canonical character and invariants.
2. The one action that expresses the product.
3. Canvas ratio and left/right composition.
4. Palette, line, paper, grain, and halftone treatment.
5. Safe area and negative space.
6. Exact text, when text is unavoidable.
7. Explicit exclusions tied to likely failures.

Describe visible choices, not taste labels such as “premium,” “stunning,” or “not AI-looking.”

## Visual review checklist

Inspect the image itself at full size and at delivery size.

- **Identity:** silhouette, colors, face, proportions, and personality match the approved mascot.
- **Anatomy:** every limb attaches once; hands, feet, eyes, and joints have the intended count and placement.
- **Function:** tools can be held; gates hinge; cups contain liquid; openings fit inserted objects; furniture supports its load.
- **Contact:** feet meet the ground, hands meet props, and shadows agree with contact points.
- **Occlusion:** no object passes accidentally through the mascot or another object.
- **Composition:** one focal action, balanced negative space, no accidental tangencies, safe crop margins.
- **Texture:** grain is controlled, focal surfaces remain readable, and distress is not mistaken for extra facial features.
- **Typography:** exact spelling, consistent font treatment, sensible hierarchy, no unwanted line break.
- **Thumbnail:** recognizable at 64px inside a circle.
- **Hero:** readable at desktop width and resilient to the expected responsive crop.

Repair the smallest possible region when the composition is already approved.
