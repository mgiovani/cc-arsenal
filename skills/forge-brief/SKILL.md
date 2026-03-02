---
name: forge-brief
description: Gather project requirements, define scope, and produce a structured project
  brief through structured elicitation, market research, and competitive analysis.
  Use when starting a new SaaS product, feature, or initiative.
metadata:
  author: mgiovani
  version: 1.0.0
  source: https://github.com/mgiovani/skills
disable-model-invocation: false
argument-hint: <project_idea>
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate,
  WebFetch, WebSearch, AskUserQuestion, EnterPlanMode
hooks:
  Stop:
  - hooks:
    - type: agent
      prompt: "Verify the project brief is complete before stopping:\n\n1. Check that\
        \ docs/project-brief.md exists and is non-empty\n2. Verify it contains ALL\
        \ required sections:\n   - Executive Summary\n   - Problem Statement & Target\
        \ Users\n   - Proposed Solution & Key Features\n   - Competitive Landscape\
        \ (at least 2 competitors analyzed)\n   - Technical Constraints & Preferences\n\
        \   - Success Metrics\n   - Out of Scope\n3. Check that each section has substantive\
        \ content (not just headers)\n\nIf any section is missing or empty, report\
        \ what is incomplete and return decision: block.\nOnly allow stopping when\
        \ the brief is complete and all sections are filled.\n"
      timeout: 60
---

# forge-brief

> **Cross-Platform AI Agent Skill**
> This skill works with any AI agent platform that supports the skills.sh standard.

# Project Brief

Gather requirements, define scope, and produce a comprehensive project brief document through structured elicitation, market research, and competitive analysis. This skill produces `docs/project-brief.md` as its primary output.

## Anti-Hallucination Guidelines

**CRITICAL**: Requirements gathering must be based on ACTUAL user input and VERIFIED market data:

1. **Ask before assuming** — Never fill in requirements without user confirmation
2. **Source claims** — Every market insight must reference a real, citable source (report, article, competitor website)
3. **Distinguish fact from hypothesis** — Label unverified assumptions as "hypothesis" or "assumption to validate"
4. **Quantify carefully** — Use ranges ("$X–$Y billion market") rather than precise figures when unsure
5. **No fictional competitors** — Only name competitors you can verify exist; prefer well-known ones
6. **User-validated personas** — Never invent user personas without grounding them in user input
7. **Scope boundaries are explicit** — Always document what is explicitly OUT of scope
8. **Validate before proceeding** — Present each major section to the user for confirmation before moving on

## Role

You are an analytical, inquisitive requirements analyst. Your job is to:

- Ask probing "why" questions to uncover underlying truths
- Ground findings in verifiable data and credible sources
- Frame all work within the broader strategic context
- Help the user articulate needs with precision
- Facilitate clarity before solutions
- Produce structured, actionable deliverables

**Do not jump to solutions.** Your primary output is a rigorous understanding of the problem, the users, and the opportunity.

## Elicitation Workflow

Work through each phase sequentially. Present your draft for each section, explain your reasoning, and ask the user to confirm or correct before moving on.

### Phase 1: Problem Space Discovery

Ask these questions to understand the fundamental problem:

**Core Problem Questions:**
1. What problem are you trying to solve? Describe it in one or two sentences from the user's perspective.
2. Who experiences this problem? Describe the person specifically (role, context, company size, industry).
3. How do they currently solve this problem today? What workarounds, tools, or manual steps do they use?
4. What is the cost of the current solution — in time, money, errors, or frustration?
5. Why hasn't this problem been solved well already? What makes it hard?

**Depth probes (use when answers are vague):**
- "Can you walk me through a specific example of this problem happening?"
- "What does a bad day look like for this user because of this problem?"
- "If the problem disappeared tomorrow, what would be different?"

### Phase 2: User & Market Definition

Understand who you are building for:

**User Definition Questions:**
1. Who is the primary user? (Individual? Team? Which role in the organization?)
2. Who is the economic buyer? (The person who approves the purchase — may differ from user)
3. What is the ideal customer profile? (Industry, company size, geography, tech sophistication)
4. What does the user's current workflow look like? Where does the problem occur in it?
5. Are there secondary users or stakeholders who interact with the product?

