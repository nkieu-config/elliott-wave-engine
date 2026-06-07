from __future__ import annotations

from datetime import datetime, timedelta
from itertools import count

from engine.parser.types import _Leg
from engine.types import Bar, Pivot, WaveRole

# Pivot indices auto-increment; the autouse fixture in tests/engine/conftest.py
# resets the count per test, so numbering is isolated regardless of importer.
_ids = count()


def reset_pivot_counter() -> None:
    global _ids
    _ids = count()


def _pivot(price: float, bar: int) -> Pivot:
    return Pivot(
        index=next(_ids),
        time=datetime(2020, 1, 1),
        price=price,
        kind="high",
        bar_index=bar,
    )


def _leg(p0: tuple[float, int], p1: tuple[float, int]) -> _Leg:
    return _Leg(role=WaveRole.S1, span_start=_pivot(*p0), span_end=_pivot(*p1))


def linear_bars(
    start_price: float,
    end_price: float,
    start_bar: int,
    end_bar: int,
    *,
    wick: float = 0.015,
    abs_wick: float | None = None,
) -> list[Bar]:
    """Linear close ramp; wick is fractional half-height of |delta|, or abs_wick if given."""
    bars: list[Bar] = []
    span = end_bar - start_bar
    if span <= 0:
        return bars
    delta = end_price - start_price
    pad = abs_wick if abs_wick is not None else abs(delta) * wick
    prev_close = start_price
    for i in range(span):
        close = start_price + (i + 1) / span * delta
        open_ = prev_close
        bars.append(
            Bar(
                time=datetime(2020, 1, 1) + timedelta(days=start_bar + i + 1),
                open=open_,
                high=max(open_, close) + pad,
                low=min(open_, close) - pad,
                close=close,
            )
        )
        prev_close = close
    return bars
