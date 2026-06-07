from __future__ import annotations

from engine.anchor import find_anchor
from tests.fixtures import ip_pivot


def _pivot(bar_idx: int, price: float, kind: str):
    return ip_pivot(bar_idx, bar_idx, price, kind)


def test_find_anchor_empty_returns_none() -> None:
    assert find_anchor([]) is None


def test_find_anchor_no_low_pivots_returns_none() -> None:
    pivots = [_pivot(0, 200, "high"), _pivot(2, 220, "high")]
    assert find_anchor(pivots) is None


def test_find_anchor_picks_cheapest_low() -> None:
    pivots = [
        _pivot(0, 200, "high"),
        _pivot(1, 100, "low"),
        _pivot(2, 220, "high"),
        _pivot(3, 90, "low"),
        _pivot(4, 230, "high"),
        _pivot(5, 95, "low"),
    ]
    anchor = find_anchor(pivots)
    assert anchor is not None
    assert anchor.bar_index == 3
    assert anchor.price == 90
    assert anchor.kind == "low"


def test_find_anchor_tie_picks_earliest() -> None:
    pivots = [
        _pivot(0, 200, "high"),
        _pivot(1, 95, "low"),
        _pivot(2, 220, "high"),
        _pivot(3, 95, "low"),
    ]
    anchor = find_anchor(pivots)
    assert anchor is not None
    assert anchor.bar_index == 1


def test_find_anchor_single_low() -> None:
    pivots = [_pivot(0, 200, "high"), _pivot(1, 100, "low")]
    anchor = find_anchor(pivots)
    assert anchor is not None
    assert anchor.bar_index == 1
    assert anchor.price == 100
