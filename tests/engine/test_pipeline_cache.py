from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta

from engine.pipeline import _bars_digest
from engine.types import Bar


def _bar(i: int, o: float, h: float, low: float, c: float) -> Bar:
    return Bar(time=datetime(2024, 1, 1) + timedelta(weeks=i), open=o, high=h, low=low, close=c)


def _series() -> list[Bar]:
    return [_bar(i, 100 + i, 110 + i, 90 + i, 105 + i) for i in range(8)]


def test_bars_digest_stable_for_identical_bars() -> None:
    assert _bars_digest(_series()) == _bars_digest(_series())


def test_bars_digest_changes_when_any_ohlc_field_changes() -> None:
    base = _series()
    for field in ("open", "high", "low", "close"):
        revised = list(base)
        revised[3] = replace(base[3], **{field: getattr(base[3], field) + 1.0})
        assert _bars_digest(revised) != _bars_digest(base), field


def test_bars_digest_separates_same_pivots_different_content() -> None:
    # The bug: identical pivots (highs/lows) + identical length collided in the cache
    # key while count_waves scored differently off a revised open/close. The digest
    # must differ even when every high/low (hence every pivot) is unchanged.
    base = _series()
    revised = list(base)
    revised[-1] = replace(base[-1], open=base[-1].open + 5, close=base[-1].close + 5)
    assert (revised[-1].high, revised[-1].low) == (base[-1].high, base[-1].low)
    assert len(revised) == len(base)
    assert _bars_digest(revised) != _bars_digest(base)
