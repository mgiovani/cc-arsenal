"""CC-STARTUP/CACHE/REBUILD/LONGCTX/MODEL-MIX/SUBAGENT-MODEL/EFFORT/HOOK-INJECT:
every check derived straight from a session's parsed request stream."""

from __future__ import annotations

import itertools
import os
from collections import Counter
from typing import TYPE_CHECKING

from optimize_ai_setup.io import chars_to_tokens, fmt_num, median, percentile
from optimize_ai_setup.model import Finding, make_finding

if TYPE_CHECKING:
    from optimize_ai_setup.claude_code.transcript import SessionData, SessionRequest

STARTUP_MED_TOKENS = 30_000
STARTUP_HIGH_TOKENS = 50_000
LONGCTX_P90_TOKENS = 400_000
REBUILD_MIN_PROMPT_TOKENS = 20_000
TTL_1H_SECONDS = 3600
TTL_5M_SECONDS = 300
REBUILD_HIGH_IDLE_COUNT = 20
REBUILD_WRITE_SHARE = 0.5
REBUILD_READ_SHARE = 0.5
EFFORT_HIGH_SHARE_PCT = 70
MODEL_MAJORITY_SHARE = 0.5
MODEL_SHARE_DISPLAY_MIN_PCT = 0.5
SYNTHETIC_MODEL_NAME = '<synthetic>'
HOOK_SESSIONSTART_TOKEN_LIMIT = 500
HOOK_SESSIONSTART_TOKEN_MED = 2_000
HOOK_USERPROMPT_TOKEN_LIMIT = 125


