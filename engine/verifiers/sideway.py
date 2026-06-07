from __future__ import annotations

from engine.constants import (
    R2_S2_MAX_RATIO_5WS,
    R2_S2_MIN_RATIO_5WS,
    R3_S4_MAX_RATIO_5WS,
    R3_S4_MIN_RATIO_5WS,
    R4_S3_MAX_CONTRACT_5WS,
    R4_S3_MIN_CONTRACT_5WS,
    R5_S5_MAX_CONTRACT_5WS,
    R5_S5_MIN_CONTRACT_5WS,
    SIDEWAY_EXPAND_BOUNDARY,
)
from engine.helpers import in_range, price_length
from engine.types import PatternKind, RuleResult, ScaleMode, Segment
from engine.verifiers._runner import Checker, check_count_alternation, run_checkers


def verify_5wave_sideway(
    segs: list[Segment],
    mode: ScaleMode,
) -> tuple[PatternKind, list[RuleResult]] | None:
    """Validate segments as a 5-wave sideway pattern; return its kind + rule results, or None."""
    # pp.36-41. Contract: r32∈[0.5,0.99] & r54∈[0.236,0.99]. Balance: r32>1 & r54∈window. Expand: both>1.
    rules = run_checkers(CHECKERS, segs, mode)
    if rules is None:
        return None
    kind, classify_rules = _classify_5w_sideway(segs, mode)
    if kind is None:
        return None
    rules.extend(classify_rules)
    return kind, rules


def _check_r1_count_alt(
    segs: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    return check_count_alternation(segs, mode, expected=5, rule_id="5ws.r1.count_5_alt")


def _check_r2_s2_window(
    segs: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    L1 = price_length(segs[0], mode)
    L2 = price_length(segs[1], mode)
    r = L2 / L1
    return [
        RuleResult(
            "5ws.r2.s2_in_window",
            in_range(r, R2_S2_MIN_RATIO_5WS, R2_S2_MAX_RATIO_5WS),
            measured=r,
            detail=f"[{R2_S2_MIN_RATIO_5WS}, {R2_S2_MAX_RATIO_5WS}]",
        )
    ]


def _check_r3_s4_window(
    segs: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    L3 = price_length(segs[2], mode)
    L4 = price_length(segs[3], mode)
    r = L4 / L3
    return [
        RuleResult(
            "5ws.r3.s4_in_window",
            in_range(r, R3_S4_MIN_RATIO_5WS, R3_S4_MAX_RATIO_5WS),
            measured=r,
            detail=f"[{R3_S4_MIN_RATIO_5WS}, {R3_S4_MAX_RATIO_5WS}]",
        )
    ]


CHECKERS: tuple[Checker, ...] = (
    _check_r1_count_alt,
    _check_r2_s2_window,
    _check_r3_s4_window,
)


def _classify_5w_sideway(
    segs: list[Segment],
    mode: ScaleMode,
) -> tuple[PatternKind | None, list[RuleResult]]:
    L2 = price_length(segs[1], mode)
    L3 = price_length(segs[2], mode)
    L4 = price_length(segs[3], mode)
    L5 = price_length(segs[4], mode)
    r_s3_s2 = L3 / L2
    r_s5_s4 = L5 / L4

    if in_range(r_s3_s2, R4_S3_MIN_CONTRACT_5WS, R4_S3_MAX_CONTRACT_5WS) and in_range(
        r_s5_s4, R5_S5_MIN_CONTRACT_5WS, R5_S5_MAX_CONTRACT_5WS
    ):
        return PatternKind.FIVE_SIDEWAY_CONTRACT, [
            RuleResult("5ws.r4.contract_s3", True, measured=r_s3_s2),
            RuleResult("5ws.r5.contract_s5", True, measured=r_s5_s4),
        ]

    if r_s3_s2 > SIDEWAY_EXPAND_BOUNDARY and in_range(
        r_s5_s4,
        R5_S5_MIN_CONTRACT_5WS,
        R5_S5_MAX_CONTRACT_5WS,
    ):
        return PatternKind.FIVE_SIDEWAY_BALANCE, [
            RuleResult("5ws.r4.balance_s3", True, measured=r_s3_s2),
            RuleResult("5ws.r5.balance_s5", True, measured=r_s5_s4),
        ]

    if r_s3_s2 > SIDEWAY_EXPAND_BOUNDARY and r_s5_s4 > SIDEWAY_EXPAND_BOUNDARY:
        return PatternKind.FIVE_SIDEWAY_EXPAND, [
            RuleResult("5ws.r4.expand_s3", True, measured=r_s3_s2),
            RuleResult("5ws.r5.expand_s5", True, measured=r_s5_s4),
        ]

    return None, []
