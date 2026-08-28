---
name: product-prd
description: >-
  Gate-checked, size-and-intent-tiered PRD authoring. Runs a gate-zero first (is
  a written doc even needed, or is a 3-line ticket or a prototype enough?), then
  a Brief, one-pager, or big-tier stack; the big tier branches on intent: a
  PR/FAQ for validation versus a numbered full PRD for execution. Enforces
  positive, mandatory non-goals at medium and up, ID'd testable traceable
  requirements, and ends in a hand-off plus a self-grade. Use for "write a PRD",
  "draft product requirements", or "spec out this product". Writes no code. Not
  for the design spec (use product-design-spec), the visual token system (use
  product-design-tokens), or a single decision record (use docs-adr or docs-rfc).
metadata:
  author: mgiovani
  version: 2.0.0
disable-model-invocation: true
argument-hint: "<idea | file | url | #issue | PROJ-123> [--tier brief|one-pager|big] [--intent validation|execution]"
context: fork
agent: general-purpose
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(git *), Bash(gh *), Bash(python *), Bash(uv run *), Task, WebSearch, WebFetch, AskUserQuestion, Skill
---

# Product PRD

Author the *right* product doc for the work (sometimes a 3-line ticket, sometimes a full PRD), never more
than the work warrants. This skill **writes no application code**; it produces the requirements a build
(`implement-feature`, `team-implement`) then works from. Output lands under `docs/specs/prd/`.

## Input

$ARGUMENTS

Parse the source (first match wins), then read it:

| Pattern | Source | Read via |
|---|---|---|
| `PROJ-123` | Jira | `jira issue view PROJ-123` |
| `#42` / `owner/repo#42` | GitHub issue | `gh issue view 42 --json title,body,labels,comments` |
| `!123` / PR URL | GitHub PR | `gh pr view 123 --json title,body,files` |
| existing path | file/dir | Read it (dir: README, CLAUDE.md/AGENTS.md, key files) |
| `http(s)://` | URL | `WebFetch` |
| anything else | plain text | the idea itself |

A trailing `--tier brief|one-pager|big` and/or `--intent validation|execution` overrides the assessment.

## Prerequisites & fallback

Parallel research and discovery use the `Task` tool with `Explore`/haiku subagents. **No `Task` tool?** Run
every research and discovery step inline, sequentially: the phase → gate → phase structure below is the
workflow; subagents are just how it parallelizes.

## Lean by default

The organizing principle. **Default to a single `docs/specs/prd/PRD.md`** and split a section into its own
file only when it outgrows itself. Length is not quality: a bloated PRD and a tight one get rated worlds
apart on content alone. Cut anything not traceable to the problem, a goal, or a success metric.

- Track position with a single **`Phase: X`** line in your working notes: no per-turn counters, no resume state.
- **Cost stop-condition:** if the work seems to want a large multi-file tree, **stop and ask** before emitting
  it. Never auto-generate a 12- or 37-file document set. That tree exists only behind
  `scripts/scaffold.py --enterprise <tier>`, for a platform-scale program that has genuinely outgrown one file.

## Tiers: size AND intent

Gate-zero decides *whether* to write a doc; the tier decides *which* doc. Full detail:
`references/phase-workflow.md`.

| Tier | When | Template |
|---|---|---|
| **brief** (small) | single feature/addition | `assets/templates/brief.md`, ticket-shaped, ~2-3 reqs, <30s read |
| **one-pager** (medium) | a module or small app | `assets/templates/one-pager.md`, mandatory non-goals, ≤2pp |
| **big / validation** | "should we build this?" | `assets/templates/prfaq.md`, press release + FAQ + mandatory top-3 failures |
| **big / execution** | "we've decided; build it" | `assets/templates/prd-full.md`, numbered reqs, baseline/target/window metrics, dated changelog |

**Graduating guard:** if a one-pager draft exceeds ~5-7 requirements or the scope touches more than one
team/system, **stop and restart in `prd-full.md`** rather than bloating the one-pager in place.

## Workflow

Four phases: **Discover → Decide → ═authorization gate═ → Author → Validate.**

### Phase: Discover

Read the input source. If the repo is relevant (existing product), inspect it before asking the user
anything: spawn an `Explore`/haiku agent (or do it inline):

```
Task (Explore, haiku): "Discover this repo's product surface & stack: read CLAUDE.md/AGENTS.md, README,
package/build files; map major components, data model, existing capabilities, and any current PRD/specs
under docs/. Return a structured summary, each finding tagged CONFIRMED | INFERRED | UNKNOWN."
```

Tag every finding **CONFIRMED / INFERRED / UNKNOWN**: never present an inference as a fact. Pick the
discovery mode by context: cold start → 3-5 lettered clarifying questions; warm start → synthesize from the
conversation + a quick repo scan, then run a lightweight gap check.

**Gate-zero: does this even need a written doc?** For a one-line change, a bug-shaped fix, or anything
faster to prototype than to spec, say so and stop:

> "This doesn't need a PRD. Here's a 3-line ticket: {problem / change / acceptance}, or just prototype it
> and we'll spec from what we learn."

Being willing to talk the user out of a doc is the point of gate-zero.

### Phase: Decide

1. **Pick the tier**: assess size, then branch the big tier on intent (validation vs execution). Honor
   `--tier`/`--intent` if passed. State the choice and why in one line.
2. **Research**: fan out one `Explore`/haiku agent per workstream the open decisions actually need
   (competitors, technical options, regulatory, platform, accessibility). Each returns rows
   `finding | source URL | date | confidence | implication` and invents nothing. Merge them as `finding`
   rows in the one **decision log** (`assets/templates/decision-log.md`). Cite every externally-derived claim.
