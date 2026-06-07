from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from engine.helpers import alternates, price_length
from engine.types import RuleResult, ScaleMode, Segment

# Simple verifiers: (segs, mode). Links: (sets, children, links, mode).
Checker = Callable[..., "list[RuleResult] | None"]


def check_count_alternation(
    segs: list[Segment],
    mode: ScaleMode,
    *,
    expected: int,
    rule_id: str,
) -> list[RuleResult] | None:
    # Shared R1 for trend/sideway/three: exactly `expected` alternating legs, and
    # every leg except the last non-zero (the last may be 0 — the classifier's
    # ratio bounds reject a degenerate last leg).
    if len(segs) != expected or not alternates(segs):
        return None
    if min(price_length(s, mode) for s in segs[: expected - 1]) == 0:
        return None
    return [RuleResult(rule_id, True)]


def run_checkers(
    checkers: Sequence[Checker],
    *args: Any,
) -> list[RuleResult] | None:
    # None ⇒ abort (silent or passed=False); aggregated rules when all pass.
    rules: list[RuleResult] = []
    for checker in checkers:
        result = checker(*args)
        if result is None:
            return None
        rules.extend(result)
        if any(not r.passed for r in result):
            return None
    return rules
