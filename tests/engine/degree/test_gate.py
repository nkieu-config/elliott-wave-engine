from __future__ import annotations

from datetime import datetime, timedelta

from engine.degree import gann_band_ok
from engine.parser.types import _Context, _Leg
from engine.types import Pivot, WaveRole
from tests.fixtures import degree_leg as _leg


def test_gann_band_ok_empty_legs_accepts() -> None:
    ctx = _Context(family="3W", legs=[])
    new_leg = _leg(bars=5, price_delta=30.0)
    assert gann_band_ok(ctx, new_leg, "linear") is True


def test_gann_band_ok_accepts_within_band() -> None:
    prior = _leg(bars=1, price_delta=30.0)
    ctx = _Context(family="3W", legs=[prior])
    new_leg = _leg(bars=1, price_delta=15.0)
    assert gann_band_ok(ctx, new_leg, "linear") is True


def test_gann_band_ok_rejects_below_band() -> None:
    prior = _leg(bars=1, price_delta=30.0)
    ctx = _Context(family="3W", legs=[prior])
    new_leg = _leg(bars=1, price_delta=5.0)
    assert gann_band_ok(ctx, new_leg, "linear") is False


def test_gann_band_ok_rejects_above_band() -> None:
    prior = _leg(bars=1, price_delta=10.0)
    ctx = _Context(family="3W", legs=[prior])
    new_leg = _leg(bars=1, price_delta=50.0)
    assert gann_band_ok(ctx, new_leg, "linear") is False


def test_gann_band_ok_5w_trend_uses_time_axis() -> None:
    prior = _leg(bars=3, price_delta=100.0)
    ctx = _Context(family="5W_TREND", legs=[prior])
    new_leg = _leg(bars=1, price_delta=100.0)
    assert gann_band_ok(ctx, new_leg, "linear") is True


def test_gann_band_ok_5w_trend_rejects_time_mismatch() -> None:
    prior = _leg(bars=4, price_delta=10.0)
    ctx = _Context(family="5W_TREND", legs=[prior])
    new_leg = _leg(bars=1, price_delta=10.0)
    assert gann_band_ok(ctx, new_leg, "linear") is False


def test_gann_band_ok_skips_unmeasurable_sibling() -> None:
    base = datetime(2020, 1, 1)
    p0 = Pivot(0, base, 100.0, "low", None)
    p1 = Pivot(1, base + timedelta(weeks=10), 130.0, "high", None)
    unmeasurable = _Leg(role=WaveRole.S1, span_start=p0, span_end=p1)
    ctx = _Context(family="5W_TREND", legs=[unmeasurable])
    new_leg = _leg(bars=5, price_delta=30.0)
    assert gann_band_ok(ctx, new_leg, "linear") is True
