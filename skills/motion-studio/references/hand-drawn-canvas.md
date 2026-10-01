# Hand-drawn Node canvas films

Read this for storybook, brush-ink and watercolour, low-poly poster loops or game-feel shorts drawn entirely in JavaScript with no browser, no GPU and no API keys (Node plus ffmpeg; only dependency `@napi-rs/canvas`). A film is a pure function `frame(ctx, t)`; the library supplies the look, rigs act, the harness renders, previews and verifies. For Clawd and p5.brush use `clawd-mascot.md` instead.

## Install and quick start

```bash
claude plugin marketplace add buildwithhanif/claude-animation-skill
claude plugin install claude-animation@claude-animation-skill
cd <plugin dir>/skills/claude-animation && npm install
```

```bash
SK=~/.claude/skills/claude-animation            # wherever this skill lives
mkdir my-film && cd my-film && cp $SK/templates/film-template.mjs film.mjs
CLAUDE_ANIMATION_LIB=$SK/lib node film.mjs sheet 0,1,2,3,4    # look
CLAUDE_ANIMATION_LIB=$SK/lib node film.mjs render             # out/template.mp4
node $SK/scripts/music.mjs bed.wav --dur 5 --end 4.4
node $SK/scripts/sound.mjs cues.json out/template.mp4 out/final.mp4 --bed bed.wav
```

Loop: brief, style bible plus beat sheet, copy the template to `film.mjs`, `sheet`, fix, `strip` the fast bits, `verify`, `render`, `cues.json`, `sound.mjs`, look at the master's contact sheet, deliver. `strip` renders 12 consecutive frames around a fast action; `verify` proves a frame is identical rendered in or out of order; `render` is staged and never overwrites a good file with a failed encode. Speed: a 32 s 1920x1080 film renders in about 27 s, so iterate on sheets.

## Library map (`lib/`, `scripts/`)

- `core.mjs`: easing (`eOut eIn eIO eBack eElastic eBounce eExpo popS`), `ss` windows, `hash rng noise1`, `catmull pathOf ik`, canvas helpers (`at line poly smooth ellipse stroke fill taper`), texture (`hatch fibre grainOver burst speedLines`).
- `pen.mjs`: `Pen` with tapered brush `stroke`, `pencil` (3 broken passes), `ring`, `box` (overshooting corners), `wash` (blooming watercolour), `text` (writes itself), reveal-in-order, stable named seeds, opt-in boil.
- `textures.mjs`: `paper fibrePaper lightBands sun moon star4 grass soil nightSky fleshCells filmFinish`. `nature.mjs`: `sprout melonLeaf tendril vine blossom bee drop`.
- Rigs: `rigs/ant.mjs` (`ant(ctx, x, groundY, s, pose)`, `antGuides`, `seed`), `rigs/chibi.mjs` (big-head person with joints and look presets), `rigs/bean.mjs` (`person bust bubble flagCloth hat SKIN`), `rigs/critter.mjs` (action hero), `rigs/bug.mjs` (beetle and boss). `colony.mjs`: leaves, brood, fungus, roots, a nest cross-section with walkable tunnels.
- `lowpoly.mjs`: `facetMass`, `ridge`, `skyGradient`, `facetCloud`, `RAMPS` (canyon, dusk, mesa, forest, ice, water, balloon, cloud).
- `fx.mjs`: `timeWarp` (hit-stop), `shake`, `burstParticles`, `landDust`, `ring`, `flashAlpha`, `comicText`, `floatText`, `afterimages`, `starburst`, `heart`.
- `film.mjs`: `run({...})` giving `render / sheet / strip / verify`; `exposure(t, track, fps)` for ones, twos and holds.
- Sound scripts: `sound.mjs` (SFX from `cues.json`, mix, two-pass loudnorm, mux), `music.mjs` (ukulele bed: `--dur --bpm --end --quiet a-b,c-d`), `chiptune.mjs` (game soundtrack, `--sections "level:0-13.8,boss:15.4-25.1,..."`), `ambient.mjs` (pads, sparse bells, wind for loops).

## Hard rules

