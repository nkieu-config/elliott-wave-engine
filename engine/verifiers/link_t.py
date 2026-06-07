from __future__ import annotations

from engine.adaptive import KIND_TO_FAMILY
from engine.constants import (
    R8_LINK_MAX_RATIO_LINK_T,
    R8_LINK_MIN_RATIO_LINK_T,
    R9_LINK_TIME_MULTIPLIER_LINK_T,
)
from engine.helpers import bar_span, in_range
from engine.types import (
    LinkSet,
    PatternKind,
    RuleResult,
    ScaleMode,
    Segment,
    WaveNode,
)
from engine.verifiers._link_helpers import (
    check_link_count,
    check_links_pull,
    per_link_ratio_check,
)
from engine.verifiers._link_helpers import set_trend_dir as _set_trend_dir
from engine.verifiers._runner import Checker, run_checkers


def verify_link_t(
    sets: list[LinkSet],
    children: list[WaveNode],
    links: list[Segment],
    mode: ScaleMode,
) -> tuple[PatternKind, list[RuleResult]] | None:
    """Validate link sets as a trend linkage (LINK_T); return its kind + rule results, or None."""
    rules = run_checkers(CHECKERS, sets, children, links, mode)
    if rules is None:
        return None
    return PatternKind.LINK_T, rules


