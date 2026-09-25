"""Rendering: the Report shape run() builds, and its text/JSON presentations."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from optimize_ai_setup.io import fmt_num, get_dict

if TYPE_CHECKING:
    from pathlib import Path

    from optimize_ai_setup.model import Finding

TOP_FINDINGS_DEFAULT = 15


def render_metrics_block(harness: str, metrics: dict[str, object]) -> list[str]:
    lines = [f'[{harness}]']
    if not metrics or not any(metrics.values()):
        lines.append('  nothing to report')
        return lines

    if harness == 'claude-code':
        if 'startup_median_tok' in metrics:
            lines.append(
                f'startup    median {fmt_num(metrics["startup_median_tok"])} tok · '
                f'p90 {fmt_num(metrics["startup_p90_tok"])} tok | '
                f'skills {fmt_num(metrics.get("skills_tok", 0))} · '
                f'mcp tool names {fmt_num(metrics.get("mcp_tool_names_tok", 0))} · '
                f'mcp instructions {fmt_num(metrics.get("mcp_instructions_tok", 0))} · '
                f'hooks {fmt_num(metrics.get("hooks_tok", 0))}'
            )
        if 'hit_pct' in metrics:
            lines.append(
                f'cache      hit {metrics["hit_pct"]}% of prompt tok · '
                f'writes {metrics["write_pct"]}% '
                f'(≈{metrics.get("write_cost_share_pct", 0)}% of cost)'
            )
        if 'rebuilds' in metrics:
            causes = get_dict(metrics, 'causes')
            causes_str = ' · '.join(f'{k} {v}' for k, v in causes.items())
            lines.append(
                f'rebuilds   {metrics["rebuilds"]} · {fmt_num(metrics["rewritten_tok"])} '
                f'tok | {causes_str}'
            )
        if 'peak_p90_tok' in metrics:
            lines.append(
                f'context    peak p50 {fmt_num(metrics["peak_p50_tok"])} · '
                f'p90 {fmt_num(metrics["peak_p90_tok"])} · '
                f'{metrics.get("pct_turns_over_400k", 0)}% of turns >=400K'
            )
        if metrics.get('model_share_pct'):
            share = ' · '.join(f'{m} {p}%' for m, p in metrics['model_share_pct'].items())
            lines.append(f'{"models":<11}{share}')
        if metrics.get('subagent_model_share_pct'):
            share = ' · '.join(
                f'{m} {p}%' for m, p in metrics['subagent_model_share_pct'].items()
            )
            lines.append(f'{"subagents":<11}{share}')
        if 'always_loaded_tok' in metrics:
            lines.append(
                f'{"memory":<11}always-loaded '
                f'{fmt_num(metrics["always_loaded_tok"])} tok across '
                f'{metrics.get("files", 0)} files'
            )
        if metrics.get('mcp_json_note'):
            lines.append(f'{"note":<11}{metrics["mcp_json_note"]}')
    elif harness == 'codex':
        if 'sessions' in metrics:
            lines.append(f'{"sessions":<11}{metrics.get("sessions", 0)}')
        if 'cache_hit_pct' in metrics:
            lines.append(f'{"cache":<11}{metrics["cache_hit_pct"]}%')
        if 'longctx_p90_fill_pct' in metrics:
            lines.append(f'{"context":<11}p90 fill {metrics["longctx_p90_fill_pct"]}%')
        if 'agents_md_bytes' in metrics:
            lines.append(
                f'{"agents.md":<11}'
                f'{metrics["agents_md_bytes"]}B/{metrics["agents_md_cap_bytes"]}B cap'
            )
        if 'mcp_servers' in metrics:
            lines.append(f'{"mcp":<11}{metrics["mcp_servers"]} servers')
        if metrics.get('config_note'):
            lines.append(f'{"config":<11}{metrics["config_note"]}')
    else:
        for key, value in metrics.items():
            if value:
                lines.append(f'{key:<10} {value}')
    return lines


@dataclass(frozen=True)
class Report:
    project: Path
    days: int
    detected: list[str]
    sampled: list[str]
    metrics: dict[str, dict[str, object]]
    findings: list[Finding]
    errors: dict[str, str]


def render_text(report: Report, *, show_all: bool) -> None:
    lines: list[str] = [
        f'optimize-ai-setup evidence · window {report.days}d · project '
        f'{report.project.name}'
    ]

    detected_parts = []
    for name in report.detected:
        sessions = report.metrics.get(name, {}).get('sessions')
        detected_parts.append(
            f'{name} ({sessions} sessions)' if isinstance(sessions, int) else name
        )
    lines.append(
        'detected: ' + ' · '.join(detected_parts)
        if detected_parts
        else 'no harness detected'
    )

    if report.sampled:
        lines.append('sampled: ' + ' · '.join(report.sampled))

    for name in report.detected:
        lines.append('')
        if name in report.errors:
            lines.append(f'[{name}]')
            lines.append(f'  error: {report.errors[name]}')
            continue
        lines.extend(render_metrics_block(name, report.metrics.get(name, {})))

    lines.append('')
    findings = report.findings
    shown = findings if show_all else findings[:TOP_FINDINGS_DEFAULT]
    suffix = '' if show_all else f' (top {len(shown)} of {len(findings)}, --all for rest)'
    lines.append(f'findings{suffix}')
    for f in shown:
        lines.append(f'{f.severity.upper():<4} {f.id:<18} {f.evidence:<70} -> {f.fix}')

    print('\n'.join(lines))  # noqa: T201 -- this script's entire job is printing the report


def render_json(report: Report) -> None:
    payload = {
        'window_days': report.days,
        'project': report.project.name,
        'detected': report.detected,
        'sampled': report.sampled,
        'metrics': report.metrics,
        'findings': [asdict(f) for f in report.findings],
    }
    print(json.dumps(payload))  # noqa: T201 -- --json is the script's machine-readable mode
