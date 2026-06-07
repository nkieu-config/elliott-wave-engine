from __future__ import annotations

from datetime import datetime, timedelta

from engine.parser.scoring.visual import leg_smoothness
from engine.types import Bar
from tests.engine.parser.scoring._helpers import _leg, linear_bars


def _bar(idx: int, op: float, hi: float, lo: float, cl: float) -> Bar:
    return Bar(
        time=datetime(2020, 1, 1) + timedelta(days=idx),
        open=op,
        high=hi,
        low=lo,
        close=cl,
    )


def _smooth_up_bars(
    start_price: float, end_price: float, start_bar: int, end_bar: int
) -> list[Bar]:
    return linear_bars(start_price, end_price, start_bar, end_bar, abs_wick=0.05)


class TestLegSmoothness:
    def test_smooth_leg_scores_near_one(self):
        legs = [_leg((100, 0), (110, 10))]
        bars: list[Bar] = [_bar(0, 100, 100.05, 99.95, 100)]
        bars.extend(_smooth_up_bars(100, 110, 0, 10))
        s = leg_smoothness(legs, tuple(bars))
        assert s is not None
        assert s > 0.95

    def test_zigzag_leg_scores_lower(self):
        legs = [_leg((100, 0), (110, 10))]
        bars: list[Bar] = [_bar(0, 100, 100.05, 99.95, 100)]
        bars.append(_bar(1, 100, 102, 99.5, 102))
        bars.append(_bar(2, 102, 104, 101.5, 104))
        bars.append(_bar(3, 104, 105, 103, 105))
        bars.append(_bar(4, 105, 105.1, 100.5, 101))
        for i, p in enumerate([103, 105, 107, 108, 109, 110], start=5):
            bars.append(_bar(i, p - 1, p + 0.5, p - 1, p))
        s = leg_smoothness(legs, tuple(bars))
        assert s is not None
        assert s < 0.7

    def test_inactive_without_bars(self):
        legs = [_leg((100, 0), (110, 10))]
        assert leg_smoothness(legs, ()) is None

    def test_inactive_when_no_legs(self):
        assert leg_smoothness([], ()) is None

    def test_down_leg_uses_drawup_instead(self):
        legs = [_leg((110, 0), (100, 10))]
        bars: list[Bar] = [_bar(0, 110, 110.05, 109.95, 110)]
        bars.extend(_smooth_up_bars(110, 100, 0, 10))
        s = leg_smoothness(legs, tuple(bars))
        assert s is not None
        assert s > 0.95

    def test_inactive_when_leg_has_zero_length(self):
        legs = [_leg((100, 0), (100, 10))]
        bars = tuple(_smooth_up_bars(100, 100, 0, 10))
        assert leg_smoothness(legs, bars) is None
