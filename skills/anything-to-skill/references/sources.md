# Sources

How each handler behaves, which flags it takes, and what it leaves out on purpose. Every handler writes units into the same store, so any mix of inputs works in one workspace.

`a2s.py detect <input>` routes an input: a YouTube URL or an existing local path scores 10, any other http(s) URL scores 1 (web is the fallback), and a bare topic string routes to nothing.

Common flags on every ingest script: `--slug`, `--base` (workspaces directory, default `./.cc-arsenal/a2s`), `--max-pages N`, `--allow-private` (skip the private-network guard; use only for a local test server the user owns).

## Web (`ingest_web.py`, `crawl_brain.py`)

Discovery order, first hit wins per site:

1. `/llms.txt`, then `/.well-known/llms.txt`. Linked pages ending in `.md` are used directly.
2. A sitemap named in `robots.txt` (or `/sitemap.xml`), including sitemap indexes.
3. A breadth-first crawl limited to the seed's `--scope` path prefix.

Fetch rules:

- Every request is a conditional GET (ETag / Last-Modified) with `Accept: text/markdown, text/html;q=0.8`. A 304 keeps the stored page.
- `robots.txt` is honored, including `Crawl-delay`, `*` and `$` wildcards and longest-match precedence. A server error or network failure fetching `robots.txt` means disallow everything; a 4xx means no rules.
- Per-host rate: `max(Crawl-delay, 1s)` times a random 1-2x factor between requests, starting at 1-2 concurrent requests, adding one after a run of successes and halving on 429/503. `Retry-After` (seconds or HTTP date) is honored on top of a jittered backoff.
- After five consecutive 429/403 responses a host is paused, then probed once; if the probe fails the host is skipped.
- The client presents a real Chrome TLS and HTTP/2 fingerprint. It does not override the user agent or client hints.
- Only http(s). Private, loopback, link-local and NAT64-embedded private addresses are refused, and every redirect hop is checked before it is requested.
- Response bodies are capped (10 MB for pages, 50 MB for sitemaps and llms.txt, counted after decompression); an oversized page is skipped.
- Blocked pages (401, 403, 451, bot-challenge pages) are marked `blocked` and reported; 403 and challenge pages first get one attempt in the browser fallback below, 401 and 451 none. There is no CAPTCHA solving, login bypass or paywall bypass.

Extraction: HTML goes through a main-content extractor to markdown. If fenced code is lost (the `<pre>` count exceeds the fence count), it re-extracts from `<main>`/`<article>` with a second converter. Lines repeated on more than half the pages are stripped as navigation boilerplate. A JS shell page goes to the browser fallback below.

`crawl_brain.py` is the same crawl with `--brain laya`: a local model ranks each page's links against the goal and the crawl fetches best-first. It matters only when there is a real frontier to rank (no llms.txt, no sitemap; seeds across many domains). Cheap filters (scope, robots, dedupe, path depth) always run first. A wrong ranking changes only order, never content; stopping is still `--max-pages` and the effort budget. With a sitemap or llms.txt, Laya only re-orders the rules' shortlist (rank fusion, so it cannot outweigh the rules), and `status --json` reports how much the two top-10s overlap; no precision is claimed, since nothing knows which pages are truly relevant. Sitemap and llms.txt crawls also follow links: every fetched page promotes the pending pages it links to, weighted by the linking page's relevance and by whether the anchor names a goal term (a page like "Using EXPLAIN" linked from "Performance Tips" has no goal word in its URL). The anchor texts are kept on those pending units for the scorers, and each seed keeps its share of the crawl.

### Browser fallback (agent-browser)

Used for `needs_js` shells (200 with almost no text), and for 403 responses and bot-challenge pages, which get one browser attempt before being marked `blocked`. 401 and 451 never come here. Requires `agent-browser` on PATH (see the `agent-browser` skill); with `--no-browser` or without it a shell stays `needs_js` (and any later run with the browser available retries it) and a 403 or challenge stays `blocked`.

The crawl runs one render at a time, waits the host's normal per-host delay first and skips the host while its circuit breaker is open. Each render escalates:

1. `agent-browser --allowed-domains <host>,*.<host> read <url> --json`: no browser launched; often enough for a JS-heavy page. The result must end on the fetched host.
2. Headless browser: `agent-browser --session <fresh> --allowed-domains <host>,*.<host> --user-agent <Chrome UA> --args "--disable-blink-features=AutomationControlled" open <url>`, then `set viewport 1440 900`, `wait --load networkidle`, `get url`, `read`. The user agent carries the same Chrome major that the fetcher impersonates (curl_cffi), so both present one identity. There is no built-in stealth mode: these two flags are all there is, and no stealth plugin is used.
3. `--headed`: the same launch again, only when step 2 ended on a bot challenge. If the headed page is still a challenge the unit is `blocked`.

After any step the final URL must be on the fetched host and pass the same SSRF and robots.txt checks as any fetch, else the result is dropped. `--allowed-domains` refuses redirects and subresources on other hosts (a private address, a metadata endpoint).

Known gap: the plan called for `--profile ~/.cache/a2s/browser-profile`, but agent-browser 0.36.0 refuses `--allowed-domains` together with `--profile` (and with `--args --user-data-dir`), so every render uses a fresh session and keeps the host pin. Cookies do not persist between renders.

