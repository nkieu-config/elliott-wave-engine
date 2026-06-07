from __future__ import annotations

from engine.constants import EQUAL_WITHIN_DEFAULT_TOLERANCE, R7_S5_MIN_RATIO_5WT
from engine.helpers import (
    argmax_index,
    equal_within,
    is_pull,
    is_push,
    price_length,
)
from engine.types import PatternKind, RuleResult, ScaleMode, Segment
from engine.verifiers._runner import Checker, check_count_alternation, run_checkers


def verify_5wave_trend(
    segs: list[Segment],
    mode: ScaleMode,
) -> tuple[PatternKind, list[RuleResult]] | None:
    """Validate segments as a 5-wave trend (impulse) pattern; return its kind + rule results, or None."""
    # pp.30-32. R8 may reject if s5_shorter without s3-longest.
    rules = run_checkers(CHECKERS, segs, mode)
    if rules is None:
        return None
    kind, classify_rules = _classify_5w_trend(segs, mode)
    rules.extend(classify_rules)
    if kind is None:
        return None
    return kind, rules


def _check_r1_count_alt(
    segs: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    return check_count_alternation(segs, mode, expected=5, rule_id="5wt.r1.count_5_alt")


def _check_r2_odd_are_push(
    segs: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    del mode
    s1, _s2, s3, _s4, s5 = segs
    trend = s1.direction
    passed = is_push(s1, trend) and is_push(s3, trend) and is_push(s5, trend)
    return [RuleResult("5wt.r2.odd_are_push", passed)]


def _check_r3_even_are_pull(
    segs: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    del mode
    s1, s2, _s3, s4, _s5 = segs
    trend = s1.direction
    passed = is_pull(s2, trend) and is_pull(s4, trend)
    return [RuleResult("5wt.r3.even_are_pull", passed)]


def _check_r4_s3_gt_s2(
    segs: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    L2 = price_length(segs[1], mode)
    L3 = price_length(segs[2], mode)
    return [
        RuleResult(
            "5wt.r4.s3_gt_s2",
            L3 > L2,
            measured=L3 / L2 if L2 else 0.0,
        )
    ]


def _check_r5_s3_not_shortest(
    segs: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    L1 = price_length(segs[0], mode)
    L3 = price_length(segs[2], mode)
    L5 = price_length(segs[4], mode)
    passed = not (L3 < L1 and L3 < L5)
    min_other_push = min(L1, L5)
    return [
        RuleResult(
            "5wt.r5.s3_not_shortest",
            passed,
            measured=L3 / min_other_push if min_other_push > 0 else None,
            detail=">=1.0 means s3 not shortest",
        )
    ]


def _check_r6a_s2_lt_s1(
    segs: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    L1 = price_length(segs[0], mode)
    L2 = price_length(segs[1], mode)
    return [RuleResult("5wt.r6a.s2_lt_s1", L2 < L1, measured=L2 / L1)]


def _check_r6b_s4_lt_s3(
    segs: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    L3 = price_length(segs[2], mode)
    L4 = price_length(segs[3], mode)
    return [RuleResult("5wt.r6b.s4_lt_s3", L4 < L3, measured=L4 / L3)]


def _check_r7_s5_min_size(
    segs: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    L4 = price_length(segs[3], mode)
    L5 = price_length(segs[4], mode)
    r = L5 / L4
    return [RuleResult("5wt.r7.s5_min_size", r >= R7_S5_MIN_RATIO_5WT, measured=r)]


CHECKERS: tuple[Checker, ...] = (
    _check_r1_count_alt,
    _check_r2_odd_are_push,
    _check_r3_even_are_pull,
    _check_r4_s3_gt_s2,
    _check_r5_s3_not_shortest,
    _check_r6a_s2_lt_s1,
    _check_r6b_s4_lt_s3,
    _check_r7_s5_min_size,
)


def _classify_5w_trend(
    segs: list[Segment],
    mode: ScaleMode,
) -> tuple[PatternKind | None, list[RuleResult]]:
    # kind=None ⇒ S5_SHORTER without s3-longest p.32 §4 (rule still records passed=False).
    L1 = price_length(segs[0], mode)
    L3 = price_length(segs[2], mode)
    L4 = price_length(segs[3], mode)
    L5 = price_length(segs[4], mode)
    r_s5_s4 = L5 / L4 if L4 else 0.0
    push_lengths = [L1, L3, L5]
    longest = argmax_index(push_lengths)
    s5_shorter = r_s5_s4 < 1.0

    if s5_shorter:
        if longest != 1:
            return None, [
                RuleResult(
                    "5wt.r8.s5_shorter_requires_s3_longest",
                    False,
                    detail=f"longest={['s1', 's3', 's5'][longest]}",
                )
            ]
        return (
            PatternKind.FIVE_TREND_S5_SHORTER,
            [RuleResult("5wt.r8.s5_shorter_subtype", True)],
        )

    if equal_within(push_lengths, tolerance=EQUAL_WITHIN_DEFAULT_TOLERANCE):
        return (
            PatternKind.FIVE_TREND_EQUAL_PUSH,
            [RuleResult("5wt.r8.equal_push_subtype", True)],
        )

    if longest == 0:
        kind = PatternKind.FIVE_TREND_S1_LONGEST
    elif longest == 1:
        kind = PatternKind.FIVE_TREND_S3_LONGEST
    else:
        kind = PatternKind.FIVE_TREND_S5_LONGEST
    return kind, [RuleResult("5wt.r8.longest_subtype", True, detail=kind.value)]
