from __future__ import annotations

import datetime as dt
import os
import time
from datetime import timedelta
from pathlib import Path

import pandas as pd

from engine.data.cache import CacheKey
from engine.types import Bar
from infra.market_data.parquet_cache import (
    CACHE_SCHEMA_VERSION,
    ParquetCache,
)


def _fname(safe_symbol: str, label: str, period: str) -> str:
    return f"{safe_symbol}_{label}_{period}_v{CACHE_SCHEMA_VERSION}.parquet"


def _sample_bars(volume: tuple[float, float] = (1000.0, 2000.0)) -> list[Bar]:
    return [
        Bar(time=dt.datetime(2026, 1, 5), open=10.0, high=12.0, low=9.0,
            close=11.0, volume=volume[0]),
        Bar(time=dt.datetime(2026, 1, 12), open=11.0, high=13.0, low=10.5,
            close=12.5, volume=volume[1]),
    ]


def test_load_returns_none_when_absent(tmp_path: Path) -> None:
    cache = ParquetCache(tmp_path)
    assert cache.load(CacheKey("AAPL", "weekly", "max")) is None


def test_store_then_load_roundtrips_bars(tmp_path: Path) -> None:
    cache = ParquetCache(tmp_path)
    key = CacheKey("AAPL", "weekly", "max")
    original = _sample_bars()

    cache.store(key, original)
    loaded = cache.load(key)

    assert loaded == original


def test_store_uses_unique_temp_per_call_then_atomic_rename(
    tmp_path: Path, monkeypatch
) -> None:
    # Regression: a FIXED temp name let two racing writers corrupt one file; each
    # store must write a distinct temp then atomically rename, leaving no leak.
    cache = ParquetCache(tmp_path)
    key = CacheKey("AAPL", "weekly", "max")
    bars = _sample_bars()

    temps: list[str] = []
    real_to_parquet = pd.DataFrame.to_parquet

    def spy(self, path, *a, **k):
        temps.append(str(path))
        return real_to_parquet(self, path, *a, **k)

    monkeypatch.setattr(pd.DataFrame, "to_parquet", spy)

    cache.store(key, bars)
    cache.store(key, bars)

    assert len(set(temps)) == 2, "each store must use a unique temp name"
    assert all(t.endswith(".tmp") for t in temps)
    assert cache.load(key) == bars
    assert list(tmp_path.glob("*.tmp")) == []


