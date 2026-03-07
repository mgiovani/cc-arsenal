#!/usr/bin/env python3
"""
Optimize a skill description for model-invoked triggering accuracy.

Algorithm:
1. Generate 20 trigger queries (10 should-trigger, 10 should-not-trigger)
2. Split 60/40 into train/test sets (stratified by trigger intent)
3. Test current description against train set via `claude -p`
4. Iterate up to 5 times improving description based on failures
5. Validate best iteration on test set to prevent overfitting
6. Auto-shorten if improved description exceeds 1024 chars

Requires the `claude` CLI to be installed and authenticated.

Usage:
    uv run python skills/create-skill/scripts/improve_description.py <skill_path>
    uv run python skills/create-skill/scripts/improve_description.py <skill_path> \\
        --iterations 3
    uv run python skills/create-skill/scripts/improve_description.py <skill_path> --dry-run

Exit codes:
    0 - improved description saved
    1 - failed or no improvement found
"""

from __future__ import annotations

import json
import random
import re
import subprocess
import sys
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

MAX_DESCRIPTION_LENGTH = 1024
MAX_ITERATIONS = 5
TRAIN_RATIO = 0.6
QUERIES_PER_CLASS = 10
TRAIN_ACCURACY_PERFECT = 1.0
TRAIN_ACCURACY_GOOD = 0.8


def load_skill_description(skill_path: Path) -> tuple[str, str]:
    """Load current description from SKILL.md frontmatter.

    Returns:
        Tuple of (description, full_frontmatter_yaml)
    """
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        msg = f'SKILL.md not found in {skill_path}'
        raise FileNotFoundError(msg)

    content = skill_md.read_text(encoding='utf-8')
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        msg = 'No valid frontmatter found in SKILL.md'
        raise ValueError(msg)

    frontmatter_str = match.group(1)
    frontmatter = yaml.safe_load(frontmatter_str)
    description = frontmatter.get('description', '')
    if not description:
        msg = "No 'description' field in frontmatter"
        raise ValueError(msg)

    return str(description).strip('"\''), frontmatter_str


def save_skill_description(skill_path: Path, new_description: str) -> None:
    """Write updated description back to SKILL.md frontmatter."""
    skill_md = skill_path / 'SKILL.md'
    content = skill_md.read_text(encoding='utf-8')

    # Update description in frontmatter
    # Handle both quoted and unquoted descriptions
    new_content = re.sub(
        r'(^---\n.*?)(description:\s*"[^"]*"|description:\s*\'[^\']*\'|description:\s*[^\n]+)',
        lambda m: m.group(1) + f'description: "{new_description}"',
        content,
        count=1,
        flags=re.DOTALL,
    )

    skill_md.write_text(new_content, encoding='utf-8')


