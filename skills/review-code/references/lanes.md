# Conditional Lanes

Lanes the review adds when the diff touches their area. Load this file at lane selection (SKILL.md step 2) and again when building each lane agent's prompt. Core lanes (agents 1-6) and Architecture live in `agent-prompts.md` and `architecture-patterns.md`.

## Contents

- [How lanes run](#how-lanes-run)
- [security-fe](#lane-security-fe)
- [security-be](#lane-security-be)
- [deps](#lane-deps)
- [perf-deep](#lane-perf-deep)
- [design-motion](#lane-design-motion)

## How lanes run

- Every lane agent is spawned with `model: "sonnet"` set explicitly. Never leave it inherited and never use haiku.
- A lane agent reviews only the changed files that match its triggers, plus the lines around them for context. Hunk ranges from Scope decide `preexisting`.
- Each lane writes `<scratch>/findings/<lane>.json` as `{"lane": "<lane>", "findings": [...]}` using the finding shape in `agent-prompts.md`.
- Composition rule: each lane borrows a sibling skill's checklist, never its workflow. The sibling's own phases (target detection, report format, follow-up) do not run here. Skip its report template and emit findings in the shared shape.
- Sibling paths are relative to the sibling skill's directory: `skills/<sibling>/references/<file>` in a checkout, `../<sibling>/references/<file>` from this skill's directory when installed as a plugin. If the file is missing, run the lane from the check lists below alone.
- A lane that matches no changed file is skipped with a one-line reason in the lane-selection line.
- A `*.md`-only or docs-only diff triggers none of these lanes.

## Lane: security-fe

Prefix `SEC-`. Findings file `security-fe.json`.

**Triggers.** Changed files match any of:
- `**/*.{tsx,jsx,vue,svelte,html}`, `**/components/**`, `**/pages/**`, `**/app/**` (UI code)
- client auth or session code: paths containing `auth`, `session`, `login`, `token`, `oauth`, `sso`
- `**/middleware.*`, `next.config.*`, `vite.config.*`, CSP or header config
- code that reads or writes `localStorage`, `sessionStorage`, `document.cookie`, `postMessage`, `dangerouslySetInnerHTML`, `innerHTML`, `v-html`, `eval`

**Composition.** Use the `review-security` skill's agent prompts and category patterns (via the `Skill` tool where available, otherwise load `skills/review-security/references/agent-prompts.md` and apply it inline). Take only the frontend subset:
- "Agent 2 - Configuration & Design", the **A02 - Security Misconfiguration Patterns** block (CSP, CORS, headers, debug flags, default config)
- "Agent 3 - Injection & Data Integrity", the **A05 - Injection Patterns** block (DOM XSS, HTML injection, unsafe URL schemes, template injection) and the **A08 - Data Integrity Failures** block (unsafe deserialization, unverified third-party scripts, missing SRI)

Announce it with `Using review-security to scan the client-side changes`.

**Client-side checks on top of the borrowed blocks.**
- Tokens or PII in `localStorage`/`sessionStorage`; cookies missing `HttpOnly`, `Secure` or `SameSite`.
- Auth state decided only in the client (a hidden button or route guard with no server check behind it).
- `postMessage` handlers that do not check `event.origin`; `window.open` or links with `target=_blank` and no `rel="noopener"`.
- Open redirects built from `?next=`, `returnTo` or `redirect` params without an allowlist.
- Secrets or private keys in bundled env vars (`NEXT_PUBLIC_*`, `VITE_*`, `REACT_APP_*`).
- Query or cache layers not cleared on sign-out, 401 or identity change, so the next user on a shared workstation sees the last user's data.
- Production config that silently falls back to a dev or localhost endpoint.
- Logging of tokens, form values or PII to the console or analytics.

**Prompt for the lane agent.**

```
Agent - Security (frontend), prefix SEC-, model sonnet:
- prompt: "Review the client-side security of the changes in [FILES_LIST] (only files matching the security-fe triggers). Use the review-security patterns for A02 Security Misconfiguration, A05 Injection and A08 Data Integrity Failures, loaded from the sibling skill's references/agent-prompts.md, plus the client-side checks below. Project rules to also enforce: [PROJECT_RULES].

[CLIENT_SIDE_CHECKS]

For each finding: read the surrounding code, trace where the value comes from and where it goes, and confirm an attacker can reach it before reporting. Report the exploit path in one or two sentences. Severity: Critical for reachable XSS, token theft or auth bypass; Major for missing hardening on a sensitive flow; Minor for defense-in-depth gaps. Set preexisting=true when the line is outside every changed hunk.

Write findings to [SCRATCH]/findings/security-fe.json as {\"lane\": \"security-fe\", \"findings\": [...]} using the shared finding shape, ids SEC-001 upward. Analysis only: do not edit code."
```

## Lane: security-be

Prefix `SEC-`. Findings file `security-be.json`. Ids continue from SEC-100 so they never collide with `security-fe`.

**Triggers.** Changed files match any of:
- server code: `**/api/**`, `**/routes/**`, `**/controllers/**`, `**/handlers/**`, `**/services/**`, `**/models/**`, `**/db/**`, `**/server/**`, `**/*.py`, `**/*.go`, `**/*.rs`, `**/*.java`, `**/*.rb` outside test dirs
- auth, permissions, session or token code on the server side
- config and secrets: `.env*`, `**/settings*`, `**/config/**`
- infra and CI: `Dockerfile*`, `docker-compose*`, `*.tf`, `*.tfvars`, `k8s/**`, `helm/**`, `.github/workflows/**`, `.gitlab-ci.yml`, `Jenkinsfile`

**Composition.** Use the `review-security` skill's agent prompts and category patterns (via the `Skill` tool where available, otherwise load `skills/review-security/references/agent-prompts.md` and apply it inline). Take the backend subset:
- "Agent 1 - Access Control & Authentication", **A01 - Broken Access Control Patterns** and **A07 - Authentication Failures Patterns**
- "Agent 2 - Configuration & Design", **A02 - Security Misconfiguration Patterns** and **A06 - Insecure Design Patterns**
- "Agent 3 - Injection & Data Integrity", **A05 - Injection Patterns** and **A08 - Data Integrity Failures**
- "Agent 4 - Cryptography & Supply Chain", **A04 - Cryptographic Failures**, only when crypto, hashing or token signing code changed
- "Agent 6 - Logging, Monitoring & Exception Handling", **A09** and **A10**, only when error or logging paths changed

Skip "Agent 5 - Bytecode & Compiled Code Security" and the A03 supply-chain block (the `deps` lane owns that). Announce it with `Using review-security to scan the server and infra changes`.

**Infra and config checks on top.**
- Containers running as root, `latest` tags, secrets baked into image layers or build args.
- IaC with public buckets, `0.0.0.0/0` ingress, wildcard IAM actions or resources.
- CI workflows using `pull_request_target` with a checkout of PR code, unpinned third-party actions, `${{ github.event.* }}` interpolated into `run:` steps, secrets exposed to forks.
- Missing authorization on new routes (compare with sibling routes), IDOR on ids taken from the request, mass assignment from request bodies.
- Production config that silently falls back to dev endpoints, test credentials or disabled TLS verification.

**Built-in `/security-review`.** When the host has a built-in `/security-review` command or skill, run it as one extra pass over the same diff and merge its findings into `security-be.json` (dedup by path, line and title; keep the sharper description). When it is absent, say so in the lane line and continue. Its absence is not a failure.

**Prompt for the lane agent.**

```
Agent - Security (backend and infra), prefix SEC-, model sonnet:
- prompt: "Review the server, config and infrastructure changes in [FILES_LIST] (only files matching the security-be triggers). Use the review-security patterns for A01, A07, A02, A06, A05 and A08 (plus A04, A09, A10 when relevant), loaded from the sibling skill's references/agent-prompts.md, plus the infra and config checks below. Project rules to also enforce: [PROJECT_RULES].

[INFRA_AND_CONFIG_CHECKS]

For each finding: trace the request path from entry point to sink, check what auth and validation already run, and confirm the issue is reachable before reporting. Compare a new route with its siblings to spot a missing guard. Severity: Critical for auth bypass, injection or exposed secrets; Major for a missing control on a sensitive path; Minor for hardening gaps. Set preexisting=true when the line is outside every changed hunk.

Write findings to [SCRATCH]/findings/security-be.json as {\"lane\": \"security-be\", \"findings\": [...]} using the shared finding shape, ids SEC-101 upward. Analysis only: do not edit code. Never print secret values; cite file and line only."
```

## Lane: deps

Prefix `DEP-`. Findings file `deps.json`.

**Triggers.** A manifest or lockfile changed: `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `bun.lock`, `bun.lockb`, `pyproject.toml`, `uv.lock`, `poetry.lock`, `requirements*.txt`, `Pipfile.lock`, `Cargo.toml`, `Cargo.lock`, `go.mod`, `go.sum`, `Gemfile`, `Gemfile.lock`, `pom.xml`, `build.gradle*`, `composer.json`, `composer.lock`.

**Composition.** Use the `review-deps` skill's audit commands and analysis dimensions (via the `Skill` tool where available, otherwise load `skills/review-deps/references/audit-commands.md` and `skills/review-deps/references/agent-prompts.md` and apply them inline). Announce it with `Using review-deps to audit the dependency changes`.
- Run the audit command for each ecosystem detected, from `audit-commands.md` (npm, yarn, pnpm, pip-audit, uv and the rest listed there). Read-only commands only. If the tool is missing or offline, record that as a Minor finding and continue with manifest analysis.
- Apply the first three sections of `agent-prompts.md`: **Dimension 1: vulnerability analysis (CVE/GHSA triage)**, **Dimension 2: license compliance analysis**, **Dimension 3: staleness & upgrade complexity analysis**.
- Scope to the diff: report on packages added, removed or version-changed in the PR (compare manifests and lockfiles against the base). Advisories on untouched packages go to the pre-existing bucket, not the main findings.

**Extra checks.**
- A manifest change with no matching lockfile change, or the reverse.
- A new dependency that duplicates something already installed or in the standard library.
- Floating ranges (`*`, `latest`, `^0.x`) on a security-relevant package.
- Packages pulled from a git URL, a tarball or a non-default registry.
- A package with a single maintainer, a very recent first release or a name close to a popular one (typosquat).
- A major-version bump with no matching code changes, which suggests breaking changes are unhandled.

**Prompt for the lane agent.**

```
Agent - Dependencies, prefix DEP-, model sonnet:
- prompt: "Audit the dependency changes in this PR. Changed manifests and lockfiles: [MANIFEST_FILES]. Base ref: [BASE]. First compute the added, removed and changed packages by diffing the manifests and lockfiles against the base. Then run the audit commands from the review-deps skill's references/audit-commands.md for each detected ecosystem (read-only, never install or upgrade). Then analyse the three dimensions from its references/agent-prompts.md: vulnerability triage, license compliance and staleness with upgrade complexity. Add the extra checks: [EXTRA_CHECKS].

Severity: Critical for a reachable known-exploited or critical CVE, or a copyleft license that conflicts with the project license; Major for high-severity CVEs and abandoned packages; Minor for staleness and range hygiene. Set preexisting=true for advisories on packages this PR did not touch. Path is the manifest or lockfile; line is the line of the package entry.

Write findings to [SCRATCH]/findings/deps.json as {\"lane\": \"deps\", \"findings\": [...]} using the shared finding shape, ids DEP-001 upward. Add a short summary object under a top-level \"summary\" key: counts of added, removed and updated packages and the audit tool used. Analysis only: do not edit manifests."
```

## Lane: perf-deep

Prefix `PF-`. Findings file `perf-deep.json`. Deduped against core Agent 2 (Performance).

**Triggers.** Changed files match any of:
- database and query code: ORM models, repositories, `**/migrations/**`, raw SQL, GraphQL resolvers, files calling `.query(`, `.execute(`, `.find(`, `.filter(`, `select(`
- loops over collections that call I/O, or nested loops over request-sized input
- bundle and render paths: entry points, route components, `package.json` dependency additions on the client, lazy-loading boundaries, large list or table components
- caching, connection pools, background workers, file or stream handling

If none apply, the core Agent 2 pass is enough and this lane is skipped.

**Composition.** Use the `review-perf` skill's agent prompts and anti-pattern lists (via the `Skill` tool where available, otherwise load `skills/review-perf/references/agent-prompts.md` and apply it inline). Announce it with `Using review-perf to deep-dive the performance paths`. Pick only the sections the diff touches:
- "Agent 1 - N+1 Queries & Database Performance" (N+1 Query Patterns, missing indexes, unbounded queries)
- "Agent 2 - Algorithmic Complexity & Computational Efficiency" (Quadratic and Worse Complexity, Inefficient Data Structure Usage, Unnecessary Work, Recursive Issues)
- "Agent 3 - Frontend Bottlenecks (Bundle Size, Rendering, Network)" (Bundle Size Issues, Rendering Performance, Network Performance, Web Vitals Impact)
- "Agent 4 - Resource Leaks (Memory, Connections, File Handles)" (Memory Leaks, Connection Leaks, Thread/Process Leaks, Resource Pool Exhaustion)

Its rule that `[FILES_LIST]` is the only set of files to read applies here too, and its hunk-range classification (`@@ +c,d` covers lines c to c+d-1) is the same one Scope uses for `preexisting`.

**Dedup with core Agent 2.** Core Agent 2 runs the quick performance pass in the same batch. The merge step collapses duplicates on the same path, overlapping line and title. To keep the lane worth running, this lane goes deeper instead of wider: it follows a query or loop through its callers inside the diff, estimates the cost at realistic input sizes and names the fix with the expected effect. Do not re-report shallow findings the core pass would already catch unless you add the cost estimate.

**Prompt for the lane agent.**

```
Agent - Performance deep-dive, prefix PF-, model sonnet:
- prompt: "Deep-dive the performance of the changes in [FILES_LIST] (only files matching the perf-deep triggers). Use the anti-pattern lists from the review-perf skill's references/agent-prompts.md for the sections the diff touches: N+1 and database, algorithmic complexity, frontend bottlenecks, resource leaks. Project rules to also enforce: [PROJECT_RULES].

For each finding give: the pattern, where the input size comes from, a rough cost at a realistic size (for example '1 query per row, 500 rows per page'), and the fix. No finding without a plausible input size. Severity: Critical for unbounded work on a request path or a leak that grows without limit; Major for N+1, quadratic loops on user-sized input and large bundle regressions; Minor for micro-optimizations. Set preexisting=true when the line is outside every changed hunk.

Write findings to [SCRATCH]/findings/perf-deep.json as {\"lane\": \"perf-deep\", \"findings\": [...]} using the shared finding shape, ids PF-101 upward. Analysis only: profile with read-only commands at most."
```

## Lane: design-motion

Prefix `DM-`. Findings file `design-motion.json`.

**Triggers.** Changed files match any of: `**/*.{css,scss,sass,less,pcss}`, `**/*.{tsx,jsx,vue,svelte,astro,html}`, `tailwind.config.*`, `**/styles/**`, `**/theme/**`, `**/components/**`, animation libraries added to a manifest (`framer-motion`, `motion`, `gsap`, `react-spring`, `lottie`), design tokens files.

**Composition.** Use the `review-design` skill's criteria (via the `Skill` tool where available, otherwise load `skills/review-design/references/criteria-interaction.md` and `skills/review-design/references/criteria-foundations.md` and apply them inline). Announce it with `Using review-design to audit the UI and motion changes`.
- From `criteria-interaction.md`: **Dimension 6: Feedback & States**, **Dimension 7: Motion & Microinteractions** (checks MO-01 to MO-07), **Dimension 5: Components & Affordance (Buttons & Icons)**, and the cross-cutting **Dimension 8: Accessibility (WCAG 2.2 AA)**.
- From `criteria-foundations.md`: **Dimension 1: Visual Hierarchy & Layout** and **Dimension 2: Typography**; add **Dimension 3: Color & Theming** only when color or theme files changed.
- Review the code, not a screenshot. Skip the sibling's browser capture phase unless the app is already running and a quick check is cheap. Cite criterion ids (MO-02, and so on) where they apply.

**Optional external skills.** Detect which of these are installed, then load each one found and apply it to the diff as extra lenses. Check the host's skill list; in a plain checkout, look for `SKILL.md` under the agent's skills directories (`~/.claude/skills`, `.claude/skills`, `~/.agents/skills`, plugin caches).
- `emil-design-eng` (interaction and animation craft)
- `find-animation-opportunities` (where motion would help)
- `impeccable` (UI polish critique)
- `design-taste-frontend` (anti-template visual judgment)
- `ui-ux-pro-max` (UX heuristics)

Rules: availability is detected, never assumed. A missing skill is not an error and gets no warning beyond a line in the lane summary naming which were used and which were absent. The lane must produce full findings from the sibling criteria and the checks below even when none are installed. An optional skill's findings are tagged in the body with its name and merged under prefix `DM-`.

**Concrete checks.** Run each against the changed UI code and report every hit:
1. Layout shift on mount: a banner, toast, alert or error row that mounts inside a vertically centred column or flex container, pushing the rest of the content when it appears. Fix: reserve space, overlay it, or animate height.
2. Transition shorthand clobber: one utility or class setting `transition` (or `transition-property`) overrides another on the same element, for example a focus-ring transition lost to a press or hover transition. Check the final computed list of properties, not each class alone.
3. Keyframes versus transitions: keyframe animations on state-driven UI that users can interrupt (hover, toggles, open and close). Interruptible interactions should use transitions so they reverse smoothly from the current value.
4. Easing and duration tokens: raw `ease`, `linear` or ad-hoc millisecond values where the project defines tokens; durations outside the 200-500ms band (MO-02) for routine UI; `linear` outside spinners (MO-03). Prefer one set of tokens everywhere.
5. `prefers-reduced-motion` (MO-01): every non-essential animation, including JS-driven and library animation, has a reduced-motion path.
6. Enter and exit symmetry: an element that slides or scales in from one side leaves toward the same side, or fades in place; exits are usually shorter than enters. Flag exits that jump or vanish.
7. Disabled inputs: setting `disabled` on an input during submit drops focus and can break password-manager autofill and save prompts. Prefer `readOnly` or `aria-disabled` with a pending state, and restore focus after the request.
8. Spinner speed: a spinner that turns too fast reads as frantic or too slow reads as stalled; a full turn in about 0.8 to 1 second is the usual target. Flag spinners on loads under about 300ms that flash and vanish.
9. Text wrap: headings and short paragraphs without `text-wrap: balance` (or `pretty` for body copy) leaving orphans or one-word last lines.
10. Missing states from Dimension 6: loading, empty, error and disabled states for each new interactive component.

**Rejected animation candidates (required).** The lane output must end with a list named `Rejected animation candidates`: every place where animation was considered and not recommended, each with a one-line reason. Examples: "route change fade: reason, content swaps in under 100ms, motion would add latency"; "table row insert: reason, high-frequency update, motion would be noise". Store it in the findings file under a top-level `"rejected_animation_candidates"` key as an array of `{"path","line","candidate","reason"}`. The report prints it. If nothing was considered and rejected, write an empty array and state that no candidates were found.

**Prompt for the lane agent.**

```
Agent - Design and motion, prefix DM-, model sonnet:
- prompt: "Review the UI, CSS and animation changes in [FILES_LIST] (only files matching the design-motion triggers). Apply the review-design criteria from the sibling skill's references/criteria-interaction.md (Dimensions 5 to 8, with checks MO-01 to MO-07) and references/criteria-foundations.md (Dimensions 1 to 3). Optional design skills detected: [DETECTED_SKILLS]; load each and apply it as an extra lens, and carry on without it if none are present. Project rules to also enforce: [PROJECT_RULES].

Run the ten concrete checks: [DM_CHECKS]. Read the actual styles and components; resolve utility classes to the properties they set before judging conflicts.

Severity: Critical for flashing content (MO-05) or an interaction that is blocked or broken; Major for missing reduced-motion handling, layout shift and lost focus; Minor for easing, duration and polish issues. Set preexisting=true when the line is outside every changed hunk.

End with the required list of rejected animation candidates, each with a reason.

Write findings to [SCRATCH]/findings/design-motion.json as {\"lane\": \"design-motion\", \"findings\": [...], \"rejected_animation_candidates\": [...]} using the shared finding shape, ids DM-001 upward. Analysis only: do not edit code."
```
