from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from engine.parser.runtime import RuntimeContext
from engine.parser.types import _Leg
from engine.types import Bar, Pivot, WaveRole
from tests.engine.parser.scoring._helpers import linear_bars
from tests.fixtures import build_hypothesis_with_legs

# Pivot-index counter reset per test by the autouse fixture in tests/engine/conftest.py.


def _pivot(price: float, bar: int, idx: int) -> Pivot:
    return Pivot(
        index=idx,
        time=datetime(2020, 1, 1) + timedelta(days=bar),
        price=price,
        kind="high",
        bar_index=bar,
    )


def _leg(p0: tuple[float, int], p1: tuple[float, int], idx_offset: int = 0) -> _Leg:
    return _Leg(
        role=WaveRole.S1,
        span_start=_pivot(*p0, idx_offset),
        span_end=_pivot(*p1, idx_offset + 1),
    )


@pytest.fixture
def sample_hypothesis_with_bars():
    legs_spec = [
        ((100.0, 0), (110.0, 10)),
        ((110.0, 10), (105.0, 15)),
        ((105.0, 15), (115.0, 25)),
    ]
    legs = [_leg(p0, p1, idx_offset=i * 2) for i, (p0, p1) in enumerate(legs_spec)]
    h = build_hypothesis_with_legs(legs)
    mode = "linear"

    anchor_price = legs_spec[0][0][0]
    all_bars: list[Bar] = [
        Bar(
            time=datetime(2020, 1, 1),
            open=anchor_price,
            high=anchor_price + 0.01,
            low=anchor_price - 0.01,
            close=anchor_price,
        )
    ]
    for (p0_price, p0_bar), (p1_price, p1_bar) in legs_spec:
        all_bars.extend(linear_bars(p0_price, p1_price, p0_bar, p1_bar))

    runtime = RuntimeContext.from_bars(all_bars)
    return h, mode, runtime
