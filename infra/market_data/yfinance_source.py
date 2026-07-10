from __future__ import annotations

import logging
import time

import pandas as pd
import yfinance as yf

from engine.types import Bar
from infra.market_data._frames import frame_to_bars

__all__ = ["YFinanceSource"]

logger = logging.getLogger("infra.market_data.yfinance_source")

# yfinance is flaky; exponential backoff (0.5/1/2s) covers typical recovery.
_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_BACKOFF_BASE_S = 0.5


class YFinanceSource:
    def __init__(
        self,
        max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
        backoff_base_s: float = _DEFAULT_BACKOFF_BASE_S,
    ) -> None:
        self.max_attempts = max_attempts
        self.backoff_base_s = backoff_base_s

    def download(self, symbol: str, *, period: str, interval: str) -> list[Bar]:
        # yfinance swallows transient failures (rate-limit, network) into an empty
        # frame, so an empty result is retried too — not assumed to be a bad symbol.
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
                reason: str = str(e)
            else:
                if df is not None and not df.empty:
                    return frame_to_bars(_normalise(df))
                last_exc = None
                reason = "empty result"

            if attempt < self.max_attempts - 1:  # no backoff after the last try
                wait = self.backoff_base_s * (2**attempt)
                logger.warning(
                    "download attempt %d/%d for %s @ %s failed (%s) — retry in %.1fs",
                    attempt + 1,
                    self.max_attempts,
                    symbol,
                    interval,
                    reason,
                    wait,
                )
                time.sleep(wait)

        if last_exc is not None:
            raise RuntimeError(
                f"download: exhausted {self.max_attempts} attempts for symbol={symbol!r} "
                f"period={period!r} interval={interval!r}"
            ) from last_exc
        raise ValueError(
            f"No data for symbol={symbol!r} period={period!r} interval={interval!r} "
            f"after {self.max_attempts} attempts"
        )


def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    # Single-symbol yf returns (field, ticker) tuples; flatten to field.
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df
