# Phase Workflow: the four phases, gates, tiering, research fan-out

The detail the SKILL.md body defers. `product-prd` runs four phases; a single
`Phase: X` line in the working notes tracks where a run is (no counters, no
resume machinery).

## The four phases

```
DISCOVER → DECIDE → ═AUTHORIZATION GATE═ → AUTHOR → VALIDATE
```

- **Discover**: ingest the source; inspect the repo before asking anything; tag
  every finding CONFIRMED / INFERRED / UNKNOWN. Then run **gate-zero**.
- **Decide**: pick the tier (size AND intent), fan out research, interview the open
  decisions in dependency order, assemble the ~1-page alignment summary.
- **Authorization gate**: the one hard stop. Author nothing until the user
  explicitly authorizes. On "no": revise and re-present. Never author on silence.
- **Author**: fill the tier's single PRD.md from its template; ID'd, testable,
  traceable requirements; one append-only decision log.
- **Validate**: run `validate.py` + `hygiene.py`, fix CRITICAL/MAJOR, self-grade,
  hand off.

## Gate-zero: does this need a written doc at all?

Before any drafting, ask it plainly. A written PRD is the right tool only when the
work is big or ambiguous enough that a doc reduces back-and-forth. For a one-line
change, a bug-shaped fix, or something faster to prototype than to spec:

> "This doesn't need a PRD. Here's a 3-line ticket: {{problem / change / acceptance}},
> or just prototype it and we'll spec from what we learn."

Say no to the doc when a conversation, a ticket, or a prototype is genuinely enough.
That willingness is the point of gate-zero.

## Tier = size AND intent

Assess size, then (for the big tier) branch on intent. `--tier`/`--intent`
overrides the assessment.

| Tier | When | Output |
|---|---|---|
| **brief** (small) | single feature/addition | one `PRD.md` from `brief.md`, ~2-3 requirements, <30s read |
| **one-pager** (medium) | a module or small app | one `PRD.md` from `one-pager.md`, mandatory non-goals, ≤2pp |
| **big / validation** | "should we build this?" | one `PRD.md` from `prfaq.md`, press release + FAQ + top-3 failures |
| **big / execution** | "we've decided; build it" | one `PRD.md` from `prd-full.md`, numbered reqs, baseline/target/window metrics, dated changelog |

Single file is the default at **every** tier. Split a section into its own file
only when it outgrows itself; reach for `scaffold.py --enterprise` only for a
platform-scale program that genuinely needs the multi-file tree.

### Size signals

| Signal | heavier | lighter |
|---|---|---|
| Components affected | frontend+backend+data+infra | single |
| Security / privacy sensitivity | auth, payments, PII, regulated | none |
| External integrations | 2+ services/APIs | self-contained |
| Estimated requirement count | 30+ | <12 |
| Domain familiarity | unfamiliar / greenfield | well-understood |

On a boundary, ask the user which tier rather than guessing.

### Graduating guard

If a **one-pager** draft exceeds ~5-7 requirements or the scope touches more than
one team/system, **stop and restart in `prd-full.md`** rather than bloating the
one-pager in place. Bloating a lighter template is the failure mode this guard prevents.

## Discovery mode: pick by context

- **Cold start:** ask 3-5 lettered clarifying questions (terse answers like "1A,2C,3B").
- **Warm start (already discussed):** synthesize from the conversation + a quick repo
  scan, but always run a lightweight completeness/gap check before finalizing, or
  the PRD inherits whatever was wrong in the prior context. Tag remaining gaps
  `[NEEDS CLARIFICATION: ...]`.

## Research fan-out

Pick only the workstreams the open decisions depend on. Common ones:

| Workstream | Looks for | Feeds |
|---|---|---|
| Competitors & market | direct/indirect products, pricing, gaps | scope, differentiation, non-goals |
| Technical options | frameworks, data stores, build-vs-buy | architecture, NFRs, dependencies |
| Regulatory / privacy / security | GDPR/CCPA, data residency, OWASP | SEC/DATA requirements |
| Platform conventions | HIG, Material, web standards | UX requirements |
| Accessibility | WCAG 2.2 AA obligations | UX/DES requirements (delegated to review-design) |

Fan out one `Explore`/haiku agent per workstream in a single parallel batch (or run
the same `WebSearch` queries sequentially with no Task tool). Each returns rows
`finding | source URL | date | confidence | implication` and invents nothing.
Merge into the decision log as `finding` rows. Triangulate any legal/security claim
across ≥2 independent sources before treating it as HIGH.

Source authority order (higher overrides lower on conflict): law/regulation →
formal standards → first-party vendor docs → peer-reviewed → reputable press →
forums/blogs.

## Gate discipline

| Gate | Between | Passes when | On fail |
|---|---|---|---|
| Gate-zero | Discover → Decide | a written doc is actually warranted | emit a ticket / "go prototype", stop |
| Authorization | Decide → Author | user explicitly authorizes authoring | revise, re-present; never author |
| Validation | Author → done | 0 CRITICAL, 0 MAJOR from `validate.py` | fix findings, re-run |

## Knowledge categories: keep them separate

- **Facts**: verified from the repo or a cited source (CONFIRMED).
- **Assumptions**: working beliefs pending validation → decision log (`assumption`).
- **Decisions**: choices the user approved → decision log (`decision`).
- **Recommendations**: your evidence-based advice; never rendered as an approved
  requirement until a decision approves it.
- **Findings**: externally sourced, always cited → decision log (`finding`).

Blurring these is the most common PRD failure. A recommendation the user hasn't
approved is not a requirement.