3. **Interview**: ask the open decisions in dependency order (vision → problem → users → scope → journeys →
   architecture → non-functional → metrics), each via `AskUserQuestion` with the `decision-question.md`
   template (decision, evidence, a recommendation with rationale, alternatives). Record answers as
   `decision`/`assumption`/`question` rows in the same log. Keep facts, assumptions, and recommendations
   separate: a recommendation never hardens into a requirement without an approved decision. For the
   **users** decision, capture persona and user evidence with `product-design-spec`'s `persona.md`
   rulebook (via the `Skill` tool where available, else read `persona.md` from
   `skills/product-design-spec/assets/templates/`) rather than duplicating persona guidance here.
4. **Alignment gate (authorization)**: assemble the ~1-page `alignment-summary.md` and present it:

   > "Alignment summary for {product}: tier = {tier}, {N} approved decisions, {M} assumptions, {K} open. Do
   > you authorize me to author `docs/specs/prd/PRD.md`?"

   **Stop here if the answer is no**: revise and re-present. Author nothing before authorization.

### Phase: Author

Create the single file, then fill it from the tier template:

```bash
python skills/product-prd/scripts/scaffold.py --dir docs/specs/prd   # one PRD.md
```

- **Requirements** use `assets/templates/requirement.md`: a unique ID (`PRD-<CAT>-NNN`, six categories
  FR/NFR/UX/SEC/DATA/DES), RFC-2119 language, **one behaviour** per requirement, a 3-field evidence block
  (finding / evidence path / confidence), and **Given/When/Then** acceptance criteria. Rules:
  `references/requirement-hygiene.md` (the shared rulebook) and `references/requirement-standards.md`.
- **Non-goals are mandatory at medium+ and stated POSITIVELY**: say where the excluded work lives or when
  it's revisited, never a bare "we won't do X" (a downstream agent can't infer scope from omission).
- **Tag every unresolved gap `[NEEDS CLARIFICATION: ...]`** rather than guessing: it stays greppable.
- **Prioritization/metrics** (JTBD/Kano/MoSCoW/RICE, NSM/HEART/AARRR) are opt-in: reach for
  `references/frameworks.md` only when finer granularity is actually wanted.
- **Diagrams:** delegate Mermaid to the `docs-diagram` skill (via the `Skill` tool where available,
  otherwise apply its diagram conventions inline). **Task breakdown once requirements exist:** hand off to
  `project-planner`. **A decision worth a permanent record:** offer `docs-adr` (made) / `docs-rfc` (proposed).

### Phase: Validate & hand off

```bash
python skills/product-prd/scripts/validate.py --dir docs/specs/prd   # gate: 0 CRITICAL, 0 MAJOR
python skills/product-prd/scripts/hygiene.py  --dir docs/specs/prd   # advisory INVEST/EARS lints
```

Fix every CRITICAL/MAJOR (missing/duplicate IDs, ACs without Given/When/Then, missing Non-Goals, unresolved
`[NEEDS CLARIFICATION]`, compound requirements, dangling links, leftover placeholders). Then:

- **Self-grade** inline (no separate report file): does every requirement trace to a stated goal? Any vague
  terms, missing sections, or compound requirements left? State the readiness verdict in a sentence or two.
- **Hand off:** write the file to its repo path (report the path), or, if the user works in a tracker, offer
  to open the ticket/issue. Name the downstream consumer: `product-design-spec` (design) and
  `implement-feature`/`team-implement` (build).

## AI-agent-consumer mode (optional)

When the PRD's downstream reader is an AI implementation agent (this repo's own `implement-feature`/`fix-bug`)
rather than a human, switch modes. **Use headings + lists over prose; state every non-goal positively; give every
requirement an independently-testable acceptance criterion.** Optionally emit the companion
`assets/templates/agent-contract.md`: exact commands with flags, an Always / Ask-First / Never boundary
list, and project conventions.

## Anti-hallucination

- Investigate the repo and search the web **before** asking the user: don't ask what the code already answers.
- Tag every finding CONFIRMED / INFERRED / UNKNOWN; never present an inference or a recommendation as a fact
  or an approved requirement.
- Every externally-derived claim carries a source. No fabricated counts, metrics, or competitor data.
- Never invent requirement IDs that don't trace to a decision or need. Run `validate.py` before declaring done.
- The alignment gate is real: author files only after explicit authorization.

## References

- `references/phase-workflow.md`: the four phases, gate-zero, size+intent tiering, graduating guard, research fan-out
- `references/requirement-hygiene.md`: RFC-2119, the 8-term vague blocklist, INVEST, EARS, compound-split, `[NEEDS CLARIFICATION]` (shared with product-design-spec)
- `references/requirement-standards.md`: the six-category ID scheme, requirement quality, the one decision log
- `references/frameworks.md`: opt-in prioritization (JTBD/Kano/MoSCoW/RICE) & metrics (NSM/HEART/AARRR) pipelines
- `assets/templates/`: brief, one-pager, prfaq, prd-full, requirement, decision-question, decision-log, alignment-summary, agent-contract, prd-root
- `scripts/scaffold.py` · `scripts/validate.py` · `scripts/hygiene.py`

## Boundaries

- The design half (IA, flows, screens, states) → `product-design-spec`.
- The visual token system (DTCG / DESIGN.md) → `product-design-tokens`.
- A single architecture/decision record → `docs-adr` (records a made decision) or `docs-rfc` (proposes one).
- A lightweight spec that immediately precedes coding → `team-implement` / `implement-feature`.
- Auditing an existing design's UX → `review-design`. Rendering visual assets → `codex-imagegen`.
- WHAT/WHY only, never HOW. Writes no application code.