1. Beats before code. Fill the beat sheet first: every beat has an end state the viewer could point at, a camera, an exposure and a sound cue. Designing inside the code makes slides.
2. Every surface gets three layers: base, texture, edge. A flat fill is unfinished.
3. Characters are rigs with anatomy, not blobs. The rig origin is the ground point under the waist; callers pass `groundY`; there is no ground-offset parameter (that knob produced stilt legs for two passes). If a fix does not take, grep for overrides at call sites.
4. Boil is a decision, not a default. The textured-editorial look holds still shots perfectly still; brush-watercolour boils at 10 fps. Write the choice in the style bible.
5. Stable seeds: marks are seeded from a name (`pen.begin("ant/body")`), never the frame index, so held drawings keep their marks and re-renders are identical. `node film.mjs verify` must pass, with sample frames straddling every hand-off.
6. Look at pixels every pass: `sheet` before `render`, `strip` around every contact or fast action, and a contact sheet of the encoded master before calling it done.
7. Sound comes from the picture's timeline, about 0.03 s before each contact; no continuous scratch bed; loudnorm the mix.
8. Show the world, not a slide: layers (sky, far, mid, ground, foreground passing the camera), inhabitants doing things, a moving camera.

## Workflow details

- Brief in one paragraph: audience, story in three beats (setup, turn, payoff), length (under a minute, a beat every 1 to 3 s), format (1080x1080 feeds, 1080x1920 vertical, 1920x1080 YouTube), one style preset.
- Style bible, pasted verbatim at the top of `film.mjs`: paper, ink, at most 6 colours plus ink, which surfaces get which texture, line weight by depth, boil yes/no, cast with scales.
- Beat sheet rows: start, duration, what the viewer notices, action to end state, camera, exposure (twos for acting, ones for fast flights, zooms and anything the camera tracks, hold for a read), sound cue. Key beat in the middle of the shot, not where the cut eats it. A cut must add information; otherwise move the camera. Show feeling as behaviour ("antenna droops, body sinks 6 px").
- Build: `setup()` makes static things once; `frame(ctx, t, i, S)` is scenes as functions of local time; each element is `at(ctx, x, y, scale, rot, () => draw())` driven by windows (`ss`, `popS`, `eBack`, `eOut`); draw order is depth order. Narration: lock beats to the word timestamps.
- Detail pass before render: base, texture and edge on everything; hero most detailed; eyes with two highlights; far limbs lighter; contact shadow under characters. Line weight falls off with depth (hero 2.6 to 3.4 px, midground 1.6 to 2.4, background 1 to 1.4 at 40 to 60 percent opacity, blue construction guides 1.2 to 2 px).
- New creature rig: study sheet of 3 to 5 references, one local space (origin on ground under centre of mass, facing +x), parts as separate shapes back to front, pose parameters not keyframes (`gait`, `rear`, `headDip`, `jaw`, `blink`). Add free secondary motion (sine plus turn lag), a test sheet (standing, 4 walk phases, special poses, flipped, 2x crop), seed from the character's name. Explicit knee offsets read cleaner than two-bone IK.

## Timing (24 fps storybook)

Shots 0.8 to 2.7 s. A pop changes in 1 to 2 frames then holds ("snap, then hold": ease the settle, not the change); pop-in overshoot `eBack` s about 1.8 to 2.2 over 0.3 to 0.4 s; zoom-out transition 0.55 s `eIO`; stagger groups 0.05 to 0.14 s. One thing moves at a time; loops never all in phase (own phase per item, start mid-cycle); holds need life (breathing plus or minus 2 percent, blink about every 3.3 s). Camera is a transform on the whole scene layer (locked, slow push 5 to 10 percent, pan at 105 percent or more so edges never show); keep overlays out of it. Pass `exposure(t)` to drawings and raw `t` to the camera.

Game feel: choreograph in game time with `timeWarp` (hit-stop 0.083 s, 0.125 big hit, 0.3 finisher), squash 1.35 on landing, stretch 0.8 in air, anticipation 1.22 for about 2 frames. Every hit = target flash (cap about 0.6), sparks, ring, comic word, shake, plus a thump and crack; world camera zoom of about 1.3 so a hero is not icon-sized.

## Style presets

Textured editorial (cream #F3EEDD paper plus grain, diagonal light bands, ink #1E1612, blue construction guides #5E80CC, no boil on still shots, acting on twos, 1080x1080 at 24 fps). Brush ink plus watercolour (`fibrePaper`, tapered strokes boiling at 10 fps, blooming washes, self-writing lettering, bean cast). Line doodle (uniform 5 px black on cream, one red accent, tiny mascot). 3D extruded type around live action (glyphs on a cylinder, 1 px layers, 6-sample motion blur); faceted low-poly poster loops (`facetMass` cells 50 to 75 px, jitter about 0.22, layers back to front fading into haze, every motion periodic in the loop length, check frame 0 against the last).

## Traps

State carried between frames breaks seeking; polygons under 6 points smooth into blobs unless `sharp: true`; multiply washes on dark shapes go muddy (use `over: true`); rotate about the contact point, not the waist; frame 0 must not be empty; two-bone IK can pick knees that cross the body.
