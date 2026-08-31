# Wrapping another skill

`render /<skill> [args]` runs that skill to completion, then renders what it
produced. The wrapped skill is never modified and never needs to know this skill
exists.

## Mapping

| Wrapped skill | Mode | What becomes an anchored item |
|---|---|---|
| `review-code`, `review-security`, `review-perf`, `review-design` | `review` | one finding |
| `team-review` | `review` | one finding, grouped by the agent that raised it |
| `review-plan` | `review` | one objection to the plan |
| `docs-check`, `i18n-check`, `env-setup` | `audit` | one gap |
| `review-deps` | `audit` | one package |
| `test-suite` (its analysis pass) | `audit` | one uncovered path |
| `vrt-check` | `review` | one changed component, with its image triptych |
| `project-planner`, `implement-feature`, `orchestrate` | `plan` | one step |
| `clotho-research` | `map` | one file or risk the change touches |
| `docs-adr`, `docs-rfc` | `compare` | one alternative considered |
| `find-skills` | `compare` | one candidate skill |
| `product-prd` | `prd` | one requirement |
| `prd-to-issues` | `prd` | one requirement, with the issue it became |
| `product-design-spec` | `prd` | one screen, traced to its requirement |
| `docs-diagram` | `map` | one component |

A skill not in this table still works: run it, look at the shape of its output,
and pick the mode from the table in SKILL.md. Say which mode you picked.

## Rules

- **Run the skill first, completely.** Do not render a partial result, and do not
  substitute your own analysis for the skill's.
- **Do not restate its findings in your own words.** The page renders what it
  produced. Rewriting the content while reformatting it loses the evidence the
  wrapped skill gathered.
- **Keep its severity and ordering.** If the skill ranked its output, the page
  preserves that rank. Regrouping for filters is fine; silently reordering by
  your own judgment is not.
- **Carry the evidence.** File and line, the command that produced a number, the
  source a claim rests on. These become the detail under each anchored item, and
  they are what make the page reviewable rather than assertive.
- Skills that produce actions rather than findings are not worth wrapping. Every
  `git-*` skill, `ship`, `gitflow`, `docker-init`, `ci-generate`, `create-rule`,
  `create-skill`, `improve-skill`, `inject-docs`, `db-migrate`, `agent-browser`,
  the image generators, and `wtf`. If asked anyway, say why a page adds nothing
  and offer the bare skill.
