<!-- template: state-shortlist: the ~10 core screen states. For each CRITICAL screen,
     cover the APPLICABLE SUBSET, never just the happy path. Add others only if
     applicable to that surface. scripts/screen-states.py requires the empty / error /
     permission-denied trio unless a screen marks it N/A with a reason. -->

# Screen state shortlist

The core states every critical screen is checked against. Cover the subset that applies to the surface: a
static marketing page has no validation-error; a form has no offline concern if it's local-only. But do not
skip a state just because it's tedious: the trio **empty / error / permission-denied** is the one authors most
often forget and users most often hit.

| # | State | When it shows | Required? |
|---|---|---|---|
| 1 | **loading** | data in flight, skeleton or spinner | if the screen fetches |
| 2 | **empty** | no data yet, first run, or zero results | **yes** (or N/A + reason) |
| 3 | **populated** | the default content state | yes |
| 4 | **validation-error** | user input is invalid (inline, field-level) | **yes** if the screen takes input |
| 5 | **recoverable-error** | a system/network failure the user can retry | **yes** (error trio) |
| 6 | **permission-denied** | the user isn't allowed (403, locked, gated) | **yes** (or N/A + reason) |
| 7 | **offline** | no connectivity | where relevant |
| 8 | **success** | an action confirmed | if the screen has a primary action |
| 9 | **disabled / read-only** | the surface or an action is inert | where relevant |

## Add others only if applicable

Extend the list for this surface when it genuinely has more states, e.g.:

- **onboarding / first-run** (distinct from generic empty)
- **no-search-results** (distinct from empty)
- **expired-session** / re-auth
- **partial / optimistic** (an action applied before the server confirms)

Do not pad the list to look thorough. A state that can't occur on this surface should be marked
`N/A: <reason>`, not invented.
