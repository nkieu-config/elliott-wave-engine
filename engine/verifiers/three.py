from __future__ import annotations

from engine.constants import (
    R2_S2_MAX_RATIO_3W,
    R2_S2_MIN_RATIO_3W,
    R3_S3_MIN_RATIO_3W,
)
from engine.helpers import in_range, price_length
from engine.types import PatternKind, RuleResult, ScaleMode, Segment
from engine.verifiers._runner import Checker, check_count_alternation, run_checkers


def verify_3wave(
    segs: list[Segment],
    mode: ScaleMode,
) -> tuple[PatternKind, list[RuleResult]] | None:
    """Validate segments as a 3-wave pattern; return its kind + rule results, or None."""
    rules = run_checkers(CHECKERS, segs, mode)
    if rules is None:
        return None
    kind, classify_rules = _classify_3w(segs, mode)
    rules.extend(classify_rules)
    return kind, rules


def _check_r1_count_alt(
    segs: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    return check_count_alternation(segs, mode, expected=3, rule_id="3w.r1.count_3_alt")


def _check_r2_s2_in_range(
    segs: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    L1 = price_length(segs[0], mode)
    L2 = price_length(segs[1], mode)
    r = L2 / L1
    return [
        RuleResult(
            "3w.r2.s2_in_range",
            in_range(r, R2_S2_MIN_RATIO_3W, R2_S2_MAX_RATIO_3W),
            measured=r,
            detail=f"[{R2_S2_MIN_RATIO_3W}, {R2_S2_MAX_RATIO_3W}]",
        )
    ]


def _check_r3_s3_min_size(
    segs: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    L2 = price_length(segs[1], mode)
    L3 = price_length(segs[2], mode)
    r = L3 / L2
    return [
        RuleResult(
            "3w.r3.s3_min_size",
            r >= R3_S3_MIN_RATIO_3W,
            measured=r,
            detail=f">={R3_S3_MIN_RATIO_3W}",
        )
    ]


CHECKERS: tuple[Checker, ...] = (
    _check_r1_count_alt,
    _check_r2_s2_in_range,
    _check_r3_s3_min_size,
)


def _classify_3w(
    segs: list[Segment],
    mode: ScaleMode,
) -> tuple[PatternKind, list[RuleResult]]:
    # Subtype = (s2_longer=r21>1, s3_shorter=r32<1); always succeeds, no R4 entry.
    L1 = price_length(segs[0], mode)
    L2 = price_length(segs[1], mode)
    L3 = price_length(segs[2], mode)
    r_s2_s1 = L2 / L1
    r_s3_s2 = L3 / L2
    s2_longer = r_s2_s1 > 1.0
    s3_shorter = r_s3_s2 < 1.0

    if s2_longer and s3_shorter:
        return PatternKind.THREE_S2_LONGER_S3_SHORTER, []
    if s2_longer:
        return PatternKind.THREE_S2_LONGER, []
    if s3_shorter:
        return PatternKind.THREE_S3_SHORTER, []
    return PatternKind.THREE_NORMAL, []
