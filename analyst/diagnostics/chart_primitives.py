from __future__ import annotations

import math

from engine import Bar, Pivot, ScaleMode, TrendDir


def trendline_at(
    p1: Pivot, p2: Pivot, bar_index: int, mode: ScaleMode,
) -> float:
    if p1.bar_index is None or p2.bar_index is None:
        raise ValueError("Pivots must carry bar_index for trendline_at")
    x1, x2 = p1.bar_index, p2.bar_index
    if x2 == x1:
        raise ValueError("p1 and p2 have the same bar_index; line undefined")
    if mode == "linear":
        slope = (p2.price - p1.price) / (x2 - x1)
        return p1.price + slope * (bar_index - x1)
    ly1, ly2 = math.log(p1.price), math.log(p2.price)
    slope = (ly2 - ly1) / (x2 - x1)
    ly = ly1 + slope * (bar_index - x1)
    return math.exp(ly)


def bars_break_trendline(
    bars: list[Bar],
    p1: Pivot,
    p2: Pivot,
    *,
    direction: TrendDir,
    mode: ScaleMode,
    after_bar: int,
) -> int | None:
    # No anchored pivots → no line; treat as "not broken" (don't let it raise).
    if p1.bar_index is None or p2.bar_index is None:
        return None
    for i in range(after_bar + 1, len(bars)):
        line = trendline_at(p1, p2, bar_index=i, mode=mode)
        c = bars[i].close
        if direction == "down" and c < line:
            return i
        if direction == "up" and c > line:
            return i
    return None


def bars_reach_price(
    bars: list[Bar],
    price: float,
    *,
    direction: TrendDir,
    after_bar: int,
) -> int | None:
    for i in range(after_bar + 1, len(bars)):
        if direction == "up" and bars[i].high >= price:
            return i
        if direction == "down" and bars[i].low <= price:
            return i
    return None


def bars_after_pivot(bars: list[Bar], pivot: Pivot) -> list[Bar]:
    if pivot.bar_index is None:
        return []
    return bars[pivot.bar_index + 1 :]
