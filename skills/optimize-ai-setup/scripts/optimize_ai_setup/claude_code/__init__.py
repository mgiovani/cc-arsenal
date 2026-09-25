"""Claude Code: detection plus the orchestration that runs every claude-code
check and folds CC-PROMPT-CRUFT in (it spans memory files and skill text)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from optimize_ai_setup.claude_code.memory import check_memory
from optimize_ai_setup.claude_code.settings import check_env_and_settings
from optimize_ai_setup.claude_code.skills_mcp import (
    check_mcp_unused,
    check_plugins,
    check_skill_descriptions,
    check_skill_dup_and_unused,
)
from optimize_ai_setup.claude_code.transcript import load_all_sessions
from optimize_ai_setup.claude_code.usage_checks import (
    check_cache,
    check_effort,
    check_hooks,
    check_longctx,
    check_model_mix,
    check_rebuilds,
    check_startup,
)
from optimize_ai_setup.model import Finding, make_finding

if TYPE_CHECKING:
    from pathlib import Path

CRUFT_HITS_PER_1K_CHARS = 2.0

CRUFT_PHRASE_RE = re.compile(
    r'double-check|verify twice|be maximally thorough|CRITICAL: YOU MUST|think step by '
    r'step',
    re.IGNORECASE,
)
CAPS_WORD_RE = re.compile(r'\b(?:MUST|NEVER|ALWAYS|IMPORTANT|CRITICAL)\b')


def prompt_cruft_hits(texts: list[str]) -> tuple[int, int]:
    phrase_hits = sum(len(CRUFT_PHRASE_RE.findall(t)) for t in texts)
    caps_hits = sum(len(CAPS_WORD_RE.findall(t)) for t in texts)
    return phrase_hits, caps_hits


def detect_claude_code(home: Path, _project: Path) -> bool:
    return (
        (home / '.claude' / 'projects').is_dir()
        or (home / '.claude.json').exists()
        or (home / '.claude' / 'settings.json').exists()
    )


def collect_claude_code(
    home: Path, project: Path, days: int
) -> tuple[list[Finding], dict[str, object], list[str]]:
    sessions, sampled = load_all_sessions(home / '.claude', days)

    findings: list[Finding] = []
    metrics: dict[str, object] = {'sessions': len(sessions)}

    for check in (
        check_startup,
        check_cache,
        check_rebuilds,
        check_longctx,
        check_model_mix,
        check_effort,
        check_hooks,
    ):
        f, m = check(sessions)
        findings.extend(f)
        metrics.update(m)

    f, m = check_skill_dup_and_unused(sessions)
    findings.extend(f)
    metrics.update(m)

    f, m = check_plugins(home, sessions)
    findings.extend(f)
    metrics.update(m)

    f, m = check_mcp_unused(home, project, sessions)
    findings.extend(f)
    metrics.update(m)

    f, m = check_env_and_settings(home)
    findings.extend(f)
    metrics.update(m)

    mem_findings, mem_metrics, memory_texts = check_memory(home, project)
    findings.extend(mem_findings)
    metrics.update(mem_metrics)

    desc_findings, skill_texts = check_skill_descriptions(home, project)
    findings.extend(desc_findings)

    phrase_hits, caps_hits = prompt_cruft_hits(memory_texts + skill_texts)
    corpus_chars = sum(len(t) for t in memory_texts + skill_texts) or 1
    density = (phrase_hits + caps_hits) / (corpus_chars / 1000)
    if phrase_hits or density > CRUFT_HITS_PER_1K_CHARS:
        findings.append(
            make_finding(
                'CC-PROMPT-CRUFT',
                'low',
                f'{phrase_hits} outdated prompt patterns, {caps_hits} '
                f'MUST/NEVER/ALWAYS/CRITICAL hits '
                'in memory + skills',
                'run /claude-api prompt-audit',
                0,
            )
        )

    return findings, metrics, sampled
