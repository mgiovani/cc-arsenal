# Eval system

How the create-skill eval system works, when to use it, and platform-specific notes.

## Overview

The eval system measures skill quality by comparing outputs with and without the skill active. This is more rigorous than manual inspection because:

1. **Objective measurement**: Grader agents score consistently across iterations
2. **Blind comparison**: Grader sees outputs without knowing which is which (prevents bias)
3. **Train/test split**: Description optimizer prevents overfitting to test cases
4. **Iteration tracking**: `evals/benchmark.json` tracks improvement over time

## When to use evals

**High value**: model-invoked skills that auto-trigger based on description:
- If the description is wrong, the skill fires when it shouldn't (false positives)
- If the description is too narrow, it misses when it should fire (false negatives)
- Evals catch both problems before users do

**Medium value**: user-invoked skills with complex outputs:
- When you need to verify that the skill produces meaningfully better output than no skill
- When multiple people will use the skill and quality consistency matters

**Low value**: simple utility skills:
- Skills that just run a command or format data
- When success/failure is obvious without measurement

## How eval execution works

### Step 1: load eval cases

Read `evals/evals.json` from the skill directory. Each eval has:
- `id`: unique identifier
- `prompt`: exact user message to send
- `assertions`: natural-language checks on expected output

### Step 2: run with-Skill and baseline

For each eval, run two parallel sessions via `claude -p`:

**With-skill run**: The skill is loaded and active. The eval prompt is sent.

**Baseline run**: No skill loaded. The same eval prompt is sent.

The `run_eval.py` script handles this via `subprocess` + `claude -p --model haiku`:
```
claude -p "[PROMPT]" --model claude-haiku-4-5-20251001
```

Results are saved to `evals/results/{eval_id}/`:
- `with_skill.txt`: output when skill is active
- `baseline.txt`: output without skill
- `timing.json`: duration and approximate token counts

### Step 3: grade with blind comparison

The grader agent receives both outputs without knowing which is which. It:
1. Checks each assertion against both outputs
2. Scores the with-skill output (1-5)
3. States which output is better (or equivalent)
4. Provides actionable feedback for improvement

See `references/agent-prompts.md` for the exact grader prompt.

Results saved to `evals/results/{eval_id}/grading.json`.

### Step 4: generate report

`generate_report.py` reads all grading results and produces:
- Per-eval pass/fail table
- Aggregated metrics (mean score, pass rate, comparison verdicts)
- Summary of which assertions consistently fail

Use `--html` for a simple HTML export.

## Description optimization

The `improve_description.py` script optimizes the skill description for model-invoked skills.

### How it works

1. **Generate 20 queries**: 10 that should trigger the skill, 10 that should not
   - Should-trigger: natural phrasings of the skill's use case
   - Should-not: related but out-of-scope requests

2. **Split 60/40**: 12 training cases, 8 test cases (stratified: equal trigger/no-trigger ratio in each split)

3. **Test current description**: Send each training case as a message to `claude -p` and check whether the skill fires

4. **Iterate up to 5 times**: If any training cases misfire, improve the description and retest

5. **Validate on test set**: Use the test split to check for overfitting
   - A description that scores 100% on training but 50% on test has overfit

6. **Auto-shorten**: If the improved description exceeds 1024 chars, trim and re-validate

### What makes a good description

Based on Anthropic's skill creator patterns:

- **Assertive**: "Use this whenever..." beats "May be used when..."
- **Covers multiple phrasings**: List synonymous trigger phrases ("create a skill", "make a command", "turn this into a reusable workflow")
- **Specific**: Include domain terms users actually say
- **Not too narrow**: Overly specific descriptions cause undertriggering
- **Not too broad**: Overly broad descriptions cause false positives on unrelated queries

## Platform-Specific notes

**Requirements**:
- `claude` CLI must be installed and authenticated (`claude --version`)
- Python 3.12+ with `rich` and `click` (`uv sync --extra dev` in cc-arsenal)
- The eval scripts use `claude -p` (print mode) for non-interactive runs

**Model selection**:
- `run_eval.py` uses `claude-haiku-4-5-20251001` by default (fast, cheap)
- Grading uses sonnet (better reasoning for nuanced comparisons)
- Override with `--model` flag

**Cost**:
- Each eval run = 2 claude calls (with-skill + baseline) + 1 grader call
- A 3-eval suite = ~9 claude calls total
- Description optimization = ~20 calls per iteration × up to 5 iterations = ~100 calls

## File structure after running evals

```
skill-name/
├── SKILL.md
├── evals/
│   ├── evals.json          ← eval definitions (created during skill creation)
│   ├── metrics.json        ← aggregated metrics (created by generate_report.py)
│   ├── benchmark.json      ← iteration history (created by improve_description.py)
│   └── results/
│       ├── eval-1/
│       │   ├── with_skill.txt
│       │   ├── baseline.txt
│       │   ├── timing.json
│       │   └── grading.json
│       └── eval-2/
│           └── ...
```
