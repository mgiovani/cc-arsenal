# Prompt Engineering for Nano Banana

> Best practices for crafting effective image generation prompts. The core principle is **narrative over keywords** — describe images as a scene or story, not a keyword list.

---

## Core Principle: Narrative Over Keywords

**Weak (keyword list):**
> sunset, mountains, dramatic, 4k

**Strong (narrative):**
> A panoramic view of snow-capped mountain peaks at golden hour, warm amber and rose light painting the ridgelines, a thin layer of mist filling the valley below, shot with a wide-angle lens, deep depth of field, serene and majestic atmosphere.

Narrative prompts give the model compositional context. Keywords leave too much to chance.

---

## Category-Specific Guidance

### Photorealistic Images

**Template:**
> A [subject] [action/state], [camera angle], [lens type] lens, [lighting setup], [depth of field], [atmosphere/mood], [time of day if relevant]

**Camera Angles:**
- Bird's eye / aerial view
- Low angle (looking up — adds power)
- Eye level (natural, relatable)
- Dutch angle (slight tilt — tension, unease)
- Over-the-shoulder (narrative, POV)
- Macro / extreme close-up

**Lens Types:**
- 24mm / wide-angle — expansive environments, architecture
- 35mm — documentary, street photography feel
- 50mm — natural human perspective
- 85mm — portrait compression, flattering faces
- 135mm / telephoto — background compression, isolation
- Macro — extreme detail, insects, textures

**Lighting Setups:**
- Golden hour — warm, elongated shadows, romantic
- Blue hour — cool, atmospheric, twilight
- Overcast — soft, even, no harsh shadows
- Rembrandt lighting — dramatic triangle of light on cheek
- Split lighting — face half in shadow
- Rim / hair lighting — subject outlined against dark background
- Softbox / diffused — commercial photography look
- Hard light / midday sun — high contrast, stark shadows

**Depth of Field:**
- Shallow DoF / bokeh — subject sharp, background blurred (portraits, product shots)
- Deep DoF — everything sharp (landscapes, architecture)
- Selective focus — one element sharp in an otherwise busy scene

**Sparse → Rich Example:**
```
BEFORE: "a coffee cup"
AFTER:  "A ceramic coffee cup with wisps of steam rising, photographed from a
        45-degree overhead angle with a 50mm lens, morning soft light from a
        window on the left creating gentle shadows, shallow depth of field with
        the wooden table surface softly blurred, warm and cozy atmosphere"
```

---

### Stylized / Illustration

**Template:**
> [Subject and scene], [art style], [quality level], [shading approach], [color palette], [mood]

**Art Styles:**
- Watercolor — soft edges, visible brushwork, translucent layers
- Oil painting — rich texture, impasto technique, classical depth
- Gouache — opaque, matte, flat but detailed
- Vector / flat design — clean lines, solid fills, scalable aesthetic
- Pixel art — retro 8-bit or 16-bit, visible pixels
- Line art — clean contours, minimal fill
- Cel-shaded — sharp outline with flat color fills (anime/cartoon)
- Concept art — painterly, dramatic lighting, often dark
- Storybook illustration — whimsical, soft colors, accessible
- Art Nouveau — organic lines, decorative borders, botanical motifs

**Quality Levels:**
- Rough sketch / gestural — loose, exploratory
- Detailed illustration — polished, ready for publication
- Masterpiece / museum quality — exceptional detail and craft

**Shading Approaches:**
- Flat shading — no gradients, clean blocks of color
- Soft gradient — smooth color transitions
- Cross-hatching — parallel lines creating shadow
- Stippling — dots creating texture and value

**Sparse → Rich Example:**
```
BEFORE: "a dragon"
AFTER:  "A friendly young dragon with bright emerald scales, sitting on a mossy
        boulder in an enchanted forest, warm afternoon light filtering through
        giant mushrooms, Studio Ghibli-inspired illustration style, soft
        watercolor washes with detailed ink linework, muted natural colors with
        glowing amber highlights, whimsical and adventurous mood"
```

---

### Text Rendering

> **Always use Nano Banana Pro (`gemini-3-pro-image-preview`) for text-heavy images.** Other models produce inconsistent typography.

**Key Rules:**
1. Put the exact text in quotes within the prompt
2. Describe font style explicitly
3. Describe placement clearly
4. Keep text content short and simple when possible (< 10 words works best)

**Template:**
> [Background/context description], featuring the text "[exact text]" in [font style] typography, [font weight], [color], [placement], [size relative to image]

**Font Styles to Reference:**
- Serif — formal, traditional, editorial (like Times New Roman)
- Sans-serif — modern, clean, tech-friendly (like Helvetica)
- Display / decorative — stylized, expressive
- Monospace — code, technical, retro computing
- Script / handwritten — personal, organic
- Bold slab serif — vintage, poster, impactful
- Thin / light weight — elegant, minimal

**Placement Descriptors:**
- Centered horizontally and vertically
- Overlaid on the bottom third
- Inside a banner/ribbon element
- Top-left corner
- As a headline above the illustration
- Integrated into the composition

**Sparse → Rich Example:**
```
BEFORE: "a poster that says SALE"
AFTER:  "A vibrant retail poster with a bright red background and geometric
        yellow diamond pattern, featuring the word 'SALE' in massive bold white
        sans-serif typography centered on the image, with '50% OFF' in slightly
        smaller black text below, clean and high-contrast design for maximum
        visibility, modern retail aesthetic"
```

---

### Product / Marketing Shots

**Template:**
> [Product name/type] on [surface/background], [studio lighting], [angle], [contextual props], [overall mood/purpose]

