from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from engine.degree import axis_for_family, measure_leg
from engine.parser.types import _Leg
from engine.types import Pivot, WaveRole
from tests.fixtures import degree_leg as _leg


@pytest.mark.parametrize(
    ("family", "expected"),
    [
        ("5W_TREND", "time"),
        ("LINK_T", "time"),
        ("5W_SIDEWAY", "price"),
        ("3W", "price"),
        ("LINK_S", "price"),
    ],
    ids=["5w_trend", "link_t", "5w_sideway", "3w", "link_s"],
)
def test_axis_for_family(family: str, expected: str) -> None:
    assert axis_for_family(family) == expected


def test_measure_leg_time_returns_bar_span() -> None:
    leg = _leg(bars=5, price_delta=30.0)
    assert measure_leg(leg, "time", "linear") == pytest.approx(5.0)


def test_measure_leg_price_returns_magnitude() -> None:
    leg = _leg(bars=5, price_delta=30.0)
    assert measure_leg(leg, "price", "linear") == pytest.approx(30.0)


def test_measure_leg_time_none_when_bar_index_missing() -> None:
    base = datetime(2020, 1, 1)
    p0 = Pivot(0, base, 100.0, "low", None)
    p1 = Pivot(1, base + timedelta(weeks=5), 130.0, "high", None)
    leg = _Leg(role=WaveRole.S1, span_start=p0, span_end=p1)
    assert measure_leg(leg, "time", "linear") is None


def test_measure_leg_price_none_when_zero_magnitude() -> None:
    leg = _leg(bars=5, price_delta=0.0)
    assert measure_leg(leg, "price", "linear") is None
