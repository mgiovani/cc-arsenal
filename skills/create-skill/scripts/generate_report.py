#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "click",
#   "rich",
# ]
# ///
"""
Generate a Rich terminal report from eval grading results.

Reads grading.json files from evals/results/ and produces:
- Per-eval pass/fail table with scores
- Aggregated metrics (mean score, pass rate, comparison verdicts)
- Summary of which assertions consistently fail
- Optional HTML export

Usage:
    uv run python skills/create-skill/scripts/generate_report.py <skill_path>
    uv run python skills/create-skill/scripts/generate_report.py <skill_path> --html
    uv run python skills/create-skill/scripts/generate_report.py <skill_path> \\
        --previous-workspace <prev_path>

Exit codes:
    0 - report generated
    1 - no grading results found
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

SCORE_GOOD = 4
SCORE_OK = 3
FEEDBACK_TRUNCATE_LEN = 60
PASS_RATE_GOOD = 0.7
PASS_RATE_OK = 0.5
ASSERTION_PASS_THRESHOLD = 0.7


def load_grading_results(skill_path: Path) -> list[dict]:
    """Load all grading.json files from evals/results/."""
    results_dir = skill_path / 'evals' / 'results'
    if not results_dir.exists():
        return []

    results = []
    for eval_dir in sorted(results_dir.iterdir()):
        grading_file = eval_dir / 'grading.json'
        if grading_file.exists():
            try:
                data = json.loads(grading_file.read_text(encoding='utf-8'))
                results.append(data)
            except json.JSONDecodeError as e:
                console.print(
                    f'[yellow]Warning: Could not parse {grading_file}: {e}[/yellow]'
                )

    return results


def compute_metrics(results: list[dict]) -> dict:
    """Compute aggregated metrics from grading results."""
    if not results:
        return {}

    scores = [r.get('score', 0) for r in results]
    comparisons = [r.get('comparison', 'unknown') for r in results]

    with_skill_wins = comparisons.count('output_a_better')
    baseline_wins = comparisons.count('output_b_better')
    equivalent = comparisons.count('equivalent')

    # Compute per-assertion pass rates
    assertion_stats: dict[str, dict] = {}
    for result in results:
        for exp in result.get('expectations', []):
            assertion = exp.get('assertion', 'unknown')
            if assertion not in assertion_stats:
                assertion_stats[assertion] = {'pass': 0, 'total': 0}
            assertion_stats[assertion]['total'] += 1
            if exp.get('output_a_pass'):
                assertion_stats[assertion]['pass'] += 1

    return {
        'total_evals': len(results),
        'mean_score': round(sum(scores) / len(scores), 2) if scores else 0,
        'min_score': min(scores) if scores else 0,
        'max_score': max(scores) if scores else 0,
        'pass_rate': round(with_skill_wins / len(results), 2) if results else 0,
        'with_skill_wins': with_skill_wins,
        'baseline_wins': baseline_wins,
        'equivalent': equivalent,
        'assertion_stats': assertion_stats,
    }


def print_eval_table(results: list[dict]) -> None:
    """Print per-eval results table."""
    table = Table(title='Eval Results', show_header=True, header_style='bold')
    table.add_column('Eval ID', style='cyan', min_width=12)
    table.add_column('Score', justify='center', min_width=7)
    table.add_column('Verdict', justify='center', min_width=20)
    table.add_column('Assertions', justify='center', min_width=12)
    table.add_column('Feedback', min_width=40)

    for result in sorted(results, key=lambda r: r.get('eval_id', '')):
        eval_id = result.get('eval_id', 'unknown')
        score = result.get('score', 0)
        comparison = result.get('comparison', 'unknown')
        raw_feedback = result.get('eval_feedback', '')
        feedback = (
            raw_feedback[:FEEDBACK_TRUNCATE_LEN] + '...'
            if len(raw_feedback) > FEEDBACK_TRUNCATE_LEN
            else raw_feedback
        )

        # Score color
        score_style = (
            'green' if score >= SCORE_GOOD else 'yellow' if score >= SCORE_OK else 'red'
        )
        score_text = Text(f'{score}/5', style=score_style)

        # Verdict display
        verdict_map = {
            'output_a_better': '[green]With-Skill Better[/green]',
            'output_b_better': '[red]Baseline Better[/red]',
            'equivalent': '[yellow]Equivalent[/yellow]',
        }
        verdict = verdict_map.get(comparison, f'[dim]{comparison}[/dim]')

        # Count assertions
        expectations = result.get('expectations', [])
        passed = sum(1 for e in expectations if e.get('output_a_pass'))
        total = len(expectations)
        assertions_text = f'{passed}/{total}'
        if passed == total:
            assertions_text = f'[green]{assertions_text}[/green]'
        elif passed >= total * 0.7:
            assertions_text = f'[yellow]{assertions_text}[/yellow]'
        else:
            assertions_text = f'[red]{assertions_text}[/red]'

        table.add_row(eval_id, score_text, verdict, assertions_text, feedback)

    console.print(table)


def print_metrics_panel(metrics: dict) -> None:
    """Print aggregated metrics in a panel."""
    lines = [
        f'[bold]Total Evals:[/bold] {metrics["total_evals"]}',
        f'[bold]Mean Score:[/bold] {metrics["mean_score"]}/5 '
        f'(range: {metrics["min_score"]}-{metrics["max_score"]})',
        f'[bold]With-Skill Wins:[/bold] {metrics["with_skill_wins"]} '
        f'({metrics["baseline_wins"]} baseline wins, {metrics["equivalent"]} equivalent)',
    ]

    pass_rate = metrics.get('pass_rate', 0)
    rate_color = (
        'green'
        if pass_rate >= PASS_RATE_GOOD
        else 'yellow'
        if pass_rate >= PASS_RATE_OK
        else 'red'
    )
    lines.append(f'[bold]Win Rate:[/bold] [{rate_color}]{pass_rate:.0%}[/{rate_color}]')

    content = '\n'.join(lines)
    console.print(Panel(content, title='Summary Metrics', border_style='blue'))


def print_failing_assertions(metrics: dict) -> None:
    """Print assertions that consistently fail."""
    stats = metrics.get('assertion_stats', {})
    failing = {
        assertion: data
        for assertion, data in stats.items()
        if data['total'] > 0 and data['pass'] / data['total'] < ASSERTION_PASS_THRESHOLD
    }

    if not failing:
        console.print('[green]All assertions pass at >70% rate[/green]')
        return

    table = Table(title='Frequently Failing Assertions', header_style='bold yellow')
    table.add_column('Assertion', min_width=50)
    table.add_column('Pass Rate', justify='center', min_width=12)

    for assertion, data in sorted(
        failing.items(), key=lambda x: x[1]['pass'] / x[1]['total']
    ):
        rate = data['pass'] / data['total']
        rate_text = Text(f'{rate:.0%} ({data["pass"]}/{data["total"]})', style='red')
        table.add_row(assertion[:80], rate_text)

    console.print(table)


def compare_with_previous(current_metrics: dict, prev_path: Path) -> None:
    """Compare current metrics with a previous run."""
    prev_metrics_file = prev_path / 'evals' / 'metrics.json'
    if not prev_metrics_file.exists():
        console.print(
            f'[yellow]No previous metrics found at {prev_metrics_file}[/yellow]'
        )
        return

    prev = json.loads(prev_metrics_file.read_text(encoding='utf-8'))
    curr_score = current_metrics.get('mean_score', 0)
    prev_score = prev.get('mean_score', 0)
    delta = curr_score - prev_score

    delta_color = 'green' if delta > 0 else 'red' if delta < 0 else 'yellow'
    delta_str = f'+{delta:.2f}' if delta > 0 else f'{delta:.2f}'

    console.print(
        Panel(
            f'Previous: {prev_score}/5  →  Current: {curr_score}/5  '
            f'[{delta_color}]({delta_str})[/{delta_color}]',
            title='Comparison with Previous Run',
            border_style=delta_color,
        )
    )


def save_metrics(skill_path: Path, metrics: dict) -> None:
    """Save aggregated metrics to evals/metrics.json."""
    from datetime import UTC, datetime  # noqa: PLC0415

    metrics_with_meta = {
        **metrics,
        'skill': skill_path.name,
        'run_timestamp': datetime.now(UTC).isoformat(),
    }

    metrics_file = skill_path / 'evals' / 'metrics.json'
    metrics_file.write_text(json.dumps(metrics_with_meta, indent=2), encoding='utf-8')
    console.print(f'[dim]Metrics saved to {metrics_file}[/dim]')


def generate_html_report(skill_path: Path, results: list[dict], metrics: dict) -> Path:
    """Generate a simple HTML report."""
    html_path = skill_path / 'evals' / 'report.html'

    rows = []
    for result in sorted(results, key=lambda r: r.get('eval_id', '')):
        eval_id = result.get('eval_id', '')
        score = result.get('score', 0)
        comparison = result.get('comparison', '')
        verdict_map = {
            'output_a_better': 'With-Skill Better',
            'output_b_better': 'Baseline Better',
            'equivalent': 'Equivalent',
        }
        expectations = result.get('expectations', [])
        passed = sum(1 for e in expectations if e.get('output_a_pass'))
        total = len(expectations)

        rows.append(
            f'<tr><td>{eval_id}</td><td>{score}/5</td>'
            f'<td>{verdict_map.get(comparison, comparison)}</td>'
            f'<td>{passed}/{total}</td>'
            f'<td>{result.get("eval_feedback", "")}</td></tr>'
        )

    html = f"""<!DOCTYPE html>
