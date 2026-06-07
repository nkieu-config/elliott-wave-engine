from __future__ import annotations

import datetime as dt
from datetime import timedelta

import pandas as pd
import pytest

from engine.data.cache import CacheKey
from engine.data.repository import BarRepository, _to_bars


def _frame(volume: list | None = None) -> pd.DataFrame:
    idx = pd.to_datetime(["2026-01-05", "2026-01-12"])
    data = {"Open": [10.0, 11.0], "High": [12.0, 13.0],
            "Low": [9.0, 10.5], "Close": [11.0, 12.5]}
    if volume is not None:
        data["Volume"] = volume
    return pd.DataFrame(data, index=idx)


class _FakeSource:
    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame
        self.calls: list[tuple[str, str, str]] = []

    def download(self, symbol: str, *, period: str, interval: str) -> pd.DataFrame:
        self.calls.append((symbol, period, interval))
        return self.frame


class _FakeCache:
    def __init__(self, preload: dict[CacheKey, pd.DataFrame] | None = None) -> None:
        self.store_data: dict[CacheKey, pd.DataFrame] = dict(preload or {})
        self.loads: list[tuple[CacheKey, timedelta | None]] = []
        self.stores: list[CacheKey] = []

    def load(
        self, key: CacheKey, max_age: timedelta | None = None
    ) -> pd.DataFrame | None:
        self.loads.append((key, max_age))
        return self.store_data.get(key)

    def store(self, key: CacheKey, df: pd.DataFrame) -> None:
        self.stores.append(key)
        self.store_data[key] = df

    def clear(self, symbol: str | None = None) -> int:
        before = len(self.store_data)
        self.store_data = {
            k: v for k, v in self.store_data.items()
            if symbol is not None and k.symbol != symbol
        }
        return before - len(self.store_data)

    def count(self) -> int:
        return len(self.store_data)


def test_cache_hit_skips_the_source() -> None:
    key = CacheKey("AAPL", "weekly", "max")
    cache = _FakeCache(preload={key: _frame(volume=[1000, 2000])})
    source = _FakeSource(_frame(volume=[0, 0]))
    repo = BarRepository(source=source, cache=cache)

    bars = repo.fetch_bars("AAPL", timeframe="week", period="max")

    assert source.calls == []
    # Volume is the only field differing cache(1000/2000) vs source(0/0).
    assert [b.volume for b in bars] == [1000.0, 2000.0]


def test_cache_miss_downloads_and_stores() -> None:
    cache = _FakeCache()
    source = _FakeSource(_frame(volume=[1000, 2000]))
    repo = BarRepository(source=source, cache=cache)

    bars = repo.fetch_bars("AAPL", timeframe="week", period="max")

    assert source.calls == [("AAPL", "max", "1wk")]
    assert cache.stores == [CacheKey("AAPL", "weekly", "max")]
    assert len(bars) == 2


def test_read_cache_false_skips_read_but_still_stores() -> None:
    key = CacheKey("AAPL", "weekly", "max")
    cache = _FakeCache(preload={key: _frame(volume=[9, 9])})
    source = _FakeSource(_frame(volume=[1000, 2000]))
    repo = BarRepository(source=source, cache=cache)

    bars = repo.fetch_bars("AAPL", timeframe="week", period="max", read_cache=False)

    assert cache.loads == []
    assert source.calls == [("AAPL", "max", "1wk")]
    assert cache.stores == [key]
    assert [b.volume for b in bars] == [1000.0, 2000.0]


def test_write_cache_false_downloads_without_storing() -> None:
    cache = _FakeCache(preload={})
    source = _FakeSource(_frame(volume=[1000, 2000]))
    repo = BarRepository(source=source, cache=cache)

    bars = repo.fetch_bars("AAPL", timeframe="week", period="max", write_cache=False)

    assert source.calls == [("AAPL", "max", "1wk")]
    assert cache.stores == []
    assert [b.volume for b in bars] == [1000.0, 2000.0]