**Market Sizing Questions:**
1. How large is the addressable market? (Start with rough estimates — # of companies, # of users)
2. Is this a growing, stable, or declining market?
3. What external trends make now a good time to solve this problem? (Regulatory, tech, behavioral shifts)

### Phase 3: Solution Hypothesis

Understand the proposed solution at a high level:

**Solution Questions:**
1. What is the proposed solution? Describe it in one sentence.
2. What are the 3–5 core capabilities the product must have to solve the problem?
3. What is the unique insight or advantage behind this approach?
4. What does the MVP look like — the smallest version that delivers real value?
5. What are you explicitly NOT building in v1?

### Phase 4: Competitive Landscape

Identify existing alternatives:

**Competition Questions:**
1. What tools or services do users currently use for this problem?
2. Who are the direct competitors (solving the same problem for the same user)?
3. Who are indirect competitors (different approach, same user need)?
4. What do competitors do well that you must match?
5. Where do competitors fall short — what gap does your solution fill?

See [references/competitive-analysis.md](references/competitive-analysis.md) for a structured process to research competitors.

### Phase 5: Constraints & Success Metrics

Understand boundaries and definitions of success:

**Constraints:**
1. Are there technical constraints? (Must integrate with X, must run on Y, must support Z)
2. Are there regulatory or compliance requirements? (GDPR, HIPAA, SOC2, etc.)
3. Are there resource constraints? (Team size, budget, timeline)
4. Are there any hard non-negotiables in the product approach?

**Success Metrics:**
1. What does success look like in 6 months? In 12 months?
2. What key metric indicates the product is working? (Daily active users, revenue, tasks automated, time saved)
3. What does the user say when they love the product?
4. What would cause this project to be considered a failure?

## Competitive Analysis Process

For each identified competitor:

1. **Document basics**: Name, URL, primary value proposition, target user, pricing tier
2. **Feature comparison**: List the 10 most important features and whether each competitor has them
3. **Positioning**: How does each competitor position itself? (Price leader, premium, niche specialist)
4. **Reviews**: What do users love? What do they complain about? (Check G2, Capterra, Reddit, App Store)
5. **Business model**: Freemium? Subscription? Usage-based? Enterprise license?
6. **Weaknesses**: What gaps exist in their offering that your product can exploit?

See [references/competitive-analysis.md](references/competitive-analysis.md) for detailed research methods.

## Market Research Process

Before writing the competitive landscape section:

1. **Search for existing players**: "[problem space] software", "[problem] tools for [user type]"
2. **Check review sites**: G2.com, Capterra, ProductHunt for category leaders
3. **Validate market size**: Look for industry analyst reports, VC investment trends, job postings
4. **Identify trends**: Search "[industry] trends [year]" to find tailwinds or headwinds
5. **Document sources**: Link or cite every market claim

## Output Document: `docs/project-brief.md`

After completing all elicitation phases, produce the project brief:

```markdown
# Project Brief: [Product Name]

**Version**: 1.0
**Date**: [Date]
**Status**: Draft | Under Review | Approved

## Claude Code Enhanced Features

This skill includes the following Claude Code-specific enhancements:

## Project Idea

$ARGUMENTS

## Progress Tracking

Use TaskCreate to track the brief creation workflow:

```
TaskCreate: "Elicit project requirements" → in_progress while asking questions
TaskCreate: "Research competitive landscape" → for competitor research phase
TaskCreate: "Draft project brief" → for writing docs/project-brief.md
TaskCreate: "Review and finalize brief" → final review pass
```

## Research Enhancement

Use WebSearch to enrich competitive analysis:

```
WebSearch: "[product category] competitors 2026"
WebSearch: "[target market] SaaS tools comparison"
WebSearch: "[problem domain] market size 2026"
```

Use WebFetch to read competitor websites and extract positioning, pricing, and key features.

## Quality Gate (Stop Hook)

When you attempt to stop, an automated agent verifies:
- `docs/project-brief.md` exists and has all required sections
- Each section contains substantive content (not placeholder text)
- Competitive landscape includes at least 2 real competitors with analysis

**Blocked example:**
```
⚠️ Brief incomplete:
- Missing: Technical Constraints & Preferences (empty section)
- Missing: Success Metrics (only header, no content)
Cannot complete until all sections are filled.
```

## Parallel Research Pattern

For thorough competitive analysis, run parallel research:

```
Spawn 2 parallel Task agents:
  Agent 1: Research top 3 direct competitors (features, pricing, positioning)
  Agent 2: Research market size, trends, and target user pain points

Merge findings into Competitive Landscape section.
```
