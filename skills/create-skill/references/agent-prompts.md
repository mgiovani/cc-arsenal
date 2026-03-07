# Agent Prompts

Prompts for grader agents used in the eval system. Load this reference when running Phase 6 eval execution.

## Grader Agent

Used to score eval results with blind comparison. Receives both outputs (labeled A and B, not "with-skill" and "baseline") to prevent bias.

### Prompt Template

```
You are a skill quality evaluator. You will receive two outputs from the same prompt,
labeled Output A and Output B, and a list of assertions about what good output looks like.

Your job:
1. Check each assertion against both outputs
2. Score Output A on a 1-5 scale
3. State which output is better overall (or if they're equivalent)
4. Provide one specific, actionable suggestion for improvement

PROMPT THAT WAS SENT:
{eval_prompt}

ASSERTIONS (what good output should satisfy):
{assertions_formatted}

OUTPUT A:
{output_a}

---

OUTPUT B:
{output_b}

---

Respond with ONLY valid JSON in this exact format:
{
  "expectations": [
    {
      "assertion": "<assertion text>",
      "output_a_pass": <true|false>,
      "output_b_pass": <true|false>,
      "reasoning": "<one sentence explanation>"
    }
  ],
  "summary": "<2-3 sentence explanation of overall quality difference>",
  "score": <1-5 integer for Output A>,
  "comparison": "<output_a_better|output_b_better|equivalent>",
  "eval_feedback": "<one specific, actionable suggestion to improve either the skill or the eval assertions>"
}

Scoring guide for Output A:
1 - Completely wrong or unhelpful
2 - Partially correct but major issues
3 - Acceptable but notable gaps
4 - Good, minor issues only
5 - Excellent, satisfies all assertions

Important: You do not know which output came from a skill and which is baseline.
Grade purely on quality relative to the assertions.
```

### Usage in Phase 6

When spawning the grader as a Task agent:

```
Grader Agent:
- subagent_type: "general-purpose"
- model: "sonnet"
- prompt: [Fill template above with eval_prompt, assertions_formatted, output_a, output_b]
```

Randomly assign which output is A vs B for each grader call. Track the mapping separately so you can interpret the results correctly.

### Interpreting Results

**score field**: Quality of Output A (1-5). If you assigned with-skill as A, this scores the skill output.

**comparison field**: Which is better overall:
- `output_a_better`: A won
- `output_b_better`: B won
- `equivalent`: No meaningful difference

**eval_feedback field**: Actionable suggestion. Can target:
- The skill (improve instructions, add missing steps)
- The description (improve trigger precision)
- The evals (improve assertion specificity)

### Score Interpretation

| Score | Meaning | Action |
|-------|---------|--------|
| 5 | Excellent | Ship it |
| 4 | Good | Minor tweaks optional |
| 3 | Acceptable | Identify the gap, fix, re-eval |
| 2 | Needs work | Major revision needed |
| 1 | Broken | Rethink the approach |

Target: score ≥ 4 AND comparison = `output_a_better` (assuming with-skill = Output A).

## Batch Grader Prompt

For grading multiple evals in one agent call (reduces Task tool invocations):

```
You are a skill quality evaluator. Grade the following {n} eval results.

For each eval, you receive:
- The prompt sent
- Output A and Output B (you don't know which is which)
- Assertions about expected output

Return a JSON array with one grading object per eval.

EVALS TO GRADE:
{evals_formatted}

Each grading object must follow this schema:
{
  "eval_id": "<id>",
  "expectations": [...],
  "summary": "...",
  "score": <1-5>,
  "comparison": "<output_a_better|output_b_better|equivalent>",
  "eval_feedback": "..."
}

Return ONLY the JSON array, no other text.
```

Use the batch prompt when grading 3+ evals to reduce latency and cost.

## Description Improvement Prompt

Used by `improve_description.py` to generate an improved description after seeing failures:

```
Current skill description:
{current_description}

The description was tested against 20 trigger queries (10 that should activate the skill,
10 that should not). Here are the failures:

Failed should-trigger queries (skill didn't activate when it should have):
{failed_should_trigger}

Failed should-not-trigger queries (skill activated when it shouldn't have):
{failed_should_not_trigger}

Write an improved description that:
1. Covers the missed trigger phrasings
2. Avoids false positives for out-of-scope queries
3. Stays under 1024 characters
4. Remains assertive and specific

Return ONLY the new description text, no other content.
```
