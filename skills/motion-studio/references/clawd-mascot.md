# Clawd and p5.brush cartoons

Read this before animating Clawd (the Claude Code mascot) or any painted cartoon character. Start: `npm install`, `node render.mjs --clip --out=out/video.mp4`; open `studio.html` in Chrome to scrub (`?t=2.5`, `?loop=emotions`, `?loop=views`). The video prompt decides what the film is about; these rules decide how it is made. Nothing is final: Clawd, emotions, props and helpers can be changed, but keep every character on model within one video.

Three goals: handmade (brush strokes, boiling ink, flat 2D, no lettering), alive (always moving, faces act, characters big), one piece (planned, every scene linked).

## Hard rules

1. Flat 2D, painted. Paint everything with p5.brush through `paint()` and `inkLine()`: characters get a flat `wash` plus ink outline, backgrounds soft watercolour `fill`, usually without outline. Never plain p5 shapes (`rect`, `ellipse`, `fill()`). Linework boils: `jit()`/`random()` reseed 12 times a second; use `hash(i)` for anything that must stay put and `boilSeed(key)` per separate element or one moving thing makes everything after it jitter. Never project 3D: no `rotateY`, no WEBGL, no perspective boxes. Turns use drawn key views (front, 3/4, side, back 3/4, back) via `turn()` or `spinView()`. Depth = overlap, scale and colour (farther = smaller, bluer, paler). Light is the exception: use `glow()` (additive); painting yellow over blue turns green. Soft palette, no pure black or white (`PAL.ink`, `PAL.cream`).
2. No text. No captions, titles, labels, signs, speech bubbles with words, words on screens. Reactions are painted marks: `!`, `?`, zzz, sweat, hearts, bulb, rain cloud (emotes). A sign repeating the story is the classic failure: show Clawd lost (looking left, right, map upside down, sweat drop). If a word is the joke, `letter()` once, one or two words. Lyrics are not text either: act the meaning.
3. Something happens in every shot: an event, one focal action, cause then reaction (give the reaction time), pay off every setup.
4. Time for the viewer, not the author. For each shot list the reads (what the viewer must understand, in order); each read needs time to be found, understood and registered. One read at a time; fast actions need held meanings; lead the eye before an important read; let the reads set the shot length and give the final read time to land. Models fail here most often.
5. Alive: nothing is ever still (`feel()` idles, drifting cameras, swaying grass, boil). Faces act through `emotions()` (anticipation, squint, take, overshoot); never swap `eyes`/`mouth` between frames. Clawd is big: `u` about 20-28 in a medium shot, 40-70 in a close-up, tiny (u < 12) only for wide establishing shots, never the whole video. Everything moves on a beat: `PROJECT.bpm` (and `offset` for a song's first downbeat) drives idles and dances; use `pulse()`/`beatN()`.
6. Transitions at every seam: into the first shot, between shots, out of the last. Never start on a hard frame or just stop. Vary them: brush wipe, iris, whip pan with smear, match cut, cut on action, camera move carrying across, fade or push from paper or black. A plain cut only on action or as a deliberate smash cut. Emotions and turns inside a shot are transitions too; props arrive on arcs.
7. One piece: storyboard first, in writing, before any scene code; show it to the person and let them react. One world and palette with a colour arc, one emotional thread planned across the whole video, an ending that rhymes with the opening, motion and screen direction continuing across cuts.

Animation principles apply as written in classic animation: anticipation, squash and stretch (`sq`), slow in and out (never plain `lerp`), weight, arcs (`arcPt`), overlap and follow-through (`spring`, `ring`, `backOut`). Also: avoid twinning (offset phases and seeds; one arm acts, the other does less), exaggerate, strong key poses that read as stills, show the thought (eyes move first).

## Storyboard

```
Logline: one sentence. Clawd wants ___, but ___, so ___.
World: setting, a small palette, light, how the colour changes across the video.
Motif: the thing that recurs and pays off.
Clawd's arc: the emotion keys across the whole video.
Shots:
  A  start–end  [transition in: ___]  what's seen · the EVENT · Clawd's reaction · camera
     reads:  start–end  the first thing the viewer must understand
             start–end  the next one (where is the viewer's eye when it starts?)
             ...
  B  start–end  [transition: ___]  ...
  ...
  [transition out: ___]
```

Check it: an event in every shot, every read lands before the next starts, a transition at every seam, no text anywhere, ending rhymes with opening. If the reads do not fit the shot, lengthen the shot or cut a read; do not squeeze.

## Build

Set `duration` and `bpm` in `src/config.js`, put the scene in `src/scenes/my_video.js` (IIFE ending in `shots([...])`) and replace the `demo.js` script tag in `studio.html`. Do not copy the demo. Block key poses first, check them as stills, then add motion. A shot is `fn(t, lt, dur)` and paints the whole frame from `t` alone: frames render in parallel and out of order, no carried state, no `Math.random()`.

```js
// src/scenes/my_video.js
(() => {
  function park(t, lt, dur) {                        // t = video time, lt = time in this shot, dur = shot length
    camBegin(960 + 20 * Math.sin(lt * .6), 540, 1 + .02 * lt);   // slow drift and push: the camera is never dead
    paint(rectPts(-200, -200, W + 400, H + 400), { wash: PAL.sky, ink: null });           // background
    paint(ellPts(960, 1150, 1400, 380, 40, 2), { wash: PAL.sap, ink: PAL.ink, sw: 1 });   // ground
    const mood = emotions(lt, [[0, 'bored'], [1.2, 'surprised'], [1.7, 'excited']]);      // acted changes
    const hop = jump(lt, 2.2, 2.7, 3);                                                    // add poses that share fields
    clawd(960, 860, 26, { ...mood, dy: mood.dy + hop.dy, sq: mood.sq + hop.sq });
    const at = toScreen(960, 860 - 4 * 26);          // Clawd's screen position, for the iris
    camEnd();
    if (lt < .45) iris(...at, lerp(0, 1500, easeIn(lt / .45)));            // transition in
    if (lt > dur - .3) brushWipe((lt - (dur - .3)) / .6);                 // transition out (next shot finishes it)
  }
  shots([[0, park] /*, [3.5, nextShot], ... */]);
})();
```

## API essentials

- `clawd(x, y, u, options)`: (x, y) = ground point between the feet; Clawd is 10u wide and 8u tall with legs. Sizes: wide u 10-16, medium 20-28, close-up 40-70, extreme close-up 90+.
- Options: pose `dx dy sq rot flip aL aR walk`, `view` (front, q, side, qback, back), face `eyes mouth lookX lookY squint blush gloom lid`, `tint`, `hat`, `emote`+`emoteK`+`emoteAge`, hooks `draw(u, sw)`, `armL`/`armR`. Spread options (`{...feel('happy', t), ...turn(t, 1, 1.15, 0, .25)}`); later wins, so add shared fields (`dy`, `sq`) together.
- `feel(name, t, over)`: 31 emotions (joy, sly, low, hot, alarm, mind families). `emotions(t, [[t0,'sleepy'],[1.9,'surprised',{lookX:.8}],...])` for acted changes. `turn(t, t0, t1, a0, a1)` headings in turns (0 front, .25 right, .5 back).
- Acting: `jump`, `take`, `stroll`, `spring`, `ring`, `arcPt`, `onTwos`; dances `move(style, t, seed)`; camera `camBegin(cx,cy,zoom,rot)`/`camEnd()` (always paired, one level), `toScreen`, `shakeXY`; screen effects `brushWipe`, `iris`, `irisShape`, `flash`.
- `paint(pts, o)` options: `wash`, `fill`+`bleed`+`tex`, `hatch`, `ink`, `sw`, `curv`; `ink: null` means no outline. Build a prop from as few outlines as possible (a tail is one `ribbon`).
- p5.brush quirks: wash at 255 is exact, lower opacity mixes like pigment; outline weight scales with camera zoom (scale `sw` down for small shapes); a NaN in a point list throws a misleading `OffscreenCanvas` error (guard `acos`). Strokes far from the origin under zoom collapse; hundreds of shapes per frame are fine, thousands are not (aim at 1.5 s per frame or less).

## Review and render

```bash
# contact sheet: the shape of the whole piece (every shot's first, middle and last frames)
node render.mjs --sheet=0.1,0.8,1.6,2.4,3.1,3.9 --cols=6 --w=320 --out=out/check/sheet.jpg
# strip: EVERY frame of a moment (turns, takes, jumps, throws, transitions)
node render.mjs --strip=2.1:2.6 --cols=6 --w=320 --out=out/check/strip.jpg
# crop: full-resolution detail (faces, hands, contacts, glows); crop=x,y,w,h in frame pixels
node render.mjs --sheet=2.3,2.4 --crop=760,420,500,400 --w=500 --out=out/check/face.jpg
```

Budget: at least one sheet per shot, a strip for every key motion and transition, a crop for every face that carries the story. Check read, timing, motion (anticipation and follow-through, no pops, parts moving at different times), boil, contacts (feet touch ground, held things touch arm tips), transitions at the first and last 0.5 s of every shot, rules (text? 3D? dead stretch?), colour (muddy glows, pure black). Render: `node render.mjs --clip --out=out/video.mp4`, or `--frames --workers=4` (parallel, resumable) then `--encode --out=out/video.mp4`.

## Failures that look generated

Signs or captions; Clawd standing still smiling; one brisk speed with stacked events and no holds; moments over before understood; tiny Clawd in an empty landscape; snapping faces; linear moves with parts and arms in sync; timid poses. Re-boiling still things (missing `boilSeed`); hard cuts everywhere; 3D rotation; plain p5 shapes or digital glows; muddy yellow-over-blue glows; props floating near a hand; every shot a different unlinked world.