def check_startup(sessions: list[SessionData]) -> tuple[list[Finding], dict[str, object]]:
    starts = [
        s.requests[0].prompt_tok
        for s in sessions
        if s.requests and not s.requests[0].is_sidechain
    ]
    if not starts:
        return [], {}
    med, p90 = median(starts), percentile(starts, 0.9)

    total_listing = sum(s.skill_listing_chars for s in sessions if s.skill_listing_chars)
    n_listing = sum(1 for s in sessions if s.skill_listing_chars) or 1
    avg_listing_tok = chars_to_tokens(total_listing // n_listing)

    deferred: Counter = Counter()
    mcp_instr: Counter = Counter()
    hook_total = 0
    n_deferred = 0
    n_mcp_instr = 0
    n_hook = 0
    for s in sessions:
        if s.deferred_chars_by_server:
            deferred.update(s.deferred_chars_by_server)
            n_deferred += 1
        if s.mcp_instr_chars_by_server:
            mcp_instr.update(s.mcp_instr_chars_by_server)
            n_mcp_instr += 1
        if s.startup_hook_chars:
            hook_total += s.startup_hook_chars
            n_hook += 1
    # ponytail: per-session average attribution, not a sum across every session
    deferred_tok = chars_to_tokens(sum(deferred.values()) // max(n_deferred, 1))
    mcp_instr_tok = chars_to_tokens(sum(mcp_instr.values()) // max(n_mcp_instr, 1))
    hook_tok = chars_to_tokens(hook_total // max(n_hook, 1))

    findings = []
    if med > STARTUP_MED_TOKENS:
        severity = 'high' if med > STARTUP_HIGH_TOKENS else 'med'
        parts = {
            'skill listing': avg_listing_tok,
            'hooks': hook_tok,
            'mcp tool names': deferred_tok,
            'mcp instructions': mcp_instr_tok,
        }
        measured = sum(parts.values())
        top_name, top_tok = max(parts.items(), key=lambda kv: kv[1])
        top_note = (
            f'; measured parts {fmt_num(measured)}, biggest {top_name} {fmt_num(top_tok)}'
            f'; rest is system prompt, tool schemas, memory'
        )
        findings.append(
            make_finding(
                'CC-STARTUP',
                severity,
                f'startup context {fmt_num(med)} tok median '
                f'(>{fmt_num(STARTUP_MED_TOKENS)}){top_note}',
                'prune MCP/skills listed at start; disable unused ones',
                med,
            )
        )
    metrics = {
        'startup_median_tok': int(med),
        'startup_p90_tok': int(p90),
        'skills_tok': avg_listing_tok,
        'mcp_tool_names_tok': deferred_tok,
        'mcp_instructions_tok': mcp_instr_tok,
        'hooks_tok': hook_tok,
    }
    return findings, metrics


def check_cache(sessions: list[SessionData]) -> tuple[list[Finding], dict[str, object]]:
    reqs = [r for s in sessions for r in s.requests]
    if not reqs:
        return [], {}
    prompt_total = sum(r.prompt_tok for r in reqs) or 1
    write_1h = sum(r.write_1h for r in reqs)
    write_5m = sum(r.write_5m for r in reqs)
    reads = sum(r.read_tok for r in reqs)
    uncached = sum(r.input_tok for r in reqs)

    hit_pct = 100 * reads / prompt_total
    write_pct = 100 * (write_1h + write_5m) / prompt_total

    cost = write_1h * 2.0 + write_5m * 1.25 + reads * 0.1 + uncached * 1.0
    write_cost = write_1h * 2.0 + write_5m * 1.25
    write_cost_share = 100 * write_cost / cost if cost else 0.0

    findings = []
    if write_1h and 'DISABLE_PROMPT_CACHING' in os.environ:
        findings.append(
            make_finding(
                'CC-CACHE',
                'high',
                'DISABLE_PROMPT_CACHING is set while cache writes are still happening',
                'unset DISABLE_PROMPT_CACHING*',
                write_cost,
            )
        )
    metrics = {
        'hit_pct': round(hit_pct, 1),
        'write_pct': round(write_pct, 1),
        'write_cost_share_pct': round(write_cost_share, 1),
    }
    return findings, metrics


def _rebuild_ttl(prev: SessionRequest) -> int:
    return TTL_1H_SECONDS if prev.write_1h > 0 else TTL_5M_SECONDS


def _rebuild_cause(prev: SessionRequest, cur: SessionRequest) -> str:
    if prev.model != cur.model:
        return 'model'
    if prev.effort != cur.effort:
        return 'effort'
    if prev.version != cur.version:
        return 'upgrade'
    if prev.prompt_tok and cur.prompt_tok < 0.6 * prev.prompt_tok:
        return 'compaction'
    if cur.ts - prev.ts > _rebuild_ttl(prev):
        return 'idle>ttl'
    return 'unknown'


def check_rebuilds(
    sessions: list[SessionData],
) -> tuple[list[Finding], dict[str, object]]:
    causes: Counter = Counter()
    total_waste = 0
    count = 0
    for session in sessions:
        main = [r for r in session.requests if not r.is_sidechain]
        for prev, cur in itertools.pairwise(main):
            if cur.prompt_tok <= REBUILD_MIN_PROMPT_TOKENS:
                continue
            if cur.write_tok <= REBUILD_WRITE_SHARE * cur.prompt_tok:
                continue
            if cur.read_tok >= REBUILD_READ_SHARE * prev.prompt_tok:
                continue
            count += 1
            total_waste += cur.write_tok
            causes[_rebuild_cause(prev, cur)] += 1

    if count == 0:
        return [], {}

    idle_count = causes.get('idle>ttl', 0)
    findings = []
    severity = (
        'high'
        if idle_count >= REBUILD_HIGH_IDLE_COUNT
        else 'med'
        if idle_count
        else 'low'
    )
    causes_str = ' · '.join(f'{k} {v}' for k, v in causes.most_common())
    findings.append(
        make_finding(
            'CC-REBUILD',
            severity,
            f'{count} rebuilds, {fmt_num(total_waste)} tok rewritten ({causes_str})',
            '/compact before breaks; pin model+effort at session start',
            total_waste,
        )
    )
    metrics = {'rebuilds': count, 'rewritten_tok': total_waste, 'causes': dict(causes)}
    return findings, metrics


def check_longctx(sessions: list[SessionData]) -> tuple[list[Finding], dict[str, object]]:
    peaks = []
    over_threshold = 0
    all_prompts = 0
    for session in sessions:
        main = [r for r in session.requests if not r.is_sidechain]
        if not main:
            continue
        peaks.append(max(r.prompt_tok for r in main))
        for r in main:
            all_prompts += 1
            if r.prompt_tok >= LONGCTX_P90_TOKENS:
                over_threshold += 1
    if not peaks:
        return [], {}

    p50, p90 = median(peaks), percentile(peaks, 0.9)
    pct_over = 100 * over_threshold / max(all_prompts, 1)
    findings = []
    if p90 > LONGCTX_P90_TOKENS:
        findings.append(
            make_finding(
                'CC-LONGCTX',
                'med',
                f'peak context p90 {fmt_num(p90)} tok, {pct_over:.0f}% of turns >= '
                f'{fmt_num(LONGCTX_P90_TOKENS)}',
                '/clear between tasks; /compact <focus>; lower autoCompactWindow',
                p90,
            )
        )
    metrics = {
        'peak_p50_tok': int(p50),
        'peak_p90_tok': int(p90),
        'pct_turns_over_400k': round(pct_over, 1),
    }
    return findings, metrics


def _display_share(counter: Counter, total: int) -> dict[str, float]:
    # <synthetic> is an internal placeholder, not a real model; below-0.5%
    # entries are noise that just clutters the report.
    return {
        m: pct
        for m, t in counter.most_common()
        if m != SYNTHETIC_MODEL_NAME
        and (pct := round(100 * t / total, 1)) >= MODEL_SHARE_DISPLAY_MIN_PCT
    }


def check_model_mix(
    sessions: list[SessionData],
) -> tuple[list[Finding], dict[str, object]]:
    main_tok: Counter = Counter()
    sub_tok: Counter = Counter()
    for session in sessions:
        for r in session.requests:
            bucket = sub_tok if r.is_sidechain else main_tok
            bucket[r.model or 'unknown'] += r.prompt_tok

    findings = []
    metrics: dict[str, object] = {}
    if main_tok:
        total = sum(main_tok.values()) or 1
        metrics['model_share_pct'] = _display_share(main_tok, total)
        top_model, top_tok = main_tok.most_common(1)[0]
        top_share = round(100 * top_tok / total, 1)
        if 'fable' in top_model.lower() and top_tok / total > MODEL_MAJORITY_SHARE:
            findings.append(
                make_finding(
                    'CC-MODEL-MIX',
                    'low',
                    f'{top_model} is {top_share}% of main-thread tokens (2.5x '
                    f'Opus input cost)',
                    'reserve Fable for results that need it; default to Opus/Sonnet',
                    top_tok,
                )
            )
    if sub_tok:
        total_sub = sum(sub_tok.values()) or 1
        metrics['subagent_model_share_pct'] = _display_share(sub_tok, total_sub)
        top_model, top_tok = sub_tok.most_common(1)[0]
        top_share = round(100 * top_tok / total_sub, 1)
        if 'opus' in top_model.lower() and top_tok / total_sub > MODEL_MAJORITY_SHARE:
            findings.append(
                make_finding(
                    'CC-SUBAGENT-MODEL',
                    'med',
                    f'subagents run {top_model} for {top_share}% of subagent tokens',
                    'set model: on the agent/Agent call or CLAUDE_CODE_SUBAGENT_MODEL',
                    top_tok,
                )
            )
    return findings, metrics


def check_effort(sessions: list[SessionData]) -> tuple[list[Finding], dict[str, object]]:
    efforts: Counter = Counter()
    for session in sessions:
        for r in session.requests:
            if not r.is_sidechain and r.effort:
                efforts[r.effort] += 1
    if not efforts:
        return [], {}
    total = sum(efforts.values())
    share = {e: round(100 * c / total, 1) for e, c in efforts.most_common()}
    findings = []
    # "high" is the default effort on most models (Opus 5.5 defaults to medium),
    # so only xhigh/max represent a deliberate, costly elevation worth flagging.
    elevated_pct = share.get('xhigh', 0) + share.get('max', 0)
    if elevated_pct > EFFORT_HIGH_SHARE_PCT:
        findings.append(
            make_finding(
                'CC-EFFORT',
                'low',
                f'xhigh/max effort on {elevated_pct:.0f}% of main-thread turns',
                'default medium; raise only when it stalls',
                0,
            )
        )
    return findings, {'effort_share_pct': share}


def check_hooks(sessions: list[SessionData]) -> tuple[list[Finding], dict[str, object]]:
    # SessionStart is charged per session (sum of that session's invocations);
    # UserPromptSubmit is charged per prompt (every invocation is one prompt).
    session_start_sums: list[int] = []
    user_prompt_chars: list[int] = []
    for session in sessions:
        session_start_total = 0
        has_session_start = False
        for hook_name, lengths in session.hook_chars.items():
            if hook_name.startswith('SessionStart'):
                session_start_total += sum(lengths)
                has_session_start = True
            elif hook_name.startswith('UserPromptSubmit'):
                user_prompt_chars.extend(lengths)
        if has_session_start:
            session_start_sums.append(session_start_total)

    findings = []
    metrics: dict[str, object] = {}
    if session_start_sums:
        avg_tok = chars_to_tokens(sum(session_start_sums) // len(session_start_sums))
        metrics['session_start_hook_tok'] = avg_tok
        if avg_tok > HOOK_SESSIONSTART_TOKEN_LIMIT:
            severity = 'med' if avg_tok > HOOK_SESSIONSTART_TOKEN_MED else 'low'
            findings.append(
                make_finding(
                    'CC-HOOK-INJECT',
                    severity,
                    f'SessionStart hooks inject {fmt_num(avg_tok)} tok avg per session '
                    f'(>{fmt_num(HOOK_SESSIONSTART_TOKEN_LIMIT)})',
                    'trim hook output; move detail into a skill',
                    avg_tok,
                )
            )
    if user_prompt_chars:
        avg_tok = chars_to_tokens(sum(user_prompt_chars) // len(user_prompt_chars))
        metrics['user_prompt_hook_tok'] = avg_tok
        if avg_tok > HOOK_USERPROMPT_TOKEN_LIMIT:
            findings.append(
                make_finding(
                    'CC-HOOK-INJECT',
                    'low',
                    f'UserPromptSubmit hooks inject {fmt_num(avg_tok)} tok avg per '
                    f'prompt (>{fmt_num(HOOK_USERPROMPT_TOKEN_LIMIT)})',
                    'trim hook output; move detail into a skill',
                    avg_tok,
                )
            )
    return findings, metrics
