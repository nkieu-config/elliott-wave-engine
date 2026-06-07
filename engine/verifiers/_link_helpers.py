from __future__ import annotations

from collections.abc import Callable, Sequence

from engine.helpers import price_length
from engine.types import (
    LinkSet,
    RuleResult,
    ScaleMode,
    Segment,
    TrendDir,
    WaveNode,
    WaveRole,
)

__all__ = [
    "check_link_count",
    "check_links_pull",
    "link_set_view",
    "per_link_ratio_check",
    "set_trend_dir",
]


def check_link_count(
    prefix: str,
    sets: list[LinkSet],
    links: list[Segment],
) -> list[RuleResult] | None:
    # R1: 2-3 sets with exactly len(sets)-1 links.
    if len(sets) < 2 or len(sets) > 3:
        return None
    if len(links) != len(sets) - 1:
        return None
    return [RuleResult(f"{prefix}.r1.count_ok", True)]


def check_links_pull(
    rule_id_prefix: str,
    children: list[WaveNode],
    sets: list[LinkSet],
    links: list[Segment],
) -> list[RuleResult] | None:
    # Every link must be a Pull-Wave (counter-trend). link_t R6 / link_s R4 (p.56).
    trend = set_trend_dir(children, sets[0])
    for lk in links:
        if lk.direction == trend:
            return [RuleResult(f"{rule_id_prefix}.links_are_pull", False)]
    return [RuleResult(f"{rule_id_prefix}.links_are_pull", True)]


def per_link_ratio_check(
    items: Sequence[tuple[int, Segment | None, Segment | None]],
    mode: ScaleMode,
    *,
    accept: Callable[[float], bool],
    aggregate: Callable[[float, float], float],
    fail_id: Callable[[int], str],
    fail_detail: str,
    ok_id: str,
    ok_detail: str,
) -> list[RuleResult] | None:
    # link_t R7/R8. items=(id_index, value_seg, ref_seg); ratio=len(value)/len(ref).
    # Missing segment or zero-length ref aborts the whole pattern (None); R9's time
    # rule skips-and-continues instead, by design.
    best: float | None = None
    for idx, value_seg, ref_seg in items:
        if value_seg is None or ref_seg is None:
            return None
        ref_len = price_length(ref_seg, mode)
        if ref_len == 0:
            return None
        ratio = price_length(value_seg, mode) / ref_len
        if not accept(ratio):
            return [RuleResult(fail_id(idx), False, measured=ratio, detail=fail_detail)]
        best = ratio if best is None else aggregate(best, ratio)
    return [RuleResult(ok_id, True, measured=best, detail=ok_detail)]


def set_trend_dir(children: list[WaveNode], set_obj: LinkSet) -> TrendDir:
    # Uniform "up" fallback keeps cross-set rules (link_t R5/R6, link_s R4) pass-through.
    if set_obj.leg_start >= len(children):
        return "up"
    s1 = children[set_obj.leg_start]
    if s1.span_end is None:
        return "up"
    return "up" if s1.span_end.price > s1.span_start.price else "down"


def link_set_view(
    parent: WaveNode | list[WaveNode],
    set_obj: LinkSet,
) -> WaveNode | None:
    children = parent.children if isinstance(parent, WaveNode) else parent
    if set_obj.leg_start < 0 or set_obj.leg_end >= len(children):
        return None
    leg_slice = children[set_obj.leg_start : set_obj.leg_end + 1]
    if not leg_slice or leg_slice[-1].span_end is None:
        return None
    return WaveNode(
        role=WaveRole.ANCHOR,
        span_start=leg_slice[0].span_start,
        span_end=leg_slice[-1].span_end,
        pattern_kind=set_obj.pattern_kind,
        children=list(leg_slice),
    )
