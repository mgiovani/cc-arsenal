#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "click",
#   "rich",
# ]
# ///
"""
Eval runner for agent skills.

Runs with-skill and baseline comparisons for all evals defined in evals/evals.json.
Requires the `claude` CLI to be installed and authenticated.

Usage:
    uv run python skills/create-skill/scripts/run_eval.py <skill_path>
    uv run python skills/create-skill/scripts/run_eval.py <skill_path> --eval eval-1
    uv run python skills/create-skill/scripts/run_eval.py <skill_path> \\
        --model claude-haiku-4-5-20251001

Exit codes:
    0 - all evals ran successfully
    1 - one or more evals failed to run
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import click
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table

console = Console()

DEFAULT_MODEL = 'claude-haiku-4-5-20251001'
MAX_WORKERS = 4


def load_evals(skill_path: Path) -> dict:
    """Load eval definitions from evals/evals.json."""
    evals_file = skill_path / 'evals' / 'evals.json'
    if not evals_file.exists():
        msg = f'evals/evals.json not found in {skill_path}'
        raise FileNotFoundError(msg)
    return json.loads(evals_file.read_text(encoding='utf-8'))


def run_claude(
    prompt: str,
    model: str,
) -> tuple[str, float]:
    """Run a claude -p call and return (output, duration_seconds).

    Args:
        prompt: The prompt to send
        model: Claude model to use

    Returns:
        Tuple of (output_text, duration_seconds)
    """
    cmd = ['claude', '-p', prompt, '--model', model, '--output-format', 'text']

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
        )
        duration = time.time() - start

        if result.returncode != 0:
            error_msg = result.stderr.strip() or 'Unknown error'
            return f'ERROR: claude -p failed: {error_msg}', duration

        return result.stdout.strip(), duration

    except subprocess.TimeoutExpired:
        return 'ERROR: claude -p timed out after 300s', time.time() - start
    except FileNotFoundError:
        return (
            'ERROR: claude CLI not found. Install from https://claude.ai/code',
            time.time() - start,
        )


def run_single_eval(
    eval_case: dict,
    _skill_path: Path,
    model: str,
    results_dir: Path,
) -> dict:
    """Run one eval case: with-skill + baseline.

    Returns dict with eval results.
    """
    eval_id = eval_case['id']
    prompt = eval_case['prompt']
    eval_dir = results_dir / eval_id
    eval_dir.mkdir(parents=True, exist_ok=True)

    # Run with-skill (skill active) and baseline (no skill active).
    # skill_path is logged in results for traceability; claude -p determines
    # skill loading from its own environment configuration.
    with_skill_output, with_skill_duration = run_claude(prompt, model)

    # Run baseline (no skill)
    baseline_output, baseline_duration = run_claude(prompt, model)

    # Save outputs
    (eval_dir / 'with_skill.txt').write_text(with_skill_output, encoding='utf-8')
    (eval_dir / 'baseline.txt').write_text(baseline_output, encoding='utf-8')

    timing = {
        'eval_id': eval_id,
        'with_skill_duration_s': round(with_skill_duration, 2),
        'baseline_duration_s': round(baseline_duration, 2),
        'model': model,
    }
    (eval_dir / 'timing.json').write_text(json.dumps(timing, indent=2), encoding='utf-8')

    return {
        'eval_id': eval_id,
        'success': not with_skill_output.startswith('ERROR'),
        'with_skill': with_skill_output,
        'baseline': baseline_output,
        'timing': timing,
    }


def run_all_evals(
    skill_path: Path,
    evals_data: dict,
    model: str,
    only_eval: str | None = None,
) -> list[dict]:
    """Run all evals (or a single one if specified).

    Uses ProcessPoolExecutor for parallel execution.
    Returns list of result dicts.
    """
    results_dir = skill_path / 'evals' / 'results'
    results_dir.mkdir(parents=True, exist_ok=True)

    eval_cases = evals_data.get('evals', [])
    if only_eval:
        eval_cases = [e for e in eval_cases if e['id'] == only_eval]
        if not eval_cases:
            console.print(f'[red]Eval not found: {only_eval}[/red]')
            sys.exit(1)

    results: list[dict] = []

    with Progress(
        SpinnerColumn(),
        TextColumn('[progress.description]{task.description}'),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task('Running evals...', total=len(eval_cases))

        # Each eval runs 2 claude calls, do them with limited parallelism
        with ProcessPoolExecutor(
            max_workers=min(MAX_WORKERS, len(eval_cases))
        ) as executor:
            futures = {
                executor.submit(
                    run_single_eval, eval_case, skill_path, model, results_dir
                ): eval_case['id']
                for eval_case in eval_cases
            }

            for future in as_completed(futures):
                eval_id = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    status = '[green]✓[/green]' if result['success'] else '[red]✗[/red]'
                    progress.update(
                        task,
                        advance=1,
                        description=f'{status} {eval_id}',
                    )
                except Exception as e:  # noqa: BLE001
                    results.append(
                        {'eval_id': eval_id, 'success': False, 'error': str(e)}
                    )
                    progress.update(
                        task, advance=1, description=f'[red]✗ {eval_id}[/red]'
                    )

    return results


def print_summary(results: list[dict]) -> None:
    """Print a summary table of eval run results."""
    table = Table(title='Eval Run Summary', show_header=True)
    table.add_column('Eval ID', style='cyan')
    table.add_column('Status', justify='center')
    table.add_column('With-Skill (s)', justify='right')
    table.add_column('Baseline (s)', justify='right')

    for result in sorted(results, key=lambda r: r['eval_id']):
        status = '[green]OK[/green]' if result.get('success') else '[red]FAIL[/red]'
        timing = result.get('timing', {})
        ws_time = str(timing.get('with_skill_duration_s', '-'))
        bl_time = str(timing.get('baseline_duration_s', '-'))
        table.add_row(result['eval_id'], status, ws_time, bl_time)

    console.print(table)

    success_count = sum(1 for r in results if r.get('success'))
    console.print(
        f'\n[bold]Results:[/bold] {success_count}/{len(results)} evals ran successfully'
    )
    console.print('[dim]Next: run generate_report.py after grading is complete[/dim]')


@click.command()
@click.argument('skill_path', type=click.Path(exists=True, path_type=Path))
@click.option('--eval', 'only_eval', default=None, help='Run only this eval ID')
@click.option('--model', default=DEFAULT_MODEL, help='Claude model to use')
def main(skill_path: Path, only_eval: str | None, model: str) -> None:
    """Run evals for a skill: with-skill vs baseline comparison."""
    console.print(f'[bold blue]Running evals for:[/bold blue] {skill_path.name}')

    try:
        evals_data = load_evals(skill_path)
    except FileNotFoundError as e:
        console.print(f'[red]{e}[/red]')
        sys.exit(1)

    skill_name = evals_data.get('skill', skill_path.name)
    eval_count = len(evals_data.get('evals', []))
    console.print(f'Skill: {skill_name} | Evals: {eval_count} | Model: {model}')
    console.print()

    results = run_all_evals(skill_path, evals_data, model, only_eval)
    print_summary(results)

    failed = [r for r in results if not r.get('success')]
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