def test_dataframe_is_converted_to_bars_with_correct_fields() -> None:
    cache = _FakeCache(preload={CacheKey("AAPL", "weekly", "max"): _frame(volume=[1000, 2000])})
    repo = BarRepository(source=_FakeSource(_frame()), cache=cache)

    bars = repo.fetch_bars("AAPL", timeframe="week", period="max")

    first = bars[0]
    assert first.time == dt.datetime(2026, 1, 5)
    assert (first.open, first.high, first.low, first.close) == (10.0, 12.0, 9.0, 11.0)
    assert first.volume == 1000.0


def test_missing_volume_column_defaults_to_zero() -> None:
    cache = _FakeCache(preload={CacheKey("AAPL", "weekly", "max"): _frame(volume=None)})
    repo = BarRepository(source=_FakeSource(_frame()), cache=cache)

    bars = repo.fetch_bars("AAPL", timeframe="week", period="max")

    assert [b.volume for b in bars] == [0.0, 0.0]


def test_nan_volume_becomes_zero() -> None:
    cache = _FakeCache(preload={CacheKey("AAPL", "weekly", "max"): _frame(volume=[float("nan"), 5])})
    repo = BarRepository(source=_FakeSource(_frame()), cache=cache)

    bars = repo.fetch_bars("AAPL", timeframe="week", period="max")

    assert [b.volume for b in bars] == [0.0, 5.0]


def test_unknown_timeframe_raises() -> None:
    repo = BarRepository(source=_FakeSource(_frame()), cache=_FakeCache())
    with pytest.raises(ValueError, match="Unknown timeframe"):
        repo.fetch_bars("AAPL", timeframe="hourly", period="max")


def test_clear_cache_delegates_to_cache() -> None:
    key = CacheKey("AAPL", "weekly", "max")
    cache = _FakeCache(preload={key: _frame()})
    repo = BarRepository(source=_FakeSource(_frame()), cache=cache)

    assert repo.clear_cache("AAPL") == 1
    assert cache.count() == 0


@pytest.mark.parametrize(
    ("timeframe", "expected_ttl"),
    [
        ("day", timedelta(hours=12)),
        ("week", timedelta(days=30)),
        ("month", timedelta(days=1)),
    ],
)
def test_fetch_bars_passes_per_timeframe_ttl_to_cache(
    timeframe: str, expected_ttl: timedelta
) -> None:
    cache = _FakeCache()
    repo = BarRepository(source=_FakeSource(_frame(volume=[1, 2])), cache=cache)

    repo.fetch_bars("AAPL", timeframe=timeframe, period="max")

    _key, max_age = cache.loads[0]
    assert max_age == expected_ttl


def test_custom_ttl_policy_overrides_the_default() -> None:
    cache = _FakeCache()
    repo = BarRepository(
        source=_FakeSource(_frame(volume=[1, 2])),
        cache=cache,
        ttl_policy={"week": timedelta(hours=6)},
    )

    repo.fetch_bars("AAPL", timeframe="week", period="max")

    _key, max_age = cache.loads[0]
    assert max_age == timedelta(hours=6)


def test_timeframe_absent_from_policy_disables_staleness() -> None:
    cache = _FakeCache()
    repo = BarRepository(
        source=_FakeSource(_frame(volume=[1, 2])),
        cache=cache,
        ttl_policy={},
    )

    repo.fetch_bars("AAPL", timeframe="week", period="max")

    _key, max_age = cache.loads[0]
    assert max_age is None


def test_to_bars_drops_nan_ohlc_rows() -> None:
    idx = pd.to_datetime(["2026-01-05", "2026-01-12", "2026-01-19"])
    df = pd.DataFrame(
        {
            "Open": [10.0, float("nan"), 12.0],
            "High": [12.0, 13.0, 14.0],
            "Low": [9.0, 10.5, 11.0],
            "Close": [11.0, 12.5, 13.0],
            "Volume": [1, 2, 3],
        },
        index=idx,
    )
    bars = _to_bars(df)
    assert [b.close for b in bars] == [11.0, 13.0]
