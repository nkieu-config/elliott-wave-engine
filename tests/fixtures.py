from __future__ import annotations

from datetime import datetime, timedelta

from engine.types import Bar, Pivot, Segment


def make_bar(idx: int, o: float, h: float, low: float, c: float) -> Bar:
    return Bar(
        time=datetime(2020, 1, 1) + timedelta(weeks=idx),
        open=o,
        high=h,
        low=low,
        close=c,
    )


def make_flat_bar(idx: int, price: float) -> Bar:
    return make_bar(idx, price, price, price, price)


def build_5w_trend_segments(
    L1: float,
    L2: float,
    L3: float,
    L4: float,
    L5: float,
    s2_weeks: int = 2,
    s3_weeks: int = 1,
    s4_weeks: int = 1,
    s5_weeks: int = 1,
    *,
    trend_dir: str = "up",
) -> list[Segment]:
    if trend_dir not in ("up", "down"):
        raise ValueError(f"trend_dir must be 'up' or 'down', got {trend_dir!r}")
    base = datetime(2020, 1, 1)
    t0 = 0
    t1 = t0 + 1
    t2 = t1 + s2_weeks
    t3 = t2 + s3_weeks
    t4 = t3 + s4_weeks
    t5 = t4 + s5_weeks
    sign = 1.0 if trend_dir == "up" else -1.0
    kind_at = ("low", "high") if trend_dir == "up" else ("high", "low")
    p0 = Pivot(0, base, 100, kind_at[0], t0)
    p1 = Pivot(1, base + timedelta(weeks=t1), 100 + sign * L1, kind_at[1], t1)
    p2 = Pivot(2, base + timedelta(weeks=t2), 100 + sign * (L1 - L2), kind_at[0], t2)
    p3 = Pivot(3, base + timedelta(weeks=t3), 100 + sign * (L1 - L2 + L3), kind_at[1], t3)
    p4 = Pivot(4, base + timedelta(weeks=t4), 100 + sign * (L1 - L2 + L3 - L4), kind_at[0], t4)
    p5 = Pivot(5, base + timedelta(weeks=t5), 100 + sign * (L1 - L2 + L3 - L4 + L5), kind_at[1], t5)
    return [
        Segment(p0, p1),
        Segment(p1, p2),
        Segment(p2, p3),
        Segment(p3, p4),
        Segment(p4, p5),
    ]


def ip_pivot(idx: int, weeks: int, price: float, kind: str) -> Pivot:
    return Pivot(
        index=idx,
        time=datetime(2020, 1, 1) + timedelta(weeks=weeks),
        price=price,
        kind=kind,  # type: ignore[arg-type]
        bar_index=weeks,
    )


def ip_pivot_no_bar(idx: int, weeks: int, price: float, kind: str) -> Pivot:
    return Pivot(
        index=idx,
        time=datetime(2020, 1, 1) + timedelta(weeks=weeks),
        price=price,
        kind=kind,  # type: ignore[arg-type]
        bar_index=None,
    )


def degree_leg(bars: int, price_delta: float):
    """Single up _Leg spanning `bars` weeks with the given price delta."""
    from engine.parser.types import _Leg
    from engine.types import WaveRole

    base = datetime(2020, 1, 1)
    p0 = Pivot(0, base, 100.0, "low", 0)
    p1 = Pivot(1, base + timedelta(weeks=bars), 100.0 + price_delta, "high", bars)
    return _Leg(role=WaveRole.S1, span_start=p0, span_end=p1)


def make_segments(prices: list[float], start: datetime | None = None) -> list[Segment]:
    if len(prices) < 2:
        return []
    if start is None:
        start = datetime(2020, 1, 1)

    pivots: list[Pivot] = []
    for i, price in enumerate(prices):
        if i == 0:
            kind = "low" if (len(prices) > 1 and prices[1] > price) else "high"
        elif i == len(prices) - 1:
            kind = "high" if prices[i - 1] < price else "low"
        else:
            if prices[i - 1] < price > prices[i + 1]:
                kind = "high"
            elif prices[i - 1] > price < prices[i + 1]:
                kind = "low"
            else:
                kind = "high" if prices[i - 1] < price else "low"

        pivots.append(
            Pivot(
                index=i,
                time=start + timedelta(weeks=i),
                price=price,
                kind=kind,  # type: ignore[arg-type]
                bar_index=i,
            )
        )

    return [Segment(start=pivots[i], end=pivots[i + 1]) for i in range(len(pivots) - 1)]


def lengths(segs: list[Segment], mode: str = "linear") -> list[float]:
    from engine.helpers import price_length

    return [price_length(s, mode) for s in segs]  # type: ignore[arg-type]


def build_hypothesis_with_legs(legs):
    import uuid

    from engine.parser.types import _Context, _Hypothesis

    root = _Context(family="3W", legs=list(legs))
    return _Hypothesis(id=str(uuid.uuid4()), context_stack=[root])
