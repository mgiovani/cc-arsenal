# Interview

Phase 0 collects every decision before any fetching starts. Ask everything in one batch: `AskUserQuestion` where the tool exists (one call, several questions), otherwise one plain-text message with a numbered list. Skip anything the user already stated. If the user says "just use defaults", use the defaults column and confirm them in one line.

| # | Question | Options / format | Default |
|---|---|---|---|
| 1 | What are the sources? | URLs, paths, YouTube links, or "just a topic" | none (required) |
| 2 | How much corpus? | `quick` (~50k tokens), `standard` (~200k), `complete` (mirror every page, no cap) | `standard` |
| 3 | What should the skill know? | free text: the goal, or for a channel the topics wanted | none (required) |
| 4 | Extra instructions? | free text: audience, tone, must-include, must-avoid | none |
| 5 | Expand with a web search? | yes / no | yes for a topic, no otherwise |
| 6 | Where should it go? | path | `.agents/skills/<name>` |
| 7 | Skill name? | lowercase-hyphen, at most 64 characters | derived from the goal |

## Effort

Effort is the corpus token budget for the whole run, across sources.

| Effort | Corpus budget | Use when |
|---|---|---|
| `quick` | ~50k tokens | a focused skill from one small site or a few videos |
| `standard` | ~200k tokens | most docs sites; the default |
| `complete` | unbounded | the user wants everything mirrored; the judge never drops pages |

## Getting a usable goal

The goal drives ranking, video filtering, the judge and the hub's routing table. A vague goal ("PostgreSQL") makes all four worse. If the goal is a bare noun, ask one follow-up: what will the agent using this skill be asked to do? Store the answer in the goal, for example "best practices for psql, SQL, indexing and query performance", not "PostgreSQL".

## Output location

- Default `.agents/skills/<name>`, the tool-neutral location.
- If Claude Code is in use, run `emit --link-claude` to also create a relative symlink `.claude/skills/<name>` pointing at it. It refuses to overwrite an existing path.
- A user-global skill goes under their home skills directory: pass that path as `--out`.

## Non-interactive runs

When there is no way to ask (an automated run), the caller supplies the answers in the prompt. Pass them straight to `a2s.py init` and skip the interview; still show the phase 5 tree in the final report even if approval is pre-granted.

## After the interview

```bash
uv run <skill-dir>/scripts/a2s.py init <slug> --goal "..." --effort standard \
  --out <path> --name <name> --instructions "..."
```

The slug is the workspace name under `.cc-arsenal/a2s/`. Use the skill name. Add `.cc-arsenal/` to `.gitignore` if the project is a git repository.
