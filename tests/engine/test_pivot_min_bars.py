from __future__ import annotations

from datetime import datetime, timedelta

from engine.pivot import enforce_min_bars
from engine.types import Pivot


def _t(idx: int) -> datetime:
    return datetime(2020, 1, 1) + timedelta(weeks=idx)


def _p(bar_idx: int, price: float, kind: str, idx: int = 0) -> Pivot:
    return Pivot(index=idx, time=_t(bar_idx), price=price, kind=kind, bar_index=bar_idx)  # type: ignore[arg-type]


def test_disabled_when_min_bars_le_1() -> None:
    pivots = [_p(0, 100, "low"), _p(1, 110, "high"), _p(2, 95, "low")]
    assert enforce_min_bars(pivots, min_bars=1) == pivots
    assert enforce_min_bars(pivots, min_bars=0) == pivots


def test_empty_and_single() -> None:
    assert enforce_min_bars([], min_bars=4) == []
    single = [_p(0, 100, "low")]
    assert enforce_min_bars(single, min_bars=4) == single


def test_drops_short_leg_keeps_more_extreme_high() -> None:
    pivots = [
        _p(0, 100, "high"),
        _p(2, 98, "low"),
        _p(20, 110, "high"),
    ]
    out = enforce_min_bars(pivots, min_bars=4)
    assert len(out) == 1
    assert out[0].bar_index == 20 and out[0].price == 110


def test_drops_short_leg_keeps_more_extreme_low() -> None:
    pivots = [
        _p(0, 100, "low"),
        _p(2, 105, "high"),
        _p(20, 80, "low"),
    ]
    out = enforce_min_bars(pivots, min_bars=4)
    assert len(out) == 1
    assert out[0].bar_index == 20 and out[0].price == 80


def test_keeps_pivots_when_all_legs_long_enough() -> None:
    pivots = [
        _p(0, 100, "low"),
        _p(10, 130, "high"),
        _p(25, 95, "low"),
        _p(40, 140, "high"),
    ]
    out = enforce_min_bars(pivots, min_bars=4)
    assert len(out) == 4
    assert [p.bar_index for p in out] == [0, 10, 25, 40]


def test_preserves_extreme_high_when_quick_dip_after() -> None:
    pivots = [
        _p(0, 50, "low"),
        _p(100, 200, "high"),
        _p(102, 130, "low"),
    ]
    out = enforce_min_bars(pivots, min_bars=4)
    assert len(out) == 2
    assert out[-1].bar_index == 100 and out[-1].price == 200


def test_cascades_through_multiple_short_legs() -> None:
    pivots = [
        _p(0, 100, "low"),
        _p(10, 105, "high"),
        _p(12, 102, "low"),
        _p(14, 120, "high"),
        _p(50, 80, "low"),
    ]
    out = enforce_min_bars(pivots, min_bars=4)
    assert [p.bar_index for p in out] == [0, 14, 50]
    assert out[1].price == 120


def test_reindexes_output() -> None:
    pivots = [
        _p(0, 100, "low"),
        _p(2, 110, "high"),
        _p(20, 130, "high"),
        _p(40, 90, "low"),
    ]
    out = enforce_min_bars(pivots, min_bars=4)
    for i, p in enumerate(out):
        assert p.index == i


def test_preserves_alternation() -> None:
    pivots = [
        _p(0, 100, "low"),
        _p(2, 105, "high"),
        _p(3, 102, "low"),
        _p(20, 130, "high"),
        _p(40, 90, "low"),
    ]
    out = enforce_min_bars(pivots, min_bars=4)
    for i in range(1, len(out)):
        assert out[i].kind != out[i - 1].kind


def test_does_not_mutate_input() -> None:
    pivots = [
        _p(0, 100, "low"),
        _p(2, 110, "high"),
        _p(20, 90, "low"),
    ]
    snapshot = list(pivots)
    enforce_min_bars(pivots, min_bars=4)
    assert pivots == snapshot
