from __future__ import annotations

import pytest

from engine.data.timeframe import (
    DEFAULT_TIMEFRAME,
    TIMEFRAMES,
    resolve_timeframe,
)


def test_timeframes_tuple_contents_and_order() -> None:
    assert TIMEFRAMES == ("day", "week", "month")


def test_default_timeframe_is_a_valid_key() -> None:
    assert DEFAULT_TIMEFRAME in TIMEFRAMES


@pytest.mark.parametrize(
    ("key", "yf_interval", "cache_label"),
    [
        ("day", "1d", "daily"),
        ("week", "1wk", "weekly"),
        ("month", "1mo", "monthly"),
    ],
)
def test_resolve_timeframe_maps_each_key(key: str, yf_interval: str, cache_label: str) -> None:
    spec = resolve_timeframe(key)
    assert spec.yf_interval == yf_interval
    assert spec.cache_label == cache_label


def test_resolve_timeframe_rejects_unknown_key() -> None:
    with pytest.raises(ValueError, match="Unknown timeframe"):
        resolve_timeframe("hourly")