def _check_r1_count(
    sets: list[LinkSet],
    children: list[WaveNode],
    links: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    del children, mode
    return check_link_count("link_t", sets, links)


def _check_r2_all_3w(
    sets: list[LinkSet],
    children: list[WaveNode],
    links: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    del children, links, mode
    for s in sets:
        if KIND_TO_FAMILY.get(s.pattern_kind) != "3W":
            return [RuleResult("link_t.r2.all_3w", False)]
    return [RuleResult("link_t.r2.all_3w", True)]


def _check_r3_first_normal(
    sets: list[LinkSet],
    children: list[WaveNode],
    links: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    del children, links, mode
    if sets[0].pattern_kind != PatternKind.THREE_NORMAL:
        return [RuleResult("link_t.r3.first_normal", False)]
    return [RuleResult("link_t.r3.first_normal", True)]


def _check_r4_middle_normal(
    sets: list[LinkSet],
    children: list[WaveNode],
    links: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    # Longer/Shorter subtypes allowed only on LAST set.
    del children, links, mode
    if len(sets) == 3 and sets[1].pattern_kind != PatternKind.THREE_NORMAL:
        return [RuleResult("link_t.r4.middle_normal", False)]
    return [RuleResult("link_t.r4.middle_normal", True)]


def _check_r5_same_trend(
    sets: list[LinkSet],
    children: list[WaveNode],
    links: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    del links, mode
    trend = _set_trend_dir(children, sets[0])
    for s in sets:
        if _set_trend_dir(children, s) != trend:
            return [RuleResult("link_t.r5.same_trend", False)]
    return [RuleResult("link_t.r5.same_trend", True)]


def _check_r6_links_pull(
    sets: list[LinkSet],
    children: list[WaveNode],
    links: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    del mode
    return check_links_pull("link_t.r6", children, sets, links)


def _check_r7_s1_gt_link(
    sets: list[LinkSet],
    children: list[WaveNode],
    links: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    # p.62: each set's s1 (full leg span, not first leaf segment) must exceed the
    # prior link; track worst-case (min) ratio across sets.
    items = [
        (i, _set_leg_segment(children, sets[i], 0), links[i - 1])
        for i in range(1, len(sets))
    ]
    return per_link_ratio_check(
        items,
        mode,
        accept=lambda r: r > 1.0,
        aggregate=min,
        fail_id=lambda i: f"link_t.r7.s1_gt_link_{i}",
        fail_detail=">1.0 required",
        ok_id="link_t.r7.s1_gt_link",
        ok_detail="min ratio across sets (>1.0)",
    )


def _check_r8_link_size(
    sets: list[LinkSet],
    children: list[WaveNode],
    links: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    window_str = f"[{R8_LINK_MIN_RATIO_LINK_T}, {R8_LINK_MAX_RATIO_LINK_T}]"
    items = [
        (i, lk, _set_last_leg_segment(children, sets[i])) for i, lk in enumerate(links)
    ]
    return per_link_ratio_check(
        items,
        mode,
        accept=lambda r: in_range(r, R8_LINK_MIN_RATIO_LINK_T, R8_LINK_MAX_RATIO_LINK_T),
        aggregate=max,
        fail_id=lambda i: f"link_t.r8.link_size_{i}",
        fail_detail=window_str,
        ok_id="link_t.r8.link_sizes",
        ok_detail=f"max ratio across links ({window_str})",
    )


def _check_r9_link_time(
    sets: list[LinkSet],
    children: list[WaveNode],
    links: list[Segment],
    mode: ScaleMode,
) -> list[RuleResult] | None:
    # Hard >200% time; skip (passed=True) when bar_index missing (synthetic fixtures).
    del mode
    rules: list[RuleResult] = []
    first_s2 = _set_leg_segment(children, sets[0], 1)
    first_s2_time = _seg_bar_span(first_s2) if first_s2 is not None else None
    if first_s2_time is None:
        rules.append(
            RuleResult(
                "link_t.r9.link_time_skipped",
                True,
                detail="bar_index unavailable on first-set s2 → R9 (>200% time) skipped",
            )
        )
        return rules

    min_ratio: float | None = None
    for i, lk in enumerate(links):
        link_time = _seg_bar_span(lk)
        prev_s3 = _set_last_leg_segment(children, sets[i])
        prev_s3_time = _seg_bar_span(prev_s3) if prev_s3 is not None else None
        if link_time is None or prev_s3_time is None:
            rules.append(
                RuleResult(
                    f"link_t.r9.link_time_skipped_{i}",
                    True,
                    detail="bar_index unavailable on link or prev s3 → R9 skipped for this link",
                )
            )
            continue
        ceiling_time = max(first_s2_time, prev_s3_time)
        if ceiling_time == 0:
            rules.append(
                RuleResult(
                    f"link_t.r9.link_time_skipped_{i}",
                    True,
                    detail="zero-bar reference → R9 skipped for this link",
                )
            )
            continue
        ratio = link_time / ceiling_time
        if ratio <= R9_LINK_TIME_MULTIPLIER_LINK_T:
            rules.append(
                RuleResult(
                    f"link_t.r9.link_time_{i}",
                    False,
                    measured=ratio,
                    detail=(
                        f"p.94: link[{i}] time / max(t(first_s2)={first_s2_time}, t(prev_s3)={prev_s3_time}) "
                        f"= {ratio:.3f} (>{R9_LINK_TIME_MULTIPLIER_LINK_T} required)"
                    ),
                )
            )
            return rules
        min_ratio = ratio if min_ratio is None else min(min_ratio, ratio)
    rules.append(
        RuleResult(
            "link_t.r9.link_times",
            True,
            measured=min_ratio,
            detail=(
                f"min ratio across links (>{R9_LINK_TIME_MULTIPLIER_LINK_T} of "
                "max(first_s2_time, prev_s3_time))"
            ),
        )
    )
    return rules


# p.94 R1..R9 order; run_checkers aborts at first None / passed=False.
CHECKERS: tuple[Checker, ...] = (
    _check_r1_count,
    _check_r2_all_3w,
    _check_r3_first_normal,
    _check_r4_middle_normal,
    _check_r5_same_trend,
    _check_r6_links_pull,
    _check_r7_s1_gt_link,
    _check_r8_link_size,
    _check_r9_link_time,
)


def _set_leg_segment(
    children: list[WaveNode],
    set_obj: LinkSet,
    leg_idx: int,
) -> Segment | None:
    target = set_obj.leg_start + leg_idx
    if target > set_obj.leg_end or target >= len(children):
        return None
    leg = children[target]
    if leg.span_end is None:
        return None
    return Segment(start=leg.span_start, end=leg.span_end)


def _set_last_leg_segment(
    children: list[WaveNode],
    set_obj: LinkSet,
) -> Segment | None:
    if set_obj.leg_end >= len(children):
        return None
    leg = children[set_obj.leg_end]
    if leg.span_end is None:
        return None
    return Segment(start=leg.span_start, end=leg.span_end)


def _seg_bar_span(seg: Segment | None) -> int | None:
    if seg is None:
        return None
    return bar_span(seg.start, seg.end)


__all__ = ["verify_link_t"]
