# README + description checklist

Load this before writing Stage 4's README. Rewrite the whole file to this shape rather than patching the existing one piecemeal — a launch README reads in a different order than a working README.

## Order that matters

1. **One-line value prop** — what it does and who it's for, before any badge or install step. Pull this from what the code actually does (read the entry point / main module), not from aspiration.
2. **Badges** (optional) — build status, license, package version. Only add a badge for something that actually exists (a CI workflow file, a published package) — a badge pointing at a pipeline that doesn't exist is worse than no badge.
3. **Demo asset** — a screenshot or GIF if one already exists in the repo or was produced in Stage 3; link it, don't fabricate a placeholder image path that doesn't resolve.
4. **Install** — the real command for the real package manager/language (`npm install`, `pip install`, `cargo add`, `go get`) detected from the manifest file, not assumed.
5. **Usage** — the smallest working example, ideally copy-pasted from an existing test or example file so it's guaranteed to run.
6. **Contributing / License footer** — link to `CONTRIBUTING.md` if it exists, name the license Stage 1 confirmed.

## Repo description and topics

`gh repo edit --description` (GitHub's short one-liner, ~350 char limit) should match the README's opening value-prop sentence, not restate the whole README.

Topics: 5-10 lowercase, hyphenated keywords a search would actually use — draw them from:
- The primary language(s) (`typescript`, `python`, `rust`)
- The framework/runtime in the manifest (`nextjs`, `fastapi`, `cli`)
- The problem domain, described plainly (`browser-automation`, `code-review`, `image-generation`) — not marketing adjectives (`ai-powered`, `next-gen`)

```bash
gh repo edit --description "Headless browser automation CLI optimized for AI agents" \
  --add-topic browser-automation --add-topic cli --add-topic typescript
```

Never add a topic or description claim the codebase doesn't back up — a mismatched description is the first thing a visitor notices.
