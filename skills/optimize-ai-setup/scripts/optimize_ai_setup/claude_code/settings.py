"""CC-STALE-ENV, CC-TOOLSEARCH-OFF, CC-OBSERVABILITY: settings.json/env checks
that need no session log, only the allowlisted keys they name explicitly."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from optimize_ai_setup.io import get_dict, read_json
from optimize_ai_setup.model import Finding, make_finding

if TYPE_CHECKING:
    from pathlib import Path

MCP_OUTPUT_TOKEN_LIMIT = 25_000

ENV_EXACT_KEYS = (
    'ENABLE_TOOL_SEARCH',
    'MAX_THINKING_TOKENS',
    'MAX_MCP_OUTPUT_TOKENS',
    'ANTHROPIC_BASE_URL',
    'CLAUDE_CODE_SUBAGENT_MODEL',
    'CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS',
    'FORCE_PROMPT_CACHING_5M',
    'ENABLE_PROMPT_CACHING_1H',
)
ENV_PREFIX_KEYS = ('DISABLE_PROMPT_CACHING',)


def collect_allowlisted_env(settings: dict) -> dict[str, str]:
    settings_env = get_dict(settings, 'env')
    found: dict[str, str] = {}
    for source in (settings_env, os.environ):
        for key in ENV_EXACT_KEYS:
            if key in source:
                found.setdefault(key, str(source[key]))
        for prefix in ENV_PREFIX_KEYS:
            for actual_key in source:
                if actual_key.startswith(prefix):
                    found.setdefault(actual_key, str(source[actual_key]))
    return found


def check_env_and_settings(home: Path) -> tuple[list[Finding], dict[str, object]]:
    settings = read_json(home / '.claude' / 'settings.json')
    settings.update(read_json(home / '.claude' / 'settings.local.json'))
    env = collect_allowlisted_env(settings)

    findings = []
    if any(k.startswith('DISABLE_PROMPT_CACHING') for k in env):
        findings.append(
            make_finding(
                'CC-STALE-ENV',
                'high',
                'DISABLE_PROMPT_CACHING* is set: every request re-writes the cache',
                'unset DISABLE_PROMPT_CACHING*',
                0,
            )
        )
    max_mcp_output = env.get('MAX_MCP_OUTPUT_TOKENS')
    if (
        max_mcp_output
        and max_mcp_output.isdigit()
        and int(max_mcp_output) > MCP_OUTPUT_TOKEN_LIMIT
    ):
        findings.append(
            make_finding(
                'CC-STALE-ENV',
                'med',
                f'MAX_MCP_OUTPUT_TOKENS={max_mcp_output} (>25K default cap)',
                'lower MAX_MCP_OUTPUT_TOKENS toward 25000',
                0,
            )
        )

    base_url = env.get('ANTHROPIC_BASE_URL', '')
    is_first_party = base_url == '' or 'anthropic.com' in base_url
    tool_search_off = env.get('ENABLE_TOOL_SEARCH') == 'false'
    betas_disabled = 'CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS' in env
    if (
        tool_search_off
        or betas_disabled
        or (not is_first_party and 'ENABLE_TOOL_SEARCH' not in env)
    ):
        findings.append(
            make_finding(
                'CC-TOOLSEARCH-OFF',
                'med',
                'tool search appears off: every MCP tool schema loads at startup',
                'unset the env forcing it off, or set ENABLE_TOOL_SEARCH=true',
                0,
            )
        )

    if not settings.get('statusLine'):
        findings.append(
            make_finding(
                'CC-OBSERVABILITY',
                'info',
                'no statusLine configured',
                'set statusLine; check /usage and /context each session',
                0,
            )
        )
    return findings, {}
