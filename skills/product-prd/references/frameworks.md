# Frameworks: opt-in prioritization & metrics pipelines

These are **opt-in**. Activate a stage only when finer granularity is actually
wanted: do not force all of them through every PRD, and never let a framework
inflate a brief. The quality bar is "does this reduce back-and-forth", not
"how many frameworks did we run".

## Prioritization pipeline (per requirement, when disputed)

Run only the stages the decision needs, in this order:

1. **JTBD / Opportunity-Solution-Tree**: frame the need as a job:
   "When {{situation}}, I want {{motivation}}, so I can {{outcome}}." The evidence
   for the job is what was tested (Torres discovery): record it in the evidence block.
2. **Kano category**: classify: **Basic** (expected, dissatisfier if missing) ·
   **Performance** (more is better) · **Delighter** (unexpected upside).
3. **MoSCoW**: release-scope tag: **Must · Should · Could · Won't**.
4. **RICE**: rank *within* a MoSCoW bucket, and only for genuinely disputed edges:
   `(Reach × Impact × Confidence) ÷ Effort`. Don't score the obvious.

Stop at the first stage that resolves the dispute. A requirement everyone agrees
on needs none of these.

## Metrics pipeline (per feature)

1. **North Star alignment**: one line: how this feature moves the product's North
   Star metric. If you can't draw the line, the requirement may not belong.
2. **HEART / Goals-Signals-Metrics**: pick only the applicable HEART categories
   (not all five): **H**appiness · **E**ngagement · **A**doption · **R**etention ·
   **T**ask-success. For each chosen category: a Goal, the Signal that indicates it,
   and the Metric that measures it: each with baseline / target / measurement window.
3. **AARRR funnel tag** (growth only): tag acquisition / activation / retention /
   revenue / referral requirements with their funnel stage. Skip for non-growth work.

## When to reach for these

- A **brief** almost never needs them.
- A **one-pager** may add a Kano tag or a single North-Star line.
- A **big/execution PRD** uses MoSCoW + baseline/target/window metrics by
  default, and RICE only where the team disputes an edge.
