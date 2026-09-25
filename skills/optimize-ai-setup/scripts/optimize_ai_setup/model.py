"""The Finding shape every check returns, and the severity it sorts by."""

from __future__ import annotations

from dataclasses import dataclass, field

SEVERITY_ORDER = {'high': 0, 'med': 1, 'low': 2, 'info': 3}


@dataclass(frozen=True)
class Finding:
    id: str
    severity: str
    evidence: str
    fix: str
    impact_tokens: int
    harness: str = ''
    names: list[str] = field(default_factory=list)


def make_finding(  # noqa: PLR0913 -- names is an optional 6th arg on an established 5-arg helper
    check_id: str,
    severity: str,
    evidence: str,
    fix: str,
    impact_tokens: float,
    names: list[str] | None = None,
) -> Finding:
    # harness is filled in by run() once a collector's findings come back,
    # since every finding from one collector shares the same harness.
    # names holds the finding's concrete items, for a render step to cite.
    return Finding(
        id=check_id,
        severity=severity,
        evidence=evidence[:160],
        fix=fix[:80],
        impact_tokens=int(impact_tokens),
        names=list(names) if names else [],
    )
