from __future__ import annotations

import glob
import logging
import os
import time
import uuid
from collections.abc import Sequence
from datetime import timedelta
from pathlib import Path

import pandas as pd

from engine.data.cache import CacheKey
from engine.types import Bar
from infra.market_data._frames import bars_to_frame, frame_to_bars

__all__ = [
    "CACHE_SCHEMA_VERSION",
    "DEFAULT_CACHE_MAX_BYTES",
    "ParquetCache",
]

logger = logging.getLogger("infra.market_data.parquet_cache")

# In-filename schema version. Bump on column/normalisation change so old entries
# miss (re-download) instead of reading stale; orphans age out via store() eviction.
CACHE_SCHEMA_VERSION = 1

# LRU budget. `symbol` is user-supplied, so without a cap the cache grows unbounded.
DEFAULT_CACHE_MAX_BYTES = 256 * 1024 * 1024


def _safe_symbol(symbol: str) -> str:
    # Pct-encode /, %, _ (plain .replace would collide BTC/USD with BTC_USD); % first.
    return (
        symbol.replace("%", "%25").replace("/", "%2F").replace("_", "%5F")
    )


class ParquetCache:
    # max_bytes=0 disables eviction (unbounded — used by tests that assert exact
    # dir contents).
    def __init__(self, directory: Path, max_bytes: int = DEFAULT_CACHE_MAX_BYTES) -> None:
        self.directory = Path(directory)
        self.max_bytes = max_bytes

    def _path(self, key: CacheKey) -> Path:
        name = (
            f"{_safe_symbol(key.symbol)}_{key.cache_label}_{key.period}"
            f"_v{CACHE_SCHEMA_VERSION}.parquet"
        )
        path = (self.directory / name).resolve()
        # period/cache_label interpolated unescaped — confine to cache dir so a
        # stray separator can't write/read elsewhere.
        if self.directory.resolve() not in path.parents:
            raise ValueError(f"unsafe cache path for symbol={key.symbol!r}")
        return path

    def load(self, key: CacheKey, max_age: timedelta | None = None) -> list[Bar] | None:
        path = self._path(key)
        if not path.exists():
            return None
        if max_age is not None:
            age_s = time.time() - path.stat().st_mtime
            if age_s > max_age.total_seconds():
                logger.debug(
                    "ParquetCache: stale %s (%.0fs old, budget %.0fs)",
                    path.name,
                    age_s,
                    max_age.total_seconds(),
                )
                return None
        try:
            df = pd.read_parquet(path)
        except Exception:
            # Corrupt entry: miss so the caller re-downloads and overwrites via store().
            logger.warning("ParquetCache: unreadable %s — treating as miss", path.name, exc_info=True)
            return None
        logger.debug("ParquetCache: hit %s", path.name)
        return frame_to_bars(df)

    def store(self, key: CacheKey, bars: Sequence[Bar]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self._path(key)
        # Unique tmp per writer so concurrent stores don't interleave bytes; rename
        # is atomic (same dir) — last writer wins, readers never see a half-written file.
        tmp = path.with_name(f"{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
        try:
            bars_to_frame(bars).to_parquet(tmp)
            tmp.replace(path)
        finally:
            # No-op on success; on failure cleans the partial temp.
            tmp.unlink(missing_ok=True)
        logger.debug("ParquetCache: stored %s", path.name)
        if self.max_bytes > 0:
            self._evict_if_over_budget(protect=path)

    def _evict_if_over_budget(self, *, protect: Path) -> None:
        # Evict oldest-fetched until under budget. mtime = fetch time (load() never
        # touches it → TTL intact), so LRU-by-age also retires stale-version orphans.
        # Never evict `protect` (just-written) or the following load() would miss.
        # stat once, and skip a file a concurrent write/clear unlinked mid-scan.
        entries = []
        for f in self.directory.glob("*.parquet"):
            try:
                st = f.stat()
            except OSError:
                continue
            # Resolve so the `path == protect` guard holds under a symlinked cache dir
            # (protect comes from _path(), which resolves); else the just-written file
            # can be evicted and the next load() misses.
            entries.append((st.st_mtime, st.st_size, f.resolve()))
        total = sum(size for _, size, _ in entries)
        if total <= self.max_bytes:
            return
        entries.sort(key=lambda t: t[0])
        for _mtime, size, path in entries:
            if total <= self.max_bytes:
                break
            if path == protect:
                continue
            try:
                path.unlink()
                total -= size
            except OSError:
                logger.debug("ParquetCache: could not evict %s", path.name)
                continue
        if total > self.max_bytes:
            logger.warning(
                "ParquetCache: still %d bytes after eviction (budget %d); "
                "protecting the just-written entry.",
                total,
                self.max_bytes,
            )

    def clear(self, symbol: str | None = None) -> int:
        if not self.directory.exists():
            return 0
        # glob.escape so a symbol carrying *, ? or [ can't widen the match — e.g.
        # clear("*") must not wipe the whole cache.
        pattern = f"{glob.escape(_safe_symbol(symbol))}_*.parquet" if symbol else "*.parquet"
        files = list(self.directory.glob(pattern))
        removed = 0
        for f in files:
            try:
                f.unlink(missing_ok=True)
            except OSError:
                # A concurrent clear()/store() may have moved the file; skip rather than fail.
                logger.debug("ParquetCache: could not unlink %s", f.name)
                continue
            removed += 1
        return removed

    def count(self) -> int:
        if not self.directory.exists():
            return 0
        return sum(1 for _ in self.directory.glob("*.parquet"))
