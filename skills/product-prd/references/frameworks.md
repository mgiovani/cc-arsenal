# Frameworks: opt-in prioritization & metrics pipelines

These stages are opt-in. Activate one only when finer granularity is actually
wanted: do not force all of them through every PRD, and never let a framework
inflate a brief. The quality bar is "does this reduce back-and-forth", not
"how many frameworks did we run".

## Prioritization pipeline (per requirement, when disputed)

Run only the stages the decision needs, in this order:

1. `JTBD` / Opportunity-Solution-Tree: frame the need as a job: "When
   {{situation}}, I want {{motivation}}, so I can {{outcome}}." The evidence for
   the job is what was tested (Torres discovery): record it in the evidence block.
2. `Kano` category: classify the requirement using the table below.
3. `MoSCoW`: release-scope tag, one of Must, Should, Could, Won't.
4. `RICE`: rank within a MoSCoW bucket, and only for genuinely disputed edges,
   using `(Reach × Impact × Confidence) ÷ Effort`. Don't score the obvious.

| Kano category | Meaning |
|---|---|
| Basic | expected; a dissatisfier if missing |
| Performance | more is better |
| Delighter | unexpected upside |

Stop at the first stage that resolves the dispute. A requirement everyone agrees
on needs none of these.

## Metrics pipeline (per feature)

1. North Star alignment: one line on how this feature moves the product's North
   Star metric. If you can't draw the line, the requirement may not belong.
2. `HEART` / Goals-Signals-Metrics: pick only the applicable categories, not all
   five (Happiness, Engagement, Adoption, Retention, Task-success). For each
   chosen category, record a Goal, the Signal that indicates it, and the Metric
   that measures it, each with a baseline, target, and measurement window.
3. `AARRR` funnel tag (growth only): tag acquisition, activation, retention,
   revenue, or referral requirements with their funnel stage. Skip for non-growth work.

## When to reach for these

| Tier | Usage |
|---|---|
| brief | almost never needs them |
| one-pager | may add a Kano tag or a single North Star line |
| big/execution PRD | uses MoSCoW plus baseline/target/window metrics by default, and RICE only where the team disputes an edge |
