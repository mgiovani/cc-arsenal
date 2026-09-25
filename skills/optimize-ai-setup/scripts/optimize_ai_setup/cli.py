"""Orchestration: wire every harness's detect/collect pair together, sort the
findings, and render either the text or --json report."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from optimize_ai_setup.antigravity import collect_antigravity, detect_antigravity
from optimize_ai_setup.claude_code import collect_claude_code, detect_claude_code
from optimize_ai_setup.claude_desktop import collect_claude_desktop, detect_claude_desktop
from optimize_ai_setup.codex import collect_codex, detect_codex
from optimize_ai_setup.cross_tool import collect_cross_tool
from optimize_ai_setup.cursor import collect_cursor, detect_cursor
from optimize_ai_setup.gemini import collect_gemini, detect_gemini
from optimize_ai_setup.model import SEVERITY_ORDER, Finding
from optimize_ai_setup.report import Report, render_json, render_text

DEFAULT_DAYS = 14

HARNESSES: tuple[tuple[str, object, object], ...] = (
    ('claude-code', detect_claude_code, collect_claude_code),
    ('codex', detect_codex, collect_codex),
    ('cursor', detect_cursor, collect_cursor),
    ('antigravity', detect_antigravity, collect_antigravity),
    ('gemini-cli', detect_gemini, collect_gemini),
    ('claude-desktop', detect_claude_desktop, collect_claude_desktop),
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Collect AI coding setup evidence.')
    parser.add_argument('--days', type=int, default=DEFAULT_DAYS)
    parser.add_argument('--project', type=str, default=str(Path.cwd()))
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--all', action='store_true')
    return parser.parse_args(argv)


def run(home: Path, project: Path, days: int) -> Report:
    detected: list[str] = []
    sampled: list[str] = []
    metrics: dict[str, dict[str, object]] = {}
    findings: list[Finding] = []
    errors: dict[str, str] = {}

    for name, detect, collect in HARNESSES:
        try:
            is_present = detect(home, project)
        except OSError:
            continue
        if not is_present:
            continue
        detected.append(name)
        try:
            harness_findings, harness_metrics, harness_sampled = collect(
                home, project, days
            )
        except Exception as exc:  # noqa: BLE001 -- one bad harness must not crash the whole report
            errors[name] = type(exc).__name__
            continue
        findings.extend(replace(f, harness=name) for f in harness_findings)
        metrics[name] = harness_metrics
        sampled.extend(harness_sampled)

    try:
        cross_findings, cross_sampled = collect_cross_tool(project)
    except Exception as exc:  # noqa: BLE001 -- a bad cross-tool check must not crash the report
        errors['cross-tool'] = type(exc).__name__
    else:
        findings.extend(replace(f, harness='cross-tool') for f in cross_findings)
        sampled.extend(cross_sampled)

    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), -f.impact_tokens))
    return Report(project, days, detected, sampled, metrics, findings, errors)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    home = Path.home()
    project = Path(args.project).resolve()

    report = run(home, project, args.days)

    if args.json:
        render_json(report)
    else:
        render_text(report, show_all=args.all)
    return 0
