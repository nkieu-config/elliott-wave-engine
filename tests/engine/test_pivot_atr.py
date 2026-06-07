from __future__ import annotations

import random

import pytest

from engine.pivot import (
    _compute_atr,
    compute_zigzag_pivots_atr,
)
from engine.types import Bar
from tests.fixtures import make_bar as _bar
from tests.fixtures import make_flat_bar as _flat_bar


def test_atr_empty_bars_returns_empty() -> None:
    assert _compute_atr([], period=14) == []


def test_atr_period_zero_raises() -> None:
    with pytest.raises(ValueError, match="atr_period"):
        _compute_atr([_flat_bar(0, 100)], period=0)


def test_atr_first_bar_uses_bar_range() -> None:
    bars = [_bar(0, 100, 110, 90, 100)]
    atr = _compute_atr(bars, period=14)
    assert atr == pytest.approx([20.0])


def test_atr_formula_uses_max_of_three_terms() -> None:
    bars = [
        _bar(0, 100, 100, 100, 100),
        _bar(1, 120, 125, 115, 120),
    ]
    atr = _compute_atr(bars, period=14)
    assert atr[0] == 0.0
    assert atr[1] == pytest.approx(12.5)


def test_atr_partial_window_uses_what_is_available() -> None:
    bars = [
        _bar(0, 100, 105, 95, 100),
        _bar(1, 100, 110, 95, 100),
        _bar(2, 100, 108, 99, 100),
    ]
    atr = _compute_atr(bars, period=14)
    assert atr[0] == pytest.approx(10.0)
    assert atr[1] == pytest.approx(12.5)
    assert atr[2] == pytest.approx((10 + 15 + 9) / 3)


def test_atr_rolling_window_drops_oldest() -> None:
    bars = [_bar(i, 100, 100 + (i % 3), 100 - (i % 3), 100) for i in range(10)]
    atr = _compute_atr(bars, period=3)
    assert atr[3] == pytest.approx(2.0)
    assert atr[4] == pytest.approx(2.0)


def test_atr_zigzag_empty_input() -> None:
    assert compute_zigzag_pivots_atr([]) == []
    assert compute_zigzag_pivots_atr([_flat_bar(0, 100)]) == []


def test_atr_zigzag_alternates_high_low() -> None:
    rng = random.Random(123)
    prices = [100.0]
    for _ in range(80):
        prices.append(prices[-1] * (1 + rng.uniform(-0.06, 0.06)))
    bars = [_flat_bar(i, p) for i, p in enumerate(prices)]

    pivots = compute_zigzag_pivots_atr(
        bars,
        atr_period=10,
        atr_multiplier=2.0,
        floor_threshold=0.0,
    )
    for i in range(1, len(pivots)):
        assert pivots[i].kind != pivots[i - 1].kind, f"alternation broken at {i}"


def test_atr_zigzag_bar_index_tracked() -> None:
    bars = [
        _flat_bar(0, 100),
        _flat_bar(1, 120),
        _flat_bar(2, 100),
        _flat_bar(3, 80),
        _flat_bar(4, 110),
    ]
    pivots = compute_zigzag_pivots_atr(
        bars,
        atr_period=2,
        atr_multiplier=1.0,
        floor_threshold=0.05,
    )
    for p in pivots:
        assert p.bar_index is not None
        assert 0 <= p.bar_index < len(bars)


def test_atr_zigzag_threshold_scales_with_volatility() -> None:
    def _series(amp: float) -> list[Bar]:
        pts: list[float] = [100.0]
        for _ in range(4):
            pts.append(pts[-1] * (1 + amp))
            pts.append(pts[-1] * (1 - amp))
        return [_flat_bar(i, p) for i, p in enumerate(pts)]

    calm = _series(0.05)
    volatile = _series(0.25)

    pv_calm = compute_zigzag_pivots_atr(
        calm,
        atr_period=3,
        atr_multiplier=1.0,
        floor_threshold=0.0,
    )
    pv_vol = compute_zigzag_pivots_atr(
        volatile,
        atr_period=3,
        atr_multiplier=1.0,
        floor_threshold=0.0,
    )
    # ATR threshold scales per-series, so calm/volatile resolve the same 8-swing
    # structure; a fixed threshold would fragment volatile or miss calm.
    calm_range = max(b.close for b in calm) - min(b.close for b in calm)
    vol_range = max(b.close for b in volatile) - min(b.close for b in volatile)
    assert vol_range > 5 * calm_range
    assert len(pv_calm) >= 5
    assert len(pv_vol) >= 5
    assert abs(len(pv_calm) - len(pv_vol)) <= 1


def test_atr_zigzag_floor_threshold_enforced() -> None:
    flat = [_flat_bar(i, 100.0) for i in range(50)]
    bars = flat[:]
    bars[25] = _flat_bar(25, 104.0)

    pivots = compute_zigzag_pivots_atr(
        bars,
        atr_period=14,
        atr_multiplier=3.0,
        floor_threshold=0.05,
    )
    bumped = [p for p in pivots if p.bar_index == 25]
    assert not bumped, f"4% bump shouldn't pivot under 5% floor; got {bumped}"

    pivots_low_floor = compute_zigzag_pivots_atr(
        bars,
        atr_period=14,
        atr_multiplier=3.0,
        floor_threshold=0.01,
    )
    assert any(p.bar_index == 25 for p in pivots_low_floor), (
        "4% bump should register under 1% floor"
    )


def test_atr_zigzag_higher_multiplier_fewer_pivots() -> None:
    rng = random.Random(7)
    prices = [100.0]
    for _ in range(120):
        prices.append(prices[-1] * (1 + rng.uniform(-0.08, 0.08)))
    bars = [_flat_bar(i, p) for i, p in enumerate(prices)]

    counts = []
    for k in (0.5, 1.0, 2.0, 4.0):
        pivots = compute_zigzag_pivots_atr(
            bars,
            atr_period=10,
            atr_multiplier=k,
            floor_threshold=0.0,
        )
        counts.append(len(pivots))
    for i in range(1, len(counts)):
        assert counts[i] <= counts[i - 1], f"non-monotonic: multipliers→counts = {counts}"


def test_atr_zigzag_propagates_period_error() -> None:
    bars = [_flat_bar(0, 100), _flat_bar(1, 110)]
    with pytest.raises(ValueError, match="atr_period"):
        compute_zigzag_pivots_atr(bars, atr_period=0)
