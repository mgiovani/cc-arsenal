# Style catalog

Read this to choose a look and know how to ask for it. Pick one style per film and name it in the brief; mixing styles inside one film reads as a mistake. Write the recipe (palette hex, type, texture, line weight, boil yes/no) into a style bible and paste it verbatim into every build session; paraphrase causes drift. To match a new reference, make a swatch sheet first (paper, ink at three weights, each material, one character pose) next to crops of the reference, adjust until your crop could sit in their frame, then write the numbers down.

Each entry: look, technique, how to prompt.

## UI and product looks

**Single-shape UI morph (loops).** Look: warm off-white (about #F0F0EA) with a faint radial vignette, black and white components, neutral grotesk (Inter or Geist) plus mono timestamps, one optional accent (one film used only orange for logo dot, CTA and map markers), soft shadows, no grain. Technique: one persistent container morphs size, radius and colour while content blur-cross-fades; a faux cursor travels and clicks to trigger every state. In-state motion (bar fills, chart draws itself, digits roll with blur, rows stagger in); every state is a recognisable archetype; light and dark cards alternate to separate beats; optional single 3D data moment (dot-matrix globe with glowing markers); bookend on the logo pill. Prompt: the XML state spec in `prompting-and-briefs.md` with 8 to 12 states, 120 BPM, last frame equals first. Build with `motion-and-springs.md`.

**Showreel / resume reel.** Look: fast cuts, a new technique every shot, kinetic type, camera moves, synced sound. Technique: 6 to 8 shots in 15 s, 1.5 to 4 s each. Prompt: one-liner variants and the brand version in `prompting-and-briefs.md`; use it to test the engine, then move on to a real brief.

**Chaptered product tour.** Look: each chapter swaps a full-bleed pastel colour field (cobalt intro, white, periwinkle checkout, blush upsell, sage payouts), headline left and detailed browser or phone UI right. Also: grotesk bold headline with an italic serif for the one emotional word, tiny mono chapter labels with a running timecode, a 1-bit ordered-dither mascot in a corner, no grain. Technique: one colour per chapter keeps 39 s legible; same headline/UI template every chapter; blurred slide-through camera between UI states instead of hard cuts; cursor clicks; a stopwatch chip counting up to show speed. Prompt: list chapters with colour, headline and the real UI shown; ask for the template reused per chapter.

**Flat-vector SVG documentary.** Look: dark scene-dependent grounds (garage brown, rainy navy, bokeh black), huge thin year numeral beside a bold headline, small tracked uppercase chapter labels, a bottom timeline whose hop arcs draw between events, jointed vector character, no outlines, final white-out. Technique: Remotion plus React plus SVG (about 8.7k lines for 2 minutes): a rig with procedural walk cycle, 23 custom transitions, soundtrack synthesized in Node with cuts locked to 120 BPM, lighting as scene identity (warm garage, rain night, spotlight). Prompt: name the biography, chapters and eras, ask for an always-on structural HUD (year, age, chapter, timeline).

## Print and retro looks

**Riso / halftone anime music video.** Look: cream paper with 3 to 4 flat inks (orange, indigo, hot pink, butter yellow), overprint (blue over pink makes violet), halftone-dot shading, misregistration, thick uneven outlines. Also: burned-in italic-serif lyric lines with key-word underlines, block-caps punch words, a running date-stamp HUD, palette-swapped crowd of the heroine, sunburst and concentric-ring backgrounds. Technique: generate-then-trace (video model base shots, redrawn in code), lyrics timed from the audio, cut on beats. Prompt: ask for the fixed ink palette, the lyric treatment and an identity-locked character sheet first.

**Risograph zine.** Look: two-ink (riso blue, vermilion) grain on kraft or night-sky grounds, typewriter monospace label-tape strips with offset dotted shadows, a single repeating mascot (asterisk with rounded arms) and a collector prop (a jar), corner crop marks, hand-drawn circle annotations. Technique: text-as-imagery (a bread slice or a cat silhouette filled with repeated words), kraft = chaos and requests, night sky = quiet human details; ASCII-like figures; misregistration plus halftone gradient. Prompt: a short story told through micro-copy, two inks only, one mascot, one collector prop.

**PC-98 pixel JRPG music video.** Look: limited palette with ordered dithering, navy dialogue boxes with cream borders, pixel bitmap fonts, yellow name tags in brackets, battle HUD with a progress meter, CRT scanlines, rounded bezel and machine tag. Technique: commit to the retro-hardware frame; typewriter dialogue; fake RPG battle screen with damage numbers; karaoke outlined subtitles; closing credits crawl; each scene a different set in a consistent palette. For pixel art in code, draw at a tiny integer grid (for example 160x90 or 480x270) and upscale nearest-neighbour. Prompt: name the hardware and the game screens, give the HUD meter as the story clock.

## Illustrated looks

**Watercolour storybook short (wordless).** Look: wet-wash backgrounds with bleed edges and granulation over visible paper fibre, flatter cut-out puppets with soft brown outlines, warm-cold colour arc following the emotion (lonely lavender, warm street, pink dusk), a glowing companion character as the light source. Technique: pictogram emotes instead of text (Zz, ?, rain cloud, hearts), sparkle and heart bursts for payoff, scenes dissolving room to street to rooftop to sky. Prompt: logline plus the colour arc; ask for no text. Built in code (`hand-drawn-canvas.md`, presets "brush ink + watercolour") or with p5.brush (`clawd-mascot.md`).

**Doodle fake-app film.** Look: cream parchment with thin dark-brown ink, pastel badges, hand-lettered UI labels, comic sound-effect stickers (SNIP!, EXPORT!) with yellow fill and brown outline, brush-script sign-off, wobble and crosshatch on the mascot. Technique: a cardboard-box mascot physically operates a hand-drawn editor UI (timeline, phone preview, sliders), rubber-hose arm stretching to buttons, the camera moves around one dense illustrated canvas instead of cutting, payoff frame shows the output as a vertical video. Prompt: "the AI builds and uses its own app", list UI regions and the three actions the mascot performs.

**Crayon box-mascot storybook.** Look: off-white speckled paper, a tiny burnt-orange box creature with brown outline and crosshatch, cuts to deep-navy hand-drawn science scenes (DNA helix, galaxy of glyph particles, planet horizon) in chalk-like glowing strokes, no text. Technique: one recurring mascot as bookend between big abstract scenes; paper versus night contrast; hand-hatched shadows; occlusion on the helix. Prompt: mascot, three science scenes, "no captions", crayon texture.

**Clawd hand-painted cartoon.** Look: p5.brush wash plus boiling ink linework, soft palette, flat 2D, acted emotions, no text. Technique and rules in `clawd-mascot.md`.

**Storybook insects, brush-ink explainers, line doodle, 3D extruded type, faceted low-poly poster loops.** Presets and recipes in `hand-drawn-canvas.md`.

## Choosing

Product story: UI morph or chaptered tour. Song: riso anime, PC-98, or hand-drawn lyric film; character story: watercolour, crayon, Clawd; biography or explainer: flat-vector documentary; ambient loop: low-poly poster. When unsure, ask for two contrasting style names and a one-frame mock of each before committing.
