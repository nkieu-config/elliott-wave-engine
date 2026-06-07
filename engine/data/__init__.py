from __future__ import annotations

import os
from pathlib import Path

from engine.data.cache import (
    DEFAULT_CACHE_MAX_BYTES,
    BarCache,
    CacheKey,
    ParquetCache,
)
from engine.data.repository import BarRepository
from engine.data.source import BarSource, YFinanceSource
from engine.data.timeframe import (
    DEFAULT_TIMEFRAME,
    TIMEFRAMES,
    TimeframeSpec,
    resolve_timeframe,
)
from engine.types import Bar

__all__ = [
    "TimeframeSpec",
    "resolve_timeframe",
    "BarSource",
    "YFinanceSource",
    "BarCache",
    "CacheKey",
    "ParquetCache",
    "BarRepository",
    "TIMEFRAMES",
    "DEFAULT_TIMEFRAME",
    "CACHE_DIR",
    "fetch_bars",
    "clear_cache",
    "cached_dataset_count",
    "default_repository",
]

# <repo>/data for dev; EWL_CACHE_DIR overrides for installed deployments.
_DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CACHE_DIR = Path(os.environ.get("EWL_CACHE_DIR", _DEFAULT_CACHE_DIR))


def _cache_max_bytes() -> int:
    # EWL_CACHE_MAX_BYTES tunes the parquet LRU budget; 0 disables eviction. A
    # malformed value falls back to the default rather than crashing app boot.
    raw = os.environ.get("EWL_CACHE_MAX_BYTES")
    if raw is None:
        return DEFAULT_CACHE_MAX_BYTES
    try:
        return max(0, int(raw))
    except ValueError:
        return DEFAULT_CACHE_MAX_BYTES


_DEFAULT_REPOSITORY = BarRepository(
    source=YFinanceSource(),
    cache=ParquetCache(CACHE_DIR, max_bytes=_cache_max_bytes()),
)


def default_repository() -> BarRepository:
    return _DEFAULT_REPOSITORY


def fetch_bars(
    symbol: str,
    timeframe: str = DEFAULT_TIMEFRAME,
    period: str = "10y",
    *,
    read_cache: bool = True,
    write_cache: bool = True,
) -> list[Bar]:
    return _DEFAULT_REPOSITORY.fetch_bars(
        symbol,
        timeframe=timeframe,
        period=period,
        read_cache=read_cache,
        write_cache=write_cache,
    )


def clear_cache(symbol: str | None = None) -> int:
    return _DEFAULT_REPOSITORY.clear_cache(symbol)


def cached_dataset_count() -> int:
    return _DEFAULT_REPOSITORY.cache.count()
