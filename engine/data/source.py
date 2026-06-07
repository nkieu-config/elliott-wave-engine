from __future__ import annotations

import logging
import time
from typing import Protocol

import pandas as pd
import yfinance as yf

__all__ = ["BarSource", "YFinanceSource"]

logger = logging.getLogger("engine.data.source")

# yfinance is flaky; exponential backoff (0.5/1/2s) covers typical recovery.
_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_BACKOFF_BASE_S = 0.5


class BarSource(Protocol):
    def download(self, symbol: str, *, period: str, interval: str) -> pd.DataFrame:
        ...


class YFinanceSource:
    def __init__(
        self,
        max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
        backoff_base_s: float = _DEFAULT_BACKOFF_BASE_S,
    ) -> None:
        self.max_attempts = max_attempts
        self.backoff_base_s = backoff_base_s

    def download(self, symbol: str, *, period: str, interval: str) -> pd.DataFrame:
        # Empty result NOT retried — signals bad symbol/period, not transient failure.
        last_exc: Exception | None = None
        for attempt in range(self.max_attempts):
            try:
                df = yf.download(
                    symbol,
                    period=period,
                    interval=interval,
                    auto_adjust=True,
                    progress=False,
                )
            except Exception as e:
                last_exc = e
                wait = self.backoff_base_s * (2**attempt)
                logger.warning(
                    "download failed (attempt %d/%d) for %s @ %s: %s — retry in %.1fs",
                    attempt + 1,
                    self.max_attempts,
                    symbol,
                    interval,
                    e,
                    wait,
                )
                if attempt < self.max_attempts - 1:  # no backoff after the last try
                    time.sleep(wait)
                continue
            if df is None or df.empty:
                logger.warning(
                    "empty result for symbol=%r period=%r interval=%r",
                    symbol,
                    period,
                    interval,
                )
                raise ValueError(
                    f"No data for symbol={symbol!r} period={period!r} interval={interval!r}"
                )
            return _normalise(df)
        raise RuntimeError(
            f"download: exhausted {self.max_attempts} attempts for symbol={symbol!r} "
            f"period={period!r} interval={interval!r}"
        ) from last_exc


def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    # Single-symbol yf returns (field, ticker) tuples; flatten to field.
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df
