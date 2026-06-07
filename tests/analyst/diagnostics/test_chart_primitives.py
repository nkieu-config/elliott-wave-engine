from datetime import datetime, timedelta

import pytest

from analyst.diagnostics.chart_primitives import (
    bars_break_trendline,
    bars_reach_price,
    trendline_at,
)
from engine.types import Bar
from tests.analyst._helpers import _pv


def _bars(prices: list[float]) -> list[Bar]:
    return [
        Bar(
            time=datetime(2020, 1, 1) + timedelta(days=i),
            open=p, high=p, low=p, close=p, volume=0,
        )
        for i, p in enumerate(prices)
    ]


def test_trendline_at_linear():
    p1 = _pv(0, 100.0, 0)
    p2 = _pv(1, 110.0, 10)
    assert trendline_at(p1, p2, bar_index=5, mode="linear") == pytest.approx(105.0)


def test_trendline_at_log():
    p1 = _pv(0, 100.0, 0)
    p2 = _pv(1, 200.0, 10)
    assert trendline_at(p1, p2, bar_index=5, mode="log") == pytest.approx(141.42, abs=0.01)


def test_bars_break_trendline_downward():
    p1 = _pv(0, 100.0, 0)
    p2 = _pv(1, 110.0, 5)
    bars = _bars([100, 102, 104, 106, 108, 110, 113, 90, 95])
    idx = bars_break_trendline(bars, p1, p2, direction="down", mode="linear", after_bar=5)
    assert idx == 7


def test_bars_break_trendline_none_when_no_break():
    p1 = _pv(0, 100.0, 0)
    p2 = _pv(1, 110.0, 5)
    bars = _bars([100, 102, 104, 106, 108, 110, 113, 115, 117])
    idx = bars_break_trendline(bars, p1, p2, direction="down", mode="linear", after_bar=5)
    assert idx is None


def test_bars_reach_price_up():
    bars = _bars([100, 105, 110, 115])
    assert bars_reach_price(bars, 112.0, direction="up", after_bar=0) == 3
