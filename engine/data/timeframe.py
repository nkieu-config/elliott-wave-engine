from __future__ import annotations

from dataclasses import dataclass

__all__ = ["DEFAULT_TIMEFRAME", "TIMEFRAMES", "TimeframeSpec", "resolve_timeframe"]


@dataclass(frozen=True)
class TimeframeSpec:
    yf_interval: str
    cache_label: str


# cache_label decoupled from yf_interval (existing parquet files survive yf token changes).
# Insertion order = UI segmented-control order.
_TIMEFRAME_SPECS: dict[str, TimeframeSpec] = {
    "day": TimeframeSpec("1d", "daily"),
    "week": TimeframeSpec("1wk", "weekly"),
    "month": TimeframeSpec("1mo", "monthly"),
}

TIMEFRAMES: tuple[str, ...] = tuple(_TIMEFRAME_SPECS)

DEFAULT_TIMEFRAME: str = "week"


def resolve_timeframe(timeframe: str) -> TimeframeSpec:
    try:
        return _TIMEFRAME_SPECS[timeframe]
    except KeyError as e:
        valid = ", ".join(_TIMEFRAME_SPECS)
        raise ValueError(f"Unknown timeframe {timeframe!r}. Expected one of: {valid}") from e
