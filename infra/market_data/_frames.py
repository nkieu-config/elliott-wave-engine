from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from engine.types import Bar

__all__ = ["bars_to_frame", "frame_to_bars"]

_OHLCV = ["Open", "High", "Low", "Close", "Volume"]


def frame_to_bars(df: pd.DataFrame) -> list[Bar]:
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


def bars_to_frame(bars: Sequence[Bar]) -> pd.DataFrame:
    # Mirrors the yfinance frame layout so parquet written here stays readable by
    # frame_to_bars — including entries written before bars became the port type.
    index = pd.DatetimeIndex([b.time for b in bars], name="Date")
    return pd.DataFrame(
        {
            "Open": [b.open for b in bars],
            "High": [b.high for b in bars],
            "Low": [b.low for b in bars],
            "Close": [b.close for b in bars],
            "Volume": [b.volume for b in bars],
        },
        index=index,
        columns=_OHLCV,
    )