<html><head><title>Eval Report: {skill_path.name}</title>
<style>body{{font-family:sans-serif;max-width:1000px;margin:2em auto;}}
table{{border-collapse:collapse;width:100%;}}
th,td{{border:1px solid #ccc;padding:8px;text-align:left;}}
th{{background:#f5f5f5;}}</style></head>
<body>
<h1>Eval Report: {skill_path.name}</h1>
<h2>Metrics</h2>
<p>Total Evals: {metrics.get('total_evals', 0)} | Mean Score: {metrics.get('mean_score', 0)}/5 | With-Skill Wins: {metrics.get('with_skill_wins', 0)}</p>
<h2>Results</h2>
<table>
<tr><th>ID</th><th>Score</th><th>Verdict</th><th>Assertions</th><th>Feedback</th></tr>
{''.join(rows)}
</table>
</body></html>"""

    html_path.write_text(html, encoding='utf-8')
    return html_path


@click.command()
@click.argument('skill_path', type=click.Path(exists=True, path_type=Path))
@click.option('--html', 'export_html', is_flag=True, help='Export HTML report')
@click.option(
    '--previous-workspace',
    'prev_path',
    type=click.Path(path_type=Path),
    default=None,
    help='Path to previous skill workspace for comparison',
)
def main(skill_path: Path, export_html: bool, prev_path: Path | None) -> None:
    """Generate a report from eval grading results."""
    console.print(f'[bold blue]Eval Report:[/bold blue] {skill_path.name}')
    console.print()

    results = load_grading_results(skill_path)
    if not results:
        console.print('[red]No grading results found.[/red]')
        console.print(f'Run grading first: check evals/results/ in {skill_path}')
        sys.exit(1)

    metrics = compute_metrics(results)
    save_metrics(skill_path, metrics)

    print_metrics_panel(metrics)
    console.print()
    print_eval_table(results)
    console.print()
    print_failing_assertions(metrics)

    if prev_path:
        console.print()
        compare_with_previous(metrics, prev_path)

    if export_html:
        html_path = generate_html_report(skill_path, results, metrics)
        console.print(f'\n[green]HTML report saved:[/green] {html_path}')


if __name__ == '__main__':
    main()
