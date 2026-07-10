from __future__ import annotations

import pandas as pd
import pytest

from infra.market_data.yfinance_source import YFinanceSource


def _ok_frame() -> pd.DataFrame:
    idx = pd.to_datetime(["2026-01-05", "2026-01-12"])
    return pd.DataFrame(
        {"Open": [10.0, 11.0], "High": [12.0, 13.0], "Low": [9.0, 10.5],
         "Close": [11.0, 12.5], "Volume": [1000, 2000]},
        index=idx,
    )


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("infra.market_data.yfinance_source.time.sleep", lambda _s: None)


def test_download_returns_bars_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "infra.market_data.yfinance_source.yf.download", lambda *a, **k: _ok_frame()
    )
    bars = YFinanceSource().download("AAPL", period="max", interval="1wk")
    assert len(bars) == 2
    assert (bars[0].open, bars[0].high, bars[0].low, bars[0].close) == (10.0, 12.0, 9.0, 11.0)
    assert [b.volume for b in bars] == [1000.0, 2000.0]


def test_download_passes_expected_args_to_yfinance(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def spy_download(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return _ok_frame()

    monkeypatch.setattr("infra.market_data.yfinance_source.yf.download", spy_download)
    YFinanceSource().download("AAPL", period="max", interval="1wk")

    assert captured["args"] == ("AAPL",)
    assert captured["kwargs"] == {
        "period": "max",
        "interval": "1wk",
        "auto_adjust": True,
        "progress": False,
    }


def test_persistently_empty_result_is_retried_then_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    # yfinance returns an empty frame for BOTH bad symbols and swallowed transient
    # failures, so empties are retried; a persistently empty one still raises "No data".
    calls = []

    def fake_download(*a, **k):
        calls.append(1)
        return pd.DataFrame()

    monkeypatch.setattr("infra.market_data.yfinance_source.yf.download", fake_download)

    with pytest.raises(ValueError, match="No data"):
        YFinanceSource(max_attempts=3).download("BADSYM", period="max", interval="1wk")
    assert len(calls) == 3


def test_transient_empty_frame_is_retried_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    # A transient failure surfaces as an empty frame; a later attempt recovers.
    calls = []

    def flaky_download(*a, **k):
        calls.append(1)
        return _ok_frame() if len(calls) >= 3 else pd.DataFrame()

    monkeypatch.setattr("infra.market_data.yfinance_source.yf.download", flaky_download)

    bars = YFinanceSource(max_attempts=3).download("AAPL", period="max", interval="1wk")
    assert len(bars) == 2
    assert len(calls) == 3


def test_transient_error_is_retried_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def flaky_download(*a, **k):
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError("network blip")
        return _ok_frame()

    monkeypatch.setattr("infra.market_data.yfinance_source.yf.download", flaky_download)

    bars = YFinanceSource(max_attempts=3).download("AAPL", period="max", interval="1wk")
    assert len(bars) == 2
    assert len(calls) == 3


def test_exhausted_retries_raise_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def always_fails(*a, **k):
        raise ConnectionError("network down")

    monkeypatch.setattr("infra.market_data.yfinance_source.yf.download", always_fails)

    with pytest.raises(RuntimeError, match="exhausted"):
        YFinanceSource(max_attempts=3).download("AAPL", period="max", interval="1wk")


def test_no_backoff_sleep_after_the_final_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("infra.market_data.yfinance_source.time.sleep", sleeps.append)

    def always_fails(*a, **k):
        raise ConnectionError("network down")

    monkeypatch.setattr("infra.market_data.yfinance_source.yf.download", always_fails)
    with pytest.raises(RuntimeError, match="exhausted"):
        YFinanceSource(max_attempts=3).download("AAPL", period="max", interval="1wk")
    # backoff only BETWEEN attempts, never after the last.
    assert len(sleeps) == 2


def test_multiindex_columns_are_flattened(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = _ok_frame()
    frame.columns = pd.MultiIndex.from_tuples(
        [(c, "AAPL") for c in frame.columns]
    )
    monkeypatch.setattr("infra.market_data.yfinance_source.yf.download", lambda *a, **k: frame)

    bars = YFinanceSource().download("AAPL", period="max", interval="1wk")
    assert len(bars) == 2
    assert bars[0].close == 11.0
