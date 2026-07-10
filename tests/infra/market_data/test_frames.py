from __future__ import annotations

import datetime as dt

import pandas as pd

from engine.types import Bar
from infra.market_data._frames import bars_to_frame, frame_to_bars


def _frame(volume: list | None = None) -> pd.DataFrame:
    idx = pd.to_datetime(["2026-01-05", "2026-01-12"])
    data = {"Open": [10.0, 11.0], "High": [12.0, 13.0],
            "Low": [9.0, 10.5], "Close": [11.0, 12.5]}
    if volume is not None:
        data["Volume"] = volume
    return pd.DataFrame(data, index=idx)


def test_frame_to_bars_maps_every_field() -> None:
    bars = frame_to_bars(_frame(volume=[1000, 2000]))

    first = bars[0]
    assert first.time == dt.datetime(2026, 1, 5)
    assert (first.open, first.high, first.low, first.close) == (10.0, 12.0, 9.0, 11.0)
    assert first.volume == 1000.0


def test_missing_volume_column_defaults_to_zero() -> None:
    bars = frame_to_bars(_frame(volume=None))
    assert [b.volume for b in bars] == [0.0, 0.0]


def test_nan_volume_becomes_zero() -> None:
    bars = frame_to_bars(_frame(volume=[float("nan"), 5]))
    assert [b.volume for b in bars] == [0.0, 5.0]


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
    bars = frame_to_bars(df)
    assert [b.close for b in bars] == [11.0, 13.0]


def test_bars_to_frame_roundtrips_through_frame_to_bars() -> None:
    bars = [
        Bar(time=dt.datetime(2026, 1, 5), open=10.0, high=12.0, low=9.0,
            close=11.0, volume=1000.0),
        Bar(time=dt.datetime(2026, 1, 12), open=11.0, high=13.0, low=10.5,
            close=12.5, volume=2000.0),
    ]
    assert frame_to_bars(bars_to_frame(bars)) == bars


def test_bars_to_frame_emits_the_yfinance_column_layout() -> None:
    bars = [
        Bar(time=dt.datetime(2026, 1, 5), open=10.0, high=12.0, low=9.0,
            close=11.0, volume=1000.0),
    ]
    df = bars_to_frame(bars)
    assert list(df.columns) == ["Open", "High", "Low", "Close", "Volume"]


def test_bars_to_frame_handles_an_empty_sequence() -> None:
    assert bars_to_frame([]).empty
