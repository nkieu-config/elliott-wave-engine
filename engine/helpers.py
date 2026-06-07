from __future__ import annotations

import math
from collections.abc import Sequence

from engine.constants import EQUAL_WITHIN_DEFAULT_TOLERANCE
from engine.types import Pivot, ScaleMode, Segment, TrendDir


def price_length(seg: Segment, mode: ScaleMode) -> float:
    if mode == "linear":
        return abs(seg.end.price - seg.start.price)
    if min(seg.start.price, seg.end.price) <= 0:
        return 0.0  # log undefined for non-positive prices
    return abs(math.log(seg.end.price) - math.log(seg.start.price))


def total_price_range(segs: Sequence[Segment], mode: ScaleMode) -> float:
    if not segs:
        return 0.0
    highs = [max(s.start.price, s.end.price) for s in segs]
    lows = [min(s.start.price, s.end.price) for s in segs]
    if mode == "linear":
        return max(highs) - min(lows)
    if min(lows) <= 0:
        return 0.0  # log undefined for non-positive prices
    return math.log(max(highs)) - math.log(min(lows))


def alternates(segs: Sequence[Segment]) -> bool:
    return all(
        segs[i].direction != segs[i - 1].direction for i in range(1, len(segs))
    )


def in_range(x: float, lo: float, hi: float) -> bool:
    return lo <= x <= hi


def is_push(seg: Segment, trend: TrendDir) -> bool:
    return seg.direction == trend


def is_pull(seg: Segment, trend: TrendDir) -> bool:
    return seg.direction != trend


def equal_within(
    values: Sequence[float],
    tolerance: float = EQUAL_WITHIN_DEFAULT_TOLERANCE,
) -> bool:
    if len(values) < 2:
        return True
    lo, hi = min(values), max(values)
    if lo == 0:
        return hi == 0
    return (hi - lo) / lo <= tolerance


def argmax_index(xs: Sequence[float]) -> int:
    return max(range(len(xs)), key=lambda i: xs[i])


def bar_span(p1: Pivot, p2: Pivot) -> int | None:
    # Canonical time-axis helper (Gann Box pp.91, 94); skip-when-missing contract.
    if p1.bar_index is None or p2.bar_index is None:
        return None
    return abs(p2.bar_index - p1.bar_index)
