from __future__ import annotations

import logging
from datetime import timedelta

import pandas as pd

from engine.data.cache import BarCache, CacheKey
from engine.data.source import BarSource
from engine.data.timeframe import DEFAULT_TIMEFRAME, resolve_timeframe
from engine.types import Bar

__all__ = ["DEFAULT_TTL", "BarRepository"]

logger = logging.getLogger("engine.data.repository")

# Per-timeframe freshness budget; absent timeframe = no expiry.
DEFAULT_TTL: dict[str, timedelta] = {
    "day": timedelta(hours=12),
    "week": timedelta(days=30),
    "month": timedelta(days=1),
}


class BarRepository:
    def __init__(
        self,
        source: BarSource,
        cache: BarCache,
        ttl_policy: dict[str, timedelta] | None = None,
    ) -> None:
        self.source = source
        self.cache = cache
        # ttl_policy={} = disable staleness; only None ⇒ default.
        self.ttl_policy = DEFAULT_TTL if ttl_policy is None else ttl_policy

    def fetch_bars(
        self,
        symbol: str,
        timeframe: str = DEFAULT_TIMEFRAME,
        period: str = "10y",
        *,
        read_cache: bool = True,
        write_cache: bool = True,
    ) -> list[Bar]:
        # read_cache/write_cache independent: read=False forces fresh download,
        # write=False leaves cache untouched (a single flag would couple them).
        spec = resolve_timeframe(timeframe)
        key = CacheKey(symbol=symbol, cache_label=spec.cache_label, period=period)

        df: pd.DataFrame | None = None
        if read_cache:
            df = self.cache.load(key, max_age=self.ttl_policy.get(timeframe))

        if df is None:
            logger.info(
                "fetch_bars: downloading %s (timeframe=%s, period=%s)",
                symbol,
                timeframe,
                period,
            )
            df = self.source.download(symbol, period=period, interval=spec.yf_interval)
            if write_cache:
                self.cache.store(key, df)

        return _to_bars(df)

    def clear_cache(self, symbol: str | None = None) -> int:
        return self.cache.clear(symbol)


def _to_bars(df: pd.DataFrame) -> list[Bar]:
    # Drop NaN-OHLC rows (yfinance partial/halted bars): nan silently kills
    # every ZigZag comparison in that region.
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    # itertuples ~5-10x faster than iterrows.
    bars: list[Bar] = []
    for row in df.itertuples(index=True):
        ts = row.Index
        py_ts = ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts
        raw_volume = getattr(row, "Volume", 0.0)
        volume = float(raw_volume) if pd.notna(raw_volume) else 0.0
        bars.append(
            Bar(
                time=py_ts,
                open=float(row.Open),
                high=float(row.High),
                low=float(row.Low),
                close=float(row.Close),
                volume=volume,
            )
        )
    return bars
