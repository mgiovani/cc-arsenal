# Skill Schemas

JSON schemas for eval system output formats. Use these when creating or validating eval files.

## evals/evals.json

The evaluation definition file. Created during Phase 4 of skill creation.

```json
{
  "$schema": "https://agentskills.io/schemas/evals.json",
  "skill": "skill-name",
  "description": "One-sentence description of what this skill does",
  "evals": [
    {
      "id": "eval-1",
      "prompt": "Exact trigger phrase a user would type",
      "assertions": [
        "Output contains expected content or structure",
        "Files created at expected paths",
        "No placeholder text in output"
      ]
    }
  ]
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `skill` | string | yes | Skill name (matches `name` in SKILL.md frontmatter) |
| `description` | string | yes | What the skill does in one sentence |
| `evals` | array | yes | List of eval test cases |
| `evals[].id` | string | yes | Unique identifier (kebab-case, e.g., "eval-basic-usage") |
| `evals[].prompt` | string | yes | Exact trigger phrase a user would type to activate the skill |
| `evals[].assertions` | array | yes | List of natural-language assertions about expected output |

### Writing Good Evals

**Prompts:**
- Write exactly what a real user would type — not an idealized machine-readable query
- Cover the range of trigger phrasings from the skill description
- Include at least one "easy" case and one case with ambiguity

**Assertions:**
- Be specific but not brittle — check structure and content, not exact wording
- Each assertion should fail for a clearly bad output and pass for a good one
- Avoid assertions that would pass even if the skill produced garbage

**Example evals for a commit message skill:**
```json
{
  "skill": "git-commit",
  "description": "Generates conventional commit messages from staged changes",
  "evals": [
    {
      "id": "basic-feature",
      "prompt": "Create a commit message for my staged changes",
      "assertions": [
        "Commit message follows conventional commits format (type: description)",
        "Type is one of: feat, fix, docs, style, refactor, perf, test, build, ci, chore",
        "Description is under 72 characters",
        "No placeholder text like [description] remains"
      ]
    },
    {
      "id": "breaking-change",
      "prompt": "Write a commit for these API changes that break backwards compatibility",
      "assertions": [
        "Includes BREAKING CHANGE footer or ! in type",
        "Body explains what changed and why"
      ]
    }
  ]
}
```

## evals/results/{eval_id}/grading.json

Output from the grader agent. Created during eval execution.

```json
{
  "eval_id": "eval-1",
  "skill_name": "skill-name",
  "with_skill_output": "...",
  "baseline_output": "...",
  "expectations": [
    {
      "assertion": "Output contains expected content",
      "with_skill_pass": true,
      "baseline_pass": false,
      "reasoning": "The skill output contains X while baseline does not"
    }
  ],
  "summary": "Brief explanation of overall quality difference",
  "score": 4,
  "comparison": "with_skill_better",
  "eval_feedback": "Suggestion for improving the skill or evals"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `eval_id` | string | Which eval this grades |
| `skill_name` | string | Skill being evaluated |
| `with_skill_output` | string | Output produced with skill active |
| `baseline_output` | string | Output produced without skill |
| `expectations` | array | Per-assertion verdicts |
| `expectations[].assertion` | string | The assertion being checked |
| `expectations[].with_skill_pass` | bool | Did with-skill output satisfy it? |
| `expectations[].baseline_pass` | bool | Did baseline satisfy it? |
| `expectations[].reasoning` | string | Explanation of the verdict |
| `summary` | string | Overall quality comparison |
| `score` | integer | 1-5 score for with-skill output quality |
| `comparison` | string | One of: `with_skill_better`, `baseline_better`, `equivalent` |
| `eval_feedback` | string | Actionable suggestion for improvement |

## evals/metrics.json

Aggregated metrics across all eval runs.

```json
{
  "skill": "skill-name",
  "run_timestamp": "2026-03-07T12:00:00Z",
  "total_evals": 3,
  "pass_rate": 0.67,
  "mean_score": 3.8,
  "with_skill_wins": 2,
  "baseline_wins": 0,
  "equivalent": 1,
  "per_eval": [
    {
      "eval_id": "eval-1",
      "score": 4,
      "comparison": "with_skill_better",
      "assertions_passed": 3,
      "assertions_total": 3
    }
  ]
}
```

## evals/benchmark.json

Tracks improvement across iterations.

```json
{
  "skill": "skill-name",
  "iterations": [
    {
      "iteration": 1,
      "description_version": "Original description",
      "train_score": 0.6,
      "test_score": 0.55,
      "timestamp": "2026-03-07T10:00:00Z"
    },
    {
      "iteration": 2,
      "description_version": "Improved description with more trigger phrases",
      "train_score": 0.8,
      "test_score": 0.75,
      "timestamp": "2026-03-07T11:00:00Z"
    }
  ],
  "best_iteration": 2,
  "improvement": 0.2
}
```
