# Generated skill layout

## Anatomy

```
<name>/
  SKILL.md                         hub: frontmatter + routing table, under 500 lines
  references/
    INDEX.md                       one line per file
    best-practices.md              authored, sourced
    SOURCES.md                     provenance of every input
    <section>/<file>.md            packed source pages, always in a section folder
    <video-slug>/<chapter>.md      one folder per chaptered video, one file per chapter
    videos/<title-slug>.md         chapterless videos
    examples/*.md                  authored worked examples
  assets/frames/<video-slug>/<mm-ss>.png   video sources only, with --frames
  evals/ evals.json trigger-eval.json
```

Frontmatter is `name` and `description` only. No `allowed-tools`, hooks or other keys that widen what the skill can do; the generated skill carries no authority beyond reading its own references.

## Plan rules

- **Sections**: source files are never flat next to `INDEX.md`, `SOURCES.md`, `best-practices.md` or `examples/`. The first hint segment is the section; sections under 3 files merge into `general`; a section over 25 files splits by its second path segment or page-name prefix. A page that packs into 3+ files gets its own folder. Numbered siblings are the last resort when no such cluster exists. At most about 15 sections, depth at most 2.
- Names: no uploader or channel prefix, no video id, no timestamp, apostrophes dropped before slugging (`dont`, never `don-t`), at most about 40 characters cut at a word boundary, and a file name never repeats its folder's whole name (`app-psql/usage.md`, not `app-psql/app-psql-usage.md`).
- Videos: each video with chapters is a folder named by a short title slug (main clause, filler words dropped: `uncle-bob-software-fundamentals`) holding one file per chapter named by the chapter title (`agent-loop-dynamics.md`); the `[mm:ss]` anchors stay inside the files. A chapter over 8k tokens splits into `<chapter>-part-N`. A chapterless video is `videos/<title-slug>.md`, or lands in a topic section when a shared section hint (or a judge move) puts it with other pages. A video's channel is never a section. A video always keeps its own folder: it is not folded into `general` or merged by slug.
- Frames: `--frames` stills are filed at emit as `assets/frames/<video-slug>/<mm-ss>.png` and the links in reference files are rewritten to match; only linked frames are copied.
- **Same slug across sources merges, unless two web hosts collide.** A docs site and a video that both cover "indexing" land in one `indexing/` section, never under a per-source folder. When two web hosts share a first segment (both have `sql/`) or both leave pages to `general`, each host gets its own host-qualified section (`docs-example-sql`, `docs-example-general`); otherwise the plain hint is the name. A name is never doubled (`sql-sql`). `SOURCES.md` still lists every origin.
- **Files**: target 1.5k-4k tokens, hard maximum 8k. Pages under 800 tokens are concatenated, each under its own `##` with a source line. Pages over 8k split on `##`, then `###`, then paragraphs; fenced code is never split.
- Files over 300 lines get a table of contents. Each file opens with a one-line summary and its source URL. The summary is the first real sentence under each of the first few headings, preferring one that names a goal keyword, then the first of 8+ words. Banners, dates, navigation rows, bylines, site calls to action, greeting openers, transcript timestamps and lines repeated across a host's pages are skipped. A video's summary is its chapter titles (else its description, else its title), never a transcript line.
- A page split for size names its files by their first `##` heading (`app-psql-meta-commands.md`), skipping Note/Tip boxes; a slice with no heading of its own continues the previous heading as `<heading>-part-N` (title `(part N)`), and `review.md` lists each part's own headings.
- **Hints** come from the URL path minus noise segments (docs, en, latest, version numbers), the relative file path, or docling heading breadcrumbs. A video is named by its title, never its URL or channel.
- **Priority** rises with llms.txt membership, shallow depth and goal-keyword hits, and falls for near-duplicate content.

## INDEX.md line format

```
references/indexing/btree.md — how B-tree indexes are searched and when they are used (~3k tok) [concept]
```

Path, an em dash, a one-line summary, approximate size, and the judge's kind when known.

## Hub SKILL.md template

The hub routes; the references teach. Keep it under 300 lines.

```markdown
---
name: <name>
description: <what it covers and the concrete triggers: "Use when ...">. <what it does not cover>.
---

# <Title>

<Two sentences: what this skill holds and where it came from.>

## When to use
<Bullets naming the tasks and phrases that should load this skill.>

## Core workflow
<Three to seven numbered steps for the common task, each pointing at a reference file.>

## Top practices
<Five to ten sourced rules, each `(src: <id> "quote")`, each one line.>

## Routing table
| Task | Read |
|---|---|
| <task in the user's words> | references/<section>/<file>.md |

## Not covered
<What the sources did not include, so the agent does not guess.>
```

Rules for the hub:

- The description states what the skill covers and when to trigger it, in third person, with a "Not for" clause when a neighbor skill exists. It is the only text always in context.
- Every routing row points at a file that exists (`verify` checks it) and describes the task, not the file's title.
- Facts, numbers and recommendations carry a source marker; connective prose does not need one.
- Keep reference content out of the hub: a paragraph that could live in a reference file belongs there.

## Grounding markers

In authored files, a claim reads `... (src: 42 "exact quote of at most twenty words")`. Here 42 is a unit id, and the quote must appear in that unit's text (case and whitespace normalized). At emit time each marker becomes a relative link to the reference file that holds the unit. Code blocks carry no marker; they are checked by verbatim match against the corpus instead.

Write the claim in your own words and let the marker carry the quote. Do not also quote it in the prose: the emitted line would read the quote twice (`"..." ("..." [source](...))`), and `emit` and `verify` warn when they see it. Quote a whole clause too: under 5 words is warned as a probable mid-clause cut.

```markdown
- Trim the prompt to the minimum, because the middle of a long context is neglected (src: 2 "is to trim that initial prompt down to its absolute minimum").
```

## SOURCES.md

Generated by `emit`: one row per input with its type, URI, fetch date and unit count, plus the licensing note that verbatim mirrors are for private use unless the source's license allows redistribution. Deliberate drops (judge, budget, duplicate, `a2s.py drop`) are listed, capped at 30 with per-reason counts for the rest. A page you dropped is a drop whether or not it was fetched (a dropped video also shows as `dropped` in its ranking); only pages never fetched and never dropped appear as counts per source and status.