def test_store_creates_missing_nested_directory(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b" / "cache"
    cache = ParquetCache(nested)
    cache.store(CacheKey("AAPL", "weekly", "max"), _sample_bars())
    assert cache.load(CacheKey("AAPL", "weekly", "max")) is not None


def test_store_leaves_no_temporary_file_behind(tmp_path: Path) -> None:
    cache = ParquetCache(tmp_path)
    cache.store(CacheKey("AAPL", "weekly", "max"), _sample_bars())
    assert [p.name for p in tmp_path.iterdir()] == [_fname("AAPL", "weekly", "max")]


def test_count_reflects_number_of_stored_datasets(tmp_path: Path) -> None:
    cache = ParquetCache(tmp_path)
    assert cache.count() == 0
    cache.store(CacheKey("AAPL", "weekly", "max"), _sample_bars())
    cache.store(CacheKey("TSLA", "daily", "5y"), _sample_bars())
    assert cache.count() == 2


def test_clear_with_symbol_removes_only_that_symbols_files(tmp_path: Path) -> None:
    cache = ParquetCache(tmp_path)
    cache.store(CacheKey("AAPL", "weekly", "max"), _sample_bars())
    cache.store(CacheKey("AAPL", "daily", "5y"), _sample_bars())
    cache.store(CacheKey("TSLA", "weekly", "max"), _sample_bars())

    removed = cache.clear("AAPL")

    assert removed == 2
    assert cache.count() == 1
    assert cache.load(CacheKey("TSLA", "weekly", "max")) is not None


def test_clear_without_symbol_removes_everything(tmp_path: Path) -> None:
    cache = ParquetCache(tmp_path)
    cache.store(CacheKey("AAPL", "weekly", "max"), _sample_bars())
    cache.store(CacheKey("TSLA", "daily", "5y"), _sample_bars())

    removed = cache.clear()

    assert removed == 2
    assert cache.count() == 0


def test_clear_with_glob_metachar_symbol_does_not_wipe_cache(tmp_path: Path) -> None:
    # A symbol carrying a glob wildcard must match only itself — clear("*") must not
    # delete every entry.
    cache = ParquetCache(tmp_path)
    cache.store(CacheKey("AAPL", "weekly", "max"), _sample_bars())
    cache.store(CacheKey("TSLA", "weekly", "max"), _sample_bars())

    assert cache.clear("*") == 0
    assert cache.count() == 2


def test_clear_on_missing_directory_returns_zero(tmp_path: Path) -> None:
    cache = ParquetCache(tmp_path / "never-created")
    assert cache.clear() == 0


def test_slashed_symbol_is_filesystem_safe(tmp_path: Path) -> None:
    cache = ParquetCache(tmp_path)
    key = CacheKey("BTC/USD", "weekly", "max")

    cache.store(key, _sample_bars())

    assert (tmp_path / _fname("BTC%2FUSD", "weekly", "max")).exists()
    assert cache.load(key) is not None
    assert cache.clear("BTC/USD") == 1


def test_slashed_and_underscored_symbols_do_not_collide(tmp_path: Path) -> None:
    cache = ParquetCache(tmp_path)
    key_slash = CacheKey("BTC/USD", "weekly", "max")
    key_under = CacheKey("BTC_USD", "weekly", "max")

    bars_slash = _sample_bars(volume=(1.0, 2.0))
    bars_under = _sample_bars(volume=(3.0, 4.0))

    cache.store(key_slash, bars_slash)
    cache.store(key_under, bars_under)

    files = sorted(p.name for p in tmp_path.iterdir())
    assert len(files) == 2
    assert cache.load(key_slash) == bars_slash
    assert cache.load(key_under) == bars_under
    assert cache.clear("BTC/USD") == 1
    assert cache.load(key_slash) is None
    assert cache.load(key_under) is not None


def _backdate(path: Path, age: timedelta) -> None:
    past = time.time() - age.total_seconds()
    os.utime(path, (past, past))


def test_load_without_max_age_returns_entry_of_any_age(tmp_path: Path) -> None:
    cache = ParquetCache(tmp_path)
    key = CacheKey("AAPL", "weekly", "max")
    cache.store(key, _sample_bars())
    _backdate(tmp_path / _fname("AAPL", "weekly", "max"), timedelta(days=999))

    assert cache.load(key) is not None


def test_load_returns_entry_still_within_max_age(tmp_path: Path) -> None:
    cache = ParquetCache(tmp_path)
    key = CacheKey("AAPL", "weekly", "max")
    cache.store(key, _sample_bars())

    assert cache.load(key, max_age=timedelta(days=1)) is not None


def test_load_treats_entry_older_than_max_age_as_a_miss(tmp_path: Path) -> None:
    cache = ParquetCache(tmp_path)
    key = CacheKey("AAPL", "weekly", "max")
    cache.store(key, _sample_bars())
    _backdate(tmp_path / _fname("AAPL", "weekly", "max"), timedelta(days=2))

    assert cache.load(key, max_age=timedelta(days=1)) is None


def test_store_evicts_oldest_when_over_byte_budget(tmp_path: Path) -> None:
    # max_bytes=1 (< one parquet) ⇒ each store keeps only the just-written entry.
    cache = ParquetCache(tmp_path, max_bytes=1)
    cache.store(CacheKey("AAA", "weekly", "max"), _sample_bars())
    cache.store(CacheKey("BBB", "weekly", "max"), _sample_bars())

    assert cache.load(CacheKey("BBB", "weekly", "max")) is not None  # protected
    assert cache.load(CacheKey("AAA", "weekly", "max")) is None  # evicted
    assert cache.count() == 1


def test_store_protects_just_written_entry_even_if_alone_over_budget(
    tmp_path: Path,
) -> None:
    # A lone over-budget entry must NOT be evicted, else the caller's immediate
    # load() misses what it just wrote.
    cache = ParquetCache(tmp_path, max_bytes=1)
    cache.store(CacheKey("AAA", "weekly", "max"), _sample_bars())

    assert cache.load(CacheKey("AAA", "weekly", "max")) is not None
    assert cache.count() == 1


def test_max_bytes_zero_disables_eviction(tmp_path: Path) -> None:
    cache = ParquetCache(tmp_path, max_bytes=0)
    for sym in ("AAA", "BBB", "CCC"):
        cache.store(CacheKey(sym, "weekly", "max"), _sample_bars())
    assert cache.count() == 3


def test_filename_includes_schema_version(tmp_path: Path) -> None:
    cache = ParquetCache(tmp_path)
    cache.store(CacheKey("AAPL", "weekly", "max"), _sample_bars())
    assert (tmp_path / _fname("AAPL", "weekly", "max")).exists()


def test_file_from_older_schema_version_is_a_miss(tmp_path: Path) -> None:
    # Prior-schema file (different _vN) must not be read back; stale columns.
    cache = ParquetCache(tmp_path)
    stale = tmp_path / f"AAPL_weekly_max_v{CACHE_SCHEMA_VERSION - 1}.parquet"
    pd.DataFrame(
        {"Open": [10.0], "High": [12.0], "Low": [9.0], "Close": [11.0], "Volume": [1000]},
        index=pd.to_datetime(["2026-01-05"]),
    ).to_parquet(stale)

    assert cache.load(CacheKey("AAPL", "weekly", "max")) is None


def test_entry_written_as_a_yfinance_frame_still_loads(tmp_path: Path) -> None:
    # Pre-refactor entries hold the raw yfinance frame, not a bars round-trip.
    # The on-disk schema is unchanged, so v1 files stay readable.
    cache = ParquetCache(tmp_path)
    key = CacheKey("AAPL", "weekly", "max")
    legacy = pd.DataFrame(
        {
            "Open": [10.0, 11.0], "High": [12.0, 13.0], "Low": [9.0, 10.5],
            "Close": [11.0, 12.5], "Volume": [1000, 2000],
        },
        index=pd.to_datetime(["2026-01-05", "2026-01-12"]),
    )
    tmp_path.mkdir(parents=True, exist_ok=True)
    legacy.to_parquet(tmp_path / _fname("AAPL", "weekly", "max"))

    assert cache.load(key) == _sample_bars()
