# Prompting and briefs

Read this to turn a request into a brief the agent can execute: effort level, one-liner, brand reel, reference-driven, XML state spec, overnight director brief.

## Harness first

The prompt is 10 percent of the video; the harness (render engine, sound, critique loop) is the other 90. Only an agent with a shell can render, listen and look at its own frames; a chat app can write an animation but not iterate on it. "One prompt" posts range from a 30-word sentence to a 9,500-character brief plus skills, keys and a 12-hour run; "one prompt" only counts human turns, "pure code" names the render path, "zero external assets" names the input boundary.

Effort: Opus 5.5 defaults to medium and thinks before answering. Keep medium for tweaks and re-renders, raise to xhigh for a new film, and use max for launch pieces whose opening seconds must hook.

## Ban the AI-video defaults

Without a reference or rules, output collapses to text centered on a gradient, fade-in on everything, labels in the corners or borders around the frame, glowing UI chrome, stock particle bursts. State these as banned in the brief. Add: one display face and one UI face, one accent colour unless told otherwise, something new on screen every 2 to 4 seconds. Real assets only: screenshot the real product with Playwright, never redraw UI from imagination; crop and animate the real thing.

## One-liner showreel (tests the engine, not the idea)

Ask for a dynamic 15 s motion-graphics showreel as if the model were a motion designer building a resume reel, going all out. It works because "showreel" fixes a genre with known rules (fast cuts, new technique each shot, best work first), the model is the subject so there is no content to get wrong, and 15 s fits 6 to 8 shots in one pass. Weakness: identical one-liners produce reels that rhyme with each other. Variants: 60 s 16:9 with an original piano score synced to every cut; "avoid frames and text in the corners" as an anti-slop guard; a story (history of a topic, 45 s vertical) instead of techniques; an agency persona with one accent colour and a different technique per shot.

## Brand reel

Three added lines turn the reel into a product ad: the product URL, "use the real screenshots, logo and assets", "must have music". Brief skeleton:

> Make a 20 s motion video for PRODUCT (URL) with showreel energy. Assets: visit the site, capture real screenshots, logo, colours and fonts into `./assets`, list what you found before animating. Story, one beat per 2 to 4 s: hook as 5 words of huge kinetic type; the product assembles piece by piece; three features each as a UI moment with a cursor performing a real action; one proof number; logo lockup plus CTA. Sound: original 120 BPM music synthesized in code, UI clicks and whooshes on the beat. Format: 1080x1920 first, then 1:1 and 16:9 from the same timeline. Before the full render, show a contact sheet of one frame per beat.

## Reference first, then style guide, shotlist, wait for OK

Naming a style beats describing one; a reference gives pacing, type and transitions to copy.

1. Reference as a frame (say what to take: palette, type, grain; what not: subject), a video (extract one frame every 0.5 s with ffmpeg and describe pacing shot by shot) or a library of your own images (a reference nobody else can copy).
2. Write `docs/style_guide.md`: palette hex, type family/weight/tracking, shot lengths, transition types, camera moves, texture and grain, how text enters and exits.
3. Write `docs/shotlist.md` for the new subject in that style: every shot with frames, camera, text, SFX. Borrow how the reference moves and is composed; never its subject, logos or characters.
4. Show both files and wait for OK before any scene code. (Overnight runs: continue after a stated timeout instead.)

With a reference, specify the look and constraints and let the model pick the technique; name a library only when you need reuse.

## XML state spec (looping one-shape UI morph)

Most-bookmarked pattern: write the state list, not the vibe. Tags: `<inputs>`, `<direction>`, `<structure>`, `<build>`, `<gotchas>`, `<start>`.

- `<inputs>`: the agent asks for 8 to 12 UI states that tell the story, the real data shown in each, brand colours/fonts and one accent, a royalty-free track near 120 BPM, output formats.
- `<direction>`: product-film UI motion; one container never cuts, every state is the same element changing size, radius and fill while its content swaps behind a short blur. A cursor drives every change; warm neutral canvas; springs with at most a tiny overshoot; banned: bouncy easing, glows, gradients on UI chrome, particle bursts, dead time.
- `<structure>`: BPM, number of bars, something happens on every beat, then the state sequence (for example button, loader, check, island, player with play/pause morph, scrub, volume slider that stretches past max, toggle on a beat, liquid tab indicator, self-drawing chart with hover tooltip, command palette, filter, toast, back to start).
- `<build>`: one HTML file, one canvas, `draw(t)`; no CSS transitions or timers; closed-form springs with one spring per target change. Text enters after the morph starts and leaves before the next; tab edges on different springs; beat grid measured from the track, start on a downbeat, UI sounds on measured peaks; 60 fps with 4 blended subframes; zero object allocation in the loop; last frame equals first.
- `<gotchas>`: no `will-change` on anything the camera scales; loop seam includes cursor velocity.
- `<start>`: ask for the inputs, then show the state list on the beat grid before writing code.

## Overnight director brief

Long briefs do not describe a video, they hire a crew. Sections, in order:

1. Film in one line (logline and the joke, so each decision can be checked against it).
2. References and inputs (source video, song used unchanged, image library, prior-work repo): take the grammar, never the content.
3. Tools and keys (skills to load, APIs in `.env`, budget: "be economical", where docs live).
4. Character bible (proportions, palette sampled from a sheet, expressions, an identity lock that survives style changes).
5. Beat sheet (acts with timestamps, a visual payoff every 3 to 5 s, hook in the first 2 s, last frame sets up the first).
6. Text on screen (when lyrics go huge, when they sit as subtitles; leave room).
7. Workflow with gates: plan, rig, stills, animatic at 960x540 with placeholder audio, full pass, polish, audio, render. Do not skip gates.
8. Critique loop (`critique-loop.md`), at least 3 rounds per shot.
9. Deliverables: final MP4, loop check, poster, contact sheet, clean source with a README.

Generate-then-trace: a video model renders base shots with characters and physics, then the agent redraws the whole video in JavaScript on top so the viewer sees only the code-drawn layer (hard-to-hand-code motion, consistent ownable look). Re-running one brief with your own gallery yields a completely different film.

Subagents for long films: the lead writes `docs/ANIMATION_GUIDE.md` first so every subagent codes in one style, and `STORYBOARD.md` after the first pass; each chapter lives in its own file (for example `src/ch/c03_takeoff.js`), every shot a pure function of `t`, and a subagent edits only its own chapter file. Ask for both guide files by name.

## Spec density and structure

Mood words ("snappy", "cinematic") hand the look to the model; exact hex colours, named textures, type direction and timestamps hand you control. Density never hurts, a stronger model just uses less of its own taste. Resolve simultaneity in the text: "the counter fades out fully by 4.2 s; at 4.2 s READY stamps in". Quote on-screen copy exactly; unquoted copy gets paraphrased. Timestamp the beats and tell the agent where to hold; agents skip breathing room unless told. Slot for each element: what is on screen, what it does, where it sits, how it looks, when inside the beat.

## Ship it

Export every format from one timeline. Package the pipeline as a skill so the next video is one sentence: inputs to collect (product and URL, duration, formats, brand colours and fonts, reference, music or "synthesize"). Also numbered pipeline (assets, style guide, beats, shotlist and wait for OK, build, critique at least 3 rounds, render and mix to -14 LUFS). Plus hard rules (real UI only, no `Math.random`/timers/transitions in render mode, banned looks). For client or team work add a production brief: audience and the one thing to feel, delivery specs, what must stay exact (claims, names, logo), and a table of every input asset with owner, licence and permitted use.