def generate_queries(
    _skill_path: Path,
    description: str,
    model: str = 'claude-haiku-4-5-20251001',
) -> tuple[list[str], list[str]]:
    """Generate should-trigger and should-not-trigger queries via claude -p.

    Returns:
        Tuple of (should_trigger_queries, should_not_trigger_queries)
    """

    prompt = f"""Given this skill description:

"{description}"

Generate exactly {QUERIES_PER_CLASS} queries that should activate this skill (trigger queries)
and exactly {QUERIES_PER_CLASS} queries that should NOT activate it (negative queries).

Requirements for trigger queries:
- Natural phrasings a real user would type
- Vary the wording significantly (don't just repeat the description)
- Cover different ways to express the same intent

Requirements for negative queries:
- Related topic but clearly out of scope for this skill
- Should feel plausible as adjacent requests
- Must not be the skill's core use case

Return ONLY valid JSON in this format:
{{"should_trigger": ["query1", "query2", ...], "should_not_trigger": ["query1", "query2", ...]}}
"""

    result = subprocess.run(
        ['claude', '-p', prompt, '--model', model, '--output-format', 'text'],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        msg = f'Failed to generate queries: {result.stderr}'
        raise RuntimeError(msg)

    output = result.stdout.strip()

    # Extract JSON from output
    json_match = re.search(r'\{.*\}', output, re.DOTALL)
    if not json_match:
        msg = f'Could not extract JSON from claude output: {output[:200]}'
        raise ValueError(msg)

    data = json.loads(json_match.group())
    return data.get('should_trigger', []), data.get('should_not_trigger', [])


def split_train_test(
    should_trigger: list[str],
    should_not_trigger: list[str],
    seed: int = 42,
) -> tuple[list[tuple[str, bool]], list[tuple[str, bool]]]:
    """Split queries into train/test sets with stratification.

    Returns:
        Tuple of (train_set, test_set) where each item is (query, should_trigger)
    """
    rng = random.Random(seed)  # noqa: S311 — not cryptographic, used for train/test split

    # Shuffle each class independently
    trigger_shuffled = should_trigger[:]
    rng.shuffle(trigger_shuffled)
    not_trigger_shuffled = should_not_trigger[:]
    rng.shuffle(not_trigger_shuffled)

    # Split each class at TRAIN_RATIO
    trigger_split = int(len(trigger_shuffled) * TRAIN_RATIO)
    not_trigger_split = int(len(not_trigger_shuffled) * TRAIN_RATIO)

    train = [(q, True) for q in trigger_shuffled[:trigger_split]] + [
        (q, False) for q in not_trigger_shuffled[:not_trigger_split]
    ]
    test = [(q, True) for q in trigger_shuffled[trigger_split:]] + [
        (q, False) for q in not_trigger_shuffled[not_trigger_split:]
    ]

    rng.shuffle(train)
    rng.shuffle(test)

    return train, test


def test_description(
    description: str,
    query_set: list[tuple[str, bool]],
    model: str = 'claude-haiku-4-5-20251001',  # noqa: PT028
) -> tuple[float, list[dict]]:
    """Test a description against a set of queries.

    Sends each query to claude and checks whether the model mentions or activates
    the skill concept (based on description keywords).

    Returns:
        Tuple of (accuracy, per_query_results)
    """
    correct = 0
    per_query: list[dict] = []

    # Extract key concepts from description for detection
    desc_keywords = re.findall(r'\b[a-zA-Z]{4,}\b', description.lower())
    desc_keywords = list(set(desc_keywords[:10]))  # Top 10 unique keywords

    for query, should_trigger in query_set:
        # Use a meta-prompt: ask claude if it would use the described skill
        test_prompt = f"""Given this skill description: "{description}"

Would this skill be appropriate to use for the following user request?
Respond with only YES or NO.

User request: "{query}"
"""
        result = subprocess.run(
            ['claude', '-p', test_prompt, '--model', model, '--output-format', 'text'],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            per_query.append(
                {
                    'query': query,
                    'should_trigger': should_trigger,
                    'actual_trigger': None,
                    'correct': False,
                    'error': result.stderr.strip(),
                }
            )
            continue

        output = result.stdout.strip().upper()
        actual_trigger = 'YES' in output

        is_correct = actual_trigger == should_trigger
        if is_correct:
            correct += 1

        per_query.append(
            {
                'query': query,
                'should_trigger': should_trigger,
                'actual_trigger': actual_trigger,
                'correct': is_correct,
            }
        )

    accuracy = correct / len(query_set) if query_set else 0
    return accuracy, per_query


def improve_description(
    current_description: str,
    failures: list[dict],
    model: str = 'claude-haiku-4-5-20251001',
) -> str:
    """Generate an improved description based on failures."""
    failed_should_trigger = [
        f['query'] for f in failures if f['should_trigger'] and not f.get('correct')
    ]
    failed_should_not_trigger = [
        f['query'] for f in failures if not f['should_trigger'] and not f.get('correct')
    ]

    prompt = f"""Current skill description:
{current_description}

This description was tested against trigger queries. Here are the failures:

Queries that SHOULD trigger the skill but DIDN'T (undertriggering):
{json.dumps(failed_should_trigger, indent=2) if failed_should_trigger else 'None'}

Queries that should NOT trigger the skill but DID (false positives):
{json.dumps(failed_should_not_trigger, indent=2) if failed_should_not_trigger else 'None'}

Write an improved description that:
1. Covers the missed trigger phrasings (fix undertriggering)
2. Is more specific to avoid false positives
3. Stays under {MAX_DESCRIPTION_LENGTH} characters
4. Is assertive and specific (not vague)
5. Covers multiple ways users express the same intent

Return ONLY the new description text. No explanation, no quotes, just the description.
"""

    result = subprocess.run(
        ['claude', '-p', prompt, '--model', model, '--output-format', 'text'],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        msg = f'Failed to generate improved description: {result.stderr}'
        raise RuntimeError(msg)

    new_desc = result.stdout.strip().strip('"\'')

    # Auto-shorten if too long
    if len(new_desc) > MAX_DESCRIPTION_LENGTH:
        new_desc = _shorten_description(new_desc, model)

    return new_desc


def _shorten_description(description: str, model: str) -> str:
    """Auto-shorten a description that exceeds the character limit."""
    prompt = f"""This description is {len(description)} characters but must be under {MAX_DESCRIPTION_LENGTH}.
Shorten it while preserving the key trigger phrases and intent.

Current: {description}

Return ONLY the shortened description. No explanation.
"""
    result = subprocess.run(
        ['claude', '-p', prompt, '--model', model, '--output-format', 'text'],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode == 0:
        shortened = result.stdout.strip().strip('"\'')
        if len(shortened) <= MAX_DESCRIPTION_LENGTH:
            return shortened

    # Fallback: truncate at last sentence boundary
    truncated = description[:MAX_DESCRIPTION_LENGTH]
    last_period = truncated.rfind('.')
    if last_period > MAX_DESCRIPTION_LENGTH * TRAIN_RATIO:
        truncated = truncated[: last_period + 1]
    return truncated


def print_iteration_results(
    iteration: int,
    description: str,
    train_accuracy: float,
    failures: list[dict],
) -> None:
    """Print results for one iteration."""
    failure_count = sum(1 for f in failures if not f.get('correct'))
    console.print(
        f'\n[bold]Iteration {iteration}[/bold] | '
        f'Train accuracy: [{"green" if train_accuracy >= TRAIN_ACCURACY_GOOD else "yellow"}]'
        f'{train_accuracy:.0%}[/{"green" if train_accuracy >= TRAIN_ACCURACY_GOOD else "yellow"}] | '
        f'Failures: {failure_count}'
    )
    console.print(f'[dim]Description ({len(description)} chars):[/dim]')
    console.print(Panel(description, border_style='dim'))


def save_benchmark(skill_path: Path, benchmark_data: dict) -> None:
    """Save benchmark iteration history."""
    from datetime import UTC, datetime  # noqa: PLC0415

    benchmark_file = skill_path / 'evals' / 'benchmark.json'

    existing: list[dict] = []
    if benchmark_file.exists():
        try:
            existing = json.loads(benchmark_file.read_text())
        except (json.JSONDecodeError, ValueError):
            existing = []

    entry = {
        **benchmark_data,
        'timestamp': datetime.now(UTC).isoformat(),
    }
    existing.append(entry)

    benchmark_file.parent.mkdir(parents=True, exist_ok=True)
    benchmark_file.write_text(json.dumps(existing, indent=2), encoding='utf-8')


@click.command()
@click.argument('skill_path', type=click.Path(exists=True, path_type=Path))
@click.option('--iterations', default=MAX_ITERATIONS, help='Max improvement iterations')
@click.option('--model', default='claude-haiku-4-5-20251001', help='Claude model to use')
@click.option('--dry-run', is_flag=True, help='Run without saving changes')
@click.option('--seed', default=42, help='Random seed for train/test split')
def main(
    skill_path: Path,
    iterations: int,
    model: str,
    dry_run: bool,
    seed: int,
) -> None:
    """Optimize a skill description for model-invoked triggering accuracy."""
    console.print(f'[bold blue]Description Optimizer:[/bold blue] {skill_path.name}')

    try:
        current_description, _ = load_skill_description(skill_path)
    except (FileNotFoundError, ValueError) as e:
        console.print(f'[red]{e}[/red]')
        sys.exit(1)

    console.print(f'Current description ({len(current_description)} chars):')
    console.print(Panel(current_description, border_style='dim'))
    console.print()

    # Step 1: Generate queries
    console.print('[bold]Step 1:[/bold] Generating trigger queries...')
    try:
        should_trigger, should_not_trigger = generate_queries(
            skill_path, current_description, model
        )
    except (RuntimeError, ValueError) as e:
        console.print(f'[red]Failed to generate queries: {e}[/red]')
        sys.exit(1)

    console.print(
        f'Generated {len(should_trigger)} trigger queries, '
        f'{len(should_not_trigger)} negative queries'
    )

    # Step 2: Split train/test
    train_set, test_set = split_train_test(should_trigger, should_not_trigger, seed)
    console.print(f'Split: {len(train_set)} train, {len(test_set)} test')
    console.print()

    # Step 3: Iterate and improve
    best_description = current_description
    best_train_score = 0.0
    iteration_history = []

    for i in range(1, iterations + 1):
        console.print(
            f'[bold]Step 2/3 Iteration {i}/{iterations}:[/bold] Testing description...'
        )

        train_accuracy, train_results = test_description(
            current_description, train_set, model
        )

        print_iteration_results(i, current_description, train_accuracy, train_results)

        if train_accuracy > best_train_score:
            best_train_score = train_accuracy
            best_description = current_description

        iteration_history.append(
            {
                'iteration': i,
                'description': current_description,
                'train_accuracy': train_accuracy,
            }
        )

        if train_accuracy >= TRAIN_ACCURACY_PERFECT:
            console.print('[green]Perfect train accuracy — stopping early[/green]')
            break

        # Improve for next iteration
        failures = [r for r in train_results if not r.get('correct')]
        if not failures:
            break

        console.print('Generating improved description...')
        try:
            current_description = improve_description(
                current_description, train_results, model
            )
        except RuntimeError as e:
            console.print(f'[yellow]Warning: Could not improve description: {e}[/yellow]')
            break

    # Step 4: Validate on test set
    console.print('\n[bold]Step 4:[/bold] Validating best description on test set...')
    test_accuracy, test_results = test_description(best_description, test_set, model)

    # Print final results
    table = Table(title='Optimization Results', header_style='bold')
    table.add_column('Metric', style='cyan')
    table.add_column('Value', justify='right')

    table.add_row('Best Train Accuracy', f'{best_train_score:.0%}')
    table.add_row('Test Set Accuracy', f'{test_accuracy:.0%}')
    table.add_row('Description Length', f'{len(best_description)} chars')
    table.add_row('Iterations Run', str(len(iteration_history)))

    console.print(table)
    console.print()
    console.print('[bold]Optimized Description:[/bold]')
    console.print(Panel(best_description, border_style='green'))

    # Save benchmark
    save_benchmark(
        skill_path,
        {
            'best_train_accuracy': best_train_score,
            'test_accuracy': test_accuracy,
            'iterations': len(iteration_history),
            'description_length': len(best_description),
            'description_version': best_description[:100] + '...',
        },
    )

    # Save description if improved
    if not dry_run and best_description != (load_skill_description(skill_path)[0]):
        save_skill_description(skill_path, best_description)
        console.print('[green]Saved improved description to SKILL.md[/green]')
    elif dry_run:
        console.print('[dim]Dry run — no changes saved[/dim]')
    else:
        console.print('[dim]Description unchanged[/dim]')


if __name__ == '__main__':
    main()
