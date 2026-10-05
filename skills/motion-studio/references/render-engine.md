# Render engine: the seek(t) canvas pipeline

Read this to build or repair the default route: one `index.html` that paints any moment on demand, Playwright capturing frames, ffmpeg encoding.

## Contents

- [Contract](#contract)
- [Setup](#setup)
- [The page](#the-page)
- [The renderer](#the-renderer)

## Contract

The model cannot emit an MP4. It writes a program; a headless browser calls `window.seek(t)` once per frame, screenshots the canvas, and ffmpeg stitches the frames. A 15 s film at 60 fps is 900 frames (3600 captures with 4 subframes).

- A film is a function of time only: `window.seek(t)` draws the frame at `t` and does nothing else. No state carried between frames, no counters, no physics integrated frame by frame.
- In render mode forbid CSS transitions, `setTimeout`/`setInterval` and `requestAnimationFrame`. Run the live preview loop only when `!navigator.webdriver`.
- Randomness is seeded (mulberry32), never `Math.random`. Seed from a name or index of the object, not from the frame number, so a held drawing keeps its marks and a re-render is byte-identical.
- `await document.fonts.ready` before the first capture, or canvas text renders in a fallback face.
- Frames may be rendered in parallel and out of order, so anything cached "since the last frame" breaks. Pick determinism-check frames that straddle every hand-off.
- Never put `will-change` on anything the camera scales; text turns blurry.
- Open mid-action: frame 0 must not be empty, and for a loop the last frame must equal the first (cursor position and velocity included).

Opus defaults to this zero-dependency route (one `index.html`, a seek function driven by Playwright, ffmpeg) and skips Remotion and HyperFrames even when installed. Name a framework explicitly if you want one (see `hyperframes.md`, `remotion.md`).

## Setup

Node 22+, ffmpeg, Python with `numpy librosa soundfile` for audio analysis. Then `npm i -D playwright && npx playwright install chromium`. Put the render contract (the bullets above, encode settings, banned looks, sound and loudness rules, "look at the contact sheet before the full render") in the project `CLAUDE.md` so every film inherits it. Keep one session per brand: the renderer, synth and export pipeline get reused and the second video comes out faster.

## The page

```html authored
<!doctype html>
<meta charset="utf-8">
<style>body{margin:0;background:#101012}#stage{display:block}</style>
<canvas id="stage" width="1080" height="1920"></canvas>
<script>
const cv = document.getElementById('stage'), ctx = cv.getContext('2d');
const LENGTH = 15; // seconds

// mulberry32: seed per object (e.g. hashed name), never per frame
const rand = (seed) => () => {
  seed = (seed + 0x6d2b79f5) | 0;
  let x = Math.imul(seed ^ (seed >>> 15), seed | 1);
  x ^= x + Math.imul(x ^ (x >>> 7), x | 61);
  return ((x ^ (x >>> 14)) >>> 0) / 2 ** 32;
};

// timeline: [start, end, paint(localTime, shotLength)]
const shots = [
  [0, 4, (lt, len) => { /* hook: paint only from lt */ }],
  [4, 9, (lt, len) => { /* product */ }],
];

function paintAt(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = '#101012';
  ctx.fillRect(0, 0, cv.width, cv.height);
  for (const [a, b, paint] of shots) if (t >= a && t < b) paint(t - a, b - a);
}
window.seek = (t) => { paintAt(t); return t; };

if (!navigator.webdriver) { // preview only; the headless render just calls seek()
  const start = performance.now();
  const tick = () => { paintAt(((performance.now() - start) / 1000) % LENGTH); requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
}
</script>
```

Write scenes against a layout function, not fixed pixels, so one timeline renders 9:16, 1:1 and 16:9. Reframe type and UI per format; never crop a 16:9 render to vertical.

## The renderer

```js authored
// node render.mjs --fps 60 --seconds 15 --sub 4 --start 0
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { parseArgs } from 'node:util';
import { mkdirSync } from 'node:fs';

const { values: o } = parseArgs({ options: {
  fps: { type: 'string', default: '60' }, seconds: { type: 'string', default: '15' },
  sub: { type: 'string', default: '4' }, start: { type: 'string', default: '0' },
  out: { type: 'string', default: 'out/silent.mp4' } } });
const fps = +o.fps, sub = +o.sub, start = +o.start, frames = Math.round(+o.seconds * fps);
mkdirSync('out', { recursive: true });

// average each group of `sub` captures, keep the last frame of every group
const blur = `tmix=frames=${sub},select='not(mod(n+1\\,${sub}))',setpts=N/(${fps}*TB)`;
const enc = spawn('ffmpeg', ['-y', '-f', 'image2pipe', '-c:v', 'png', '-r', `${fps * sub}`, '-i', 'pipe:0',
  '-vf', blur, '-r', `${fps}`, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', o.out],
  { stdio: ['pipe', 'ignore', 'inherit'] });
const done = new Promise((res) => enc.on('exit', res));

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
await page.goto(new URL('index.html', `file://${process.cwd()}/`).href);
await page.evaluate(async () => { await document.fonts.ready; }); // canvas text needs real fonts
const canvas = page.locator('#stage');

for (let f = 0; f < frames * sub; f++) {
  await page.evaluate((t) => window.seek(t), start + f / (fps * sub));
  const buf = await canvas.screenshot();
  if (!enc.stdin.write(buf)) await new Promise((res) => enc.stdin.once('drain', res));
}
enc.stdin.end();
await done;
await browser.close();
```

- Encode H.264 (`libx264`), `yuv420p`, CRF 16. `yuv420p` is what makes the file play everywhere.
- Motion blur: render 4 subframes per frame (`--sub 4`) and blend with `tmix`. Use `--sub 1` for fast checks.
- Re-render only the affected seconds: pass `--start`/`--seconds` for the span, write it to a segment file, then splice with the ffmpeg concat demuxer (`-f concat -c copy`). Keep segment boundaries on frame boundaries.
- Determinism check: render a short span twice (`--sub 1`) and compare the hashes of the outputs; they must match.
- Mix audio afterwards (`sound.md`), mux with `-c:v copy`, deliver `final.mp4` plus contact sheet and poster. Run `critique-loop.md` before the full render, not after.
- Faster iteration: render one frame per beat as a contact sheet first; render the first 5 s as a sample before a full render.
