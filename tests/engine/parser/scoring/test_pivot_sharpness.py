from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from engine.parser.scoring.visual import pivot_sharpness
from engine.types import Bar
from tests.engine.parser.scoring._helpers import _leg, linear_bars


def _build_bars(legs: list[tuple[tuple[float, int], tuple[float, int]]]) -> list[Bar]:
    bars: list[Bar] = [
        Bar(
            time=datetime(2020, 1, 1),
            open=legs[0][0][0],
            high=legs[0][0][0] + 0.01,
            low=legs[0][0][0] - 0.01,
            close=legs[0][0][0],
        )
    ]
    for p0, p1 in legs:
        bars.extend(linear_bars(p0[0], p1[0], p0[1], p1[1]))
    return bars


class TestPivotSharpness:
    def test_inactive_with_one_leg(self):
        legs = [_leg((100, 0), (110, 10))]
        assert pivot_sharpness(legs, bars=()) is None

    def test_inactive_without_bars(self):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (105, 20)),
        ]
        assert pivot_sharpness(legs, bars=()) is None

    def test_linear_bars_produce_sharp_pivots(self):
        legs_spec = [((100, 0), (110, 10)), ((110, 10), (100, 20))]
        legs = [_leg(p0, p1) for p0, p1 in legs_spec]
        bars = tuple(_build_bars(legs_spec))
        s = pivot_sharpness(legs, bars)
        assert s is not None
        assert s == pytest.approx(1.0, abs=0.05)

    def test_creeping_bars_lower_score(self):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (100, 20)),
        ]
        bars: list[Bar] = [
            Bar(
                time=datetime(2020, 1, 1),
                open=100,
                high=100.01,
                low=99.99,
                close=100,
            )
        ]
        for i in range(8):
            bars.append(
                Bar(
                    time=datetime(2020, 1, 1) + timedelta(days=i + 1),
                    open=100 + i * 1.25,
                    high=100 + (i + 1) * 1.25 + 0.5,
                    low=100 + i * 1.25 - 0.5,
                    close=100 + (i + 1) * 1.25,
                )
            )
        for j in range(2):
            bars.append(
                Bar(
                    time=datetime(2020, 1, 1) + timedelta(days=9 + j),
                    open=110.0,
                    high=110.05,
                    low=109.95,
                    close=110.0,
                )
            )
        bars.extend(linear_bars(110, 100, 10, 20))
        s = pivot_sharpness(legs, tuple(bars))
        assert s is not None
        assert s < 0.7