**Lighting Terms:**
- Key light — main light source, defines shadows
- Fill light — softens shadows from key light
- Rim/back light — separates subject from background
- Three-point lighting — classic product setup
- Light tent — diffused light from all sides, no shadows
- Gradient background sweep

**Surface/Background Options:**
- Seamless white / clean white sweep
- Dark matte surface
- Natural wood grain
- Marble or stone surface
- Colored gradient backdrop
- Lifestyle context (kitchen counter, coffee shop, outdoor)

**Material Descriptions:**
- Matte finish, no reflections
- High-gloss surface with specular highlights
- Frosted / satin texture
- Transparent / glass — describe refraction
- Metallic — brushed aluminum, chrome, gold

**Sparse → Rich Example:**
```
BEFORE: "a water bottle"
AFTER:  "A sleek brushed aluminum water bottle standing upright on a dark slate
        surface, professional studio photography with a soft gradient background
        transitioning from charcoal to deep blue, three-point lighting setup
        with a subtle rim light on the right edge creating a metallic gleam,
        shallow depth of field with slight foreground blur, aspirational outdoor
        lifestyle brand aesthetic"
```

---

### UI / App Design Mockups

**Template:**
> A [device type] displaying [app/interface description], featuring [UI elements], [color scheme], [design language], shown at [angle/perspective]

**Device Frames:**
- iPhone 16 / iPhone 15 Pro — modern iOS
- Android phone (generic or Pixel)
- iPad / tablet
- MacBook laptop — open at angle
- iMac desktop — overhead or frontal
- Desktop browser window — generic or browser chrome visible
- Apple Watch

**Design Languages:**
- Material Design 3 — Google's design system, colorful, rounded
- Apple Human Interface Guidelines — clean, minimal, SF Pro font
- Fluent Design (Windows) — depth, blur, acrylic effects
- Custom / clean modern — describe explicitly

**When Project Colors Are Known:**
> featuring the brand's primary color [hex or description] as the dominant accent

**Sparse → Rich Example:**
```
BEFORE: "a fitness app screen"
AFTER:  "An iPhone 16 showing a clean fitness tracking app dashboard, dark mode
        UI with navy blue (#1a1f35) background and neon green (#39ff14) accent
        color, displaying a large circular progress ring for daily step count
        (8,432/10,000), activity cards below with heart rate and calories,
        smooth rounded corners throughout, SF Pro Display typography, shown at
        a slight 3/4 angle resting on a gym mat"
```

---

### Minimalist / Abstract

**Key Principles:**
- Negative space is an active design element — describe it explicitly
- Specify exact colors (hex codes or precise color names)
- Describe composition geometry (rule of thirds, golden ratio, centered)
- Be precise about what is NOT in the image

**Template:**
> A minimalist [subject], [precise background color], [element positioning], [size proportions], [any textures or subtle details], no [things to exclude]

**Composition Guides:**
- Centered on plain background
- Positioned in the lower-left third, large negative space above
- Two elements balanced on opposite sides
- Single element at the geometric center, vast empty space surrounding

**Sparse → Rich Example:**
```
BEFORE: "a minimal logo concept"
AFTER:  "A minimalist geometric logo concept: a single thin circle in matte black
        on a pure white (#ffffff) background, with a small equilateral triangle
        inscribed at the center. The circle occupies roughly 40% of the canvas
        width, perfectly centered. Stark, modern, Swiss design aesthetic. No
        gradients, no shadows, no text. Clean vector illustration style."
```

---

### Diagrams and Technical Illustrations

**Key Considerations:**
- Use clean lines and clear labeling
- Specify color coding for different elements
- Describe the diagram type explicitly (flowchart, network diagram, architecture diagram)
- Keep backgrounds light for readability

**Template:**
> A clean [diagram type] showing [what is depicted], using [color scheme] with [element descriptions], labeled with [text style], white or light gray background, technical illustration style

**Sparse → Rich Example:**
```
BEFORE: "a system architecture diagram"
AFTER:  "A clean software architecture diagram showing a three-tier web
        application: frontend (blue box, top), connected by arrows to backend
        API (green box, middle), connected to database (yellow cylinder, bottom).
        Minimal flat design with rounded rectangle boxes, gray connector arrows,
        small monospace labels inside each component, white background,
        professional technical documentation style"
```

---

## Quality Boosters

These phrases reliably improve output quality when added to any prompt:

**For photorealistic images:**
- "professional photography, sharp focus, high detail"
- "8K resolution, award-winning photograph"
- "DSLR, RAW photo quality"

**For illustrations:**
- "highly detailed, masterpiece quality"
- "polished, ready for publication"
- "clean lines, vibrant colors"

**For commercial/product:**
- "commercial photography, advertising quality"
- "product photography for e-commerce"

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Keyword lists | No compositional context | Write a scene description |
| Contradictory styles | Confuses the model | Pick one consistent aesthetic |
| Too many subjects | Cluttered, unfocused | One primary subject |
| Vague quality terms | Meaningless without context | Specific photography or art terms |
| Overly long prompts (500+ words) | Diminishing returns past ~150 words | Focus on most important elements |
| Requesting specific people/faces | Safety policy violation | Describe appearance generically |
| Trademarked characters/logos | Content policy | Create original variations |

---

## Prompt Length Guidelines

- **Minimum effective**: ~30 words (sparse prompt will produce generic results)
- **Sweet spot**: 60–150 words (specific, narrative, covers key elements)
- **Diminishing returns**: 200+ words (model may ignore later details)
- **Maximum useful**: ~300 words (anything beyond rarely improves output)
