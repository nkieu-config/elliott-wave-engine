from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import timedelta

from engine.data.cache import BarCache, CacheKey
from engine.data.source import BarSource
from engine.data.timeframe import DEFAULT_TIMEFRAME, resolve_timeframe
from engine.types import Bar

__all__ = ["DEFAULT_TTL", "BarRepository"]

logger = logging.getLogger("engine.data.repository")

# Per-timeframe freshness budget; absent timeframe = no expiry. Each budget stays
# below one bar period so a freshly-closed (or still-forming) bar refreshes promptly
# rather than being served stale — the whole point of the live count.
DEFAULT_TTL: dict[str, timedelta] = {
    "day": timedelta(hours=12),
    "week": timedelta(days=1),
    "month": timedelta(days=3),
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

        bars: Sequence[Bar] | None = None
        if read_cache:
            bars = self.cache.load(key, max_age=self.ttl_policy.get(timeframe))

        if bars is None:
            logger.info(
                "fetch_bars: downloading %s (timeframe=%s, period=%s)",
                symbol,
                timeframe,
                period,
            )
            bars = self.source.download(symbol, period=period, interval=spec.yf_interval)
            if write_cache:
                try:
                    self.cache.store(key, bars)
                except Exception:
                    # Cache write is best-effort: a full/read-only volume must not fail
                    # a request that already holds valid downloaded data.
                    logger.warning("fetch_bars: cache store failed for %s", symbol, exc_info=True)

        return list(bars)

    def clear_cache(self, symbol: str | None = None) -> int:
        return self.cache.clear(symbol)
