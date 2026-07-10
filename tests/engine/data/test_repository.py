from __future__ import annotations

import datetime as dt
from collections.abc import Sequence
from datetime import timedelta

import pytest

from engine.data.cache import CacheKey
from engine.data.repository import BarRepository
from engine.types import Bar


def _bars(volume: tuple[float, float] = (1000.0, 2000.0)) -> list[Bar]:
    return [
        Bar(time=dt.datetime(2026, 1, 5), open=10.0, high=12.0, low=9.0,
            close=11.0, volume=volume[0]),
        Bar(time=dt.datetime(2026, 1, 12), open=11.0, high=13.0, low=10.5,
            close=12.5, volume=volume[1]),
    ]


class _FakeSource:
    def __init__(self, bars: list[Bar]) -> None:
        self.bars = bars
        self.calls: list[tuple[str, str, str]] = []

    def download(self, symbol: str, *, period: str, interval: str) -> list[Bar]:
        self.calls.append((symbol, period, interval))
        return self.bars


class _FakeCache:
    def __init__(self, preload: dict[CacheKey, list[Bar]] | None = None) -> None:
        self.store_data: dict[CacheKey, list[Bar]] = dict(preload or {})
        self.loads: list[tuple[CacheKey, timedelta | None]] = []
        self.stores: list[CacheKey] = []

    def load(
        self, key: CacheKey, max_age: timedelta | None = None
    ) -> list[Bar] | None:
        self.loads.append((key, max_age))
        return self.store_data.get(key)

    def store(self, key: CacheKey, bars: Sequence[Bar]) -> None:
        self.stores.append(key)
        self.store_data[key] = list(bars)

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
    cache = _FakeCache(preload={key: _bars(volume=(1000.0, 2000.0))})
    source = _FakeSource(_bars(volume=(0.0, 0.0)))
    repo = BarRepository(source=source, cache=cache)

    bars = repo.fetch_bars("AAPL", timeframe="week", period="max")

    assert source.calls == []
    # Volume is the only field differing cache(1000/2000) vs source(0/0).
    assert [b.volume for b in bars] == [1000.0, 2000.0]


def test_cache_miss_downloads_and_stores() -> None:
    cache = _FakeCache()
    source = _FakeSource(_bars())
    repo = BarRepository(source=source, cache=cache)

    bars = repo.fetch_bars("AAPL", timeframe="week", period="max")

    assert source.calls == [("AAPL", "max", "1wk")]
    assert cache.stores == [CacheKey("AAPL", "weekly", "max")]
    assert len(bars) == 2


def test_read_cache_false_skips_read_but_still_stores() -> None:
    key = CacheKey("AAPL", "weekly", "max")
    cache = _FakeCache(preload={key: _bars(volume=(9.0, 9.0))})
    source = _FakeSource(_bars())
    repo = BarRepository(source=source, cache=cache)

    bars = repo.fetch_bars("AAPL", timeframe="week", period="max", read_cache=False)

    assert cache.loads == []
    assert source.calls == [("AAPL", "max", "1wk")]
    assert cache.stores == [key]
    assert [b.volume for b in bars] == [1000.0, 2000.0]


def test_write_cache_false_downloads_without_storing() -> None:
    cache = _FakeCache(preload={})
    source = _FakeSource(_bars())
    repo = BarRepository(source=source, cache=cache)

    bars = repo.fetch_bars("AAPL", timeframe="week", period="max", write_cache=False)

    assert source.calls == [("AAPL", "max", "1wk")]
    assert cache.stores == []
    assert [b.volume for b in bars] == [1000.0, 2000.0]


def test_cached_bars_are_returned_verbatim() -> None:
    cache = _FakeCache(preload={CacheKey("AAPL", "weekly", "max"): _bars()})
    repo = BarRepository(source=_FakeSource(_bars()), cache=cache)

    bars = repo.fetch_bars("AAPL", timeframe="week", period="max")

    first = bars[0]
    assert first.time == dt.datetime(2026, 1, 5)
    assert (first.open, first.high, first.low, first.close) == (10.0, 12.0, 9.0, 11.0)
    assert first.volume == 1000.0


def test_cache_store_failure_does_not_fail_the_fetch() -> None:
    # A full / read-only cache volume must not sink a request that already holds
    # freshly downloaded bars.
    class _FailingCache(_FakeCache):
        def store(self, key: CacheKey, bars: Sequence[Bar]) -> None:
            raise OSError("read-only volume")

    repo = BarRepository(source=_FakeSource(_bars()), cache=_FailingCache())

    bars = repo.fetch_bars("AAPL", timeframe="week", period="max")

    assert len(bars) == 2


def test_unknown_timeframe_raises() -> None:
    repo = BarRepository(source=_FakeSource(_bars()), cache=_FakeCache())
    with pytest.raises(ValueError, match="Unknown timeframe"):
        repo.fetch_bars("AAPL", timeframe="hourly", period="max")


def test_clear_cache_delegates_to_cache() -> None:
    key = CacheKey("AAPL", "weekly", "max")
    cache = _FakeCache(preload={key: _bars()})
    repo = BarRepository(source=_FakeSource(_bars()), cache=cache)

    assert repo.clear_cache("AAPL") == 1
    assert cache.count() == 0


@pytest.mark.parametrize(
    ("timeframe", "bar_period"),
    [
        ("day", timedelta(days=1)),
        ("week", timedelta(days=7)),
        ("month", timedelta(days=30)),
    ],
)
def test_fetch_bars_ttl_stays_below_one_bar_period(
    timeframe: str, bar_period: timedelta
) -> None:
    # Staleness budget must sit under one bar period so a freshly-closed (or the
    # still-forming) bar is refreshed, not served stale — guards the week/month swap.
    cache = _FakeCache()
    repo = BarRepository(source=_FakeSource(_bars()), cache=cache)

    repo.fetch_bars("AAPL", timeframe=timeframe, period="max")

    _key, max_age = cache.loads[0]
    assert max_age is not None
    assert timedelta(0) < max_age < bar_period


def test_custom_ttl_policy_overrides_the_default() -> None:
    cache = _FakeCache()
    repo = BarRepository(
        source=_FakeSource(_bars()),
        cache=cache,
        ttl_policy={"week": timedelta(hours=6)},
    )

    repo.fetch_bars("AAPL", timeframe="week", period="max")

    _key, max_age = cache.loads[0]
    assert max_age == timedelta(hours=6)


def test_timeframe_absent_from_policy_disables_staleness() -> None:
    cache = _FakeCache()
    repo = BarRepository(
        source=_FakeSource(_bars()),
        cache=cache,
        ttl_policy={},
    )

    repo.fetch_bars("AAPL", timeframe="week", period="max")

    _key, max_age = cache.loads[0]
    assert max_age is None


def test_repository_module_does_not_import_pandas() -> None:
    # The domain repository speaks Bars; pandas belongs to the infra adapters.
    import engine.data.repository as repo_module

    assert not hasattr(repo_module, "pd")