Challenges, logins and paywalls are never solved: a page that is still walled after step 3 is reported as `blocked`. To skim a page by hand, `agent-browser read <url>` (with `--outline` for headings only, or `--llms index|full` for the nearest `llms.txt`) needs no browser launch.

## YouTube (`ingest_youtube.py`, `youtube_brain.py`, `transcribe.py`)

- `yt-dlp --flat-playlist -J` lists a playlist or channel. A bare channel URL lists every tab (videos, streams, shorts), merged and deduplicated; a tab the channel lacks is skipped, a throttled tab fails the listing rather than returning a partial one. Videos are filtered by goal keywords (a keyword count; a two-letter acronym such as `AI` matches as a whole word, and `LLMs` also hits `LLM`) and capped by `--max-videos`. `youtube_brain.py` is the same run with `--brain laya` (yt-dlp plus laya, like `crawl_brain.py` for the web) and ranks instead, only when the listing has more videos than the cap; a listing at or under the cap keeps the keyword filter.
- Laya ranking is a three-stage funnel. Every video is judged in both option orders on a two-option question ("is this video about the topic?"); each stage asks that same question of more evidence, so the scores blend.
  1. **Titles** of every listed video (for a large listing, a shortlist of the best keyword and embedding matches).
  2. **Description, chapter titles and tags** (`yt-dlp -J`) of the best N1 (`--rank-meta`; 15/30/60 for quick/standard/complete, `0` skips).
  3. **Caption excerpts** of the best N2 (`--rank-transcripts`; 6/12/24, `0` skips): three ~300-token windows (start, middle, the chapter mentioning the goal most, else the three-quarter mark). Manual or auto captions only, never speech recognition; a video without captions keeps its stage 2 score.
  The Laya score is the mean of the stages that judged the video, weighted 1:2:3. It is blended 70/30 with the fraction of goal keywords matched (keywords also read the description, chapters and tags once fetched). That becomes the unit priority, and the best `cap` videos are fetched. Chosen videos keep the metadata and captions the funnel already downloaded in `yt-cache/` inside the workspace (deleted once ingested), so nothing is fetched twice; transcripts of videos that were not chosen are discarded. Every yt-dlp call of stages 2 and 3 pauses first (`--sleep-requests`, `--sleep-subtitles`). A 429/403 is logged as a throttle event, waited out (30 s) and retried once. A second one stops that stage, so the ranking falls back to the earlier stages' scores. A wrong ranking changes which videos are fetched but never their content. If Laya is missing or errors, the run warns and uses keywords.
  The record covers the chosen videos, the 30 best skipped, each video's title, description and transcript scores, how many videos each stage scored, whether a stage was throttled, and whether both orders agreed on the top pick. It is kept under `youtube.ranking` in the workspace meta, so `status --json` shows it and `SOURCES.md` lists the kept videos with their stage scores and the top skipped ones.
- Captions: manual first, then auto, as VTT. Rolling duplicate lines in auto-captions are collapsed.
- Chapters become `##` sections with `[mm:ss]` anchors; without chapters, the transcript is grouped by time.
- No captions: the unit is `needs_asr`; `transcribe.py` (`--asr` mode) runs local recognition. Apple Silicon uses MLX Whisper, everything else uses faster-whisper. The first run downloads a model.
- `--frames`: a low-resolution download feeds `ffmpeg` frames at chapter starts and cue phrases ("as you can see", "this slide", "on screen"), deduplicated by perceptual hash, into `assets/frames/`. Needs `ffmpeg`.
- If `deno` is missing or a proof-of-origin token fails, the error appears in the run summary `errors`.

### Deferred, not in v1

Recorded so a later version does not redo the research:

- **Channel RSS feeds** (`/feeds/videos.xml?channel_id=...`): no key, but only the newest ~15 videos, so it cannot enumerate a back catalog. Useful for "what's new since last run".
- **YouTube Data API v3**: exact metadata, quota-limited (10,000 units/day) and needs a key; `captions.download` requires owner authorization, so it cannot fetch third-party captions. The flat-playlist listing gives what is needed without a key.
- **youtube-transcript-api**: convenient for captions but scrapes an undocumented endpoint and breaks when it changes; yt-dlp already covers captions and chapters in one tool.

## Local (`ingest_local.py`, `convert_docling.py`)

- `.md`, `.txt` and `.rst` pass through untouched (a folder of notes needs no heavy dependency). Hidden files and common build directories are skipped.
- PDF, DOCX, PPTX, EPUB, HTML and images are marked `needs_convert`; `convert_docling.py` (`--convert` mode) converts them with docling, which keeps headings, tables and code.
- Fallback chain when a conversion is poor or fails: standard (OCR off, fast tables), accurate (table structure, code and formula enrichment), OCR (Apple Vision on macOS, RapidOCR elsewhere), the `pypdfium2` backend, then `pdftotext -layout`.
- Chapters come from docling headings, and they become the section hints for the plan.
- The first run downloads docling models (about 1 GB).

## Topic

No code. Subagents search the web, return URLs, and the URLs go through `a2s.py seed --urls -` into the web handler. See SKILL.md phase 1.

## Units and statuses

Every input becomes rows (units) in `.cc-arsenal/a2s/<slug>/state.db`. A unit's status is one of `pending`, `done`, `skipped`, `failed`, `needs_asr`, `needs_js`, `needs_convert`, `blocked`. `a2s.py status --json` reports totals per source and every throttle event.
