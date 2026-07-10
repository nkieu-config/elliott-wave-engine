"""Shared request→pipeline helpers, and the composition root for the bar
repository. Routers call these via the module so a single monkeypatch point
covers every route in tests."""

from __future__ import annotations

import functools
import logging
import os
from collections.abc import Iterable
from pathlib import Path

from fastapi import HTTPException

from apps.api.schemas import PipelineRequest
from engine import (
    Bar,
    BarRepository,
    PipelineResult,
    Scenario,
    ScoringConfig,
    run_pipeline,
)
from infra.market_data import DEFAULT_CACHE_MAX_BYTES, ParquetCache, YFinanceSource

_log = logging.getLogger(__name__)

# <repo>/data for dev; EWL_CACHE_DIR overrides for installed deployments.
_DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[2] / "data"


def cache_dir() -> Path:
    return Path(os.environ.get("EWL_CACHE_DIR", _DEFAULT_CACHE_DIR))


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


@functools.lru_cache(maxsize=1)
def bar_repository() -> BarRepository:
    return BarRepository(
        source=YFinanceSource(),
        cache=ParquetCache(cache_dir(), max_bytes=_cache_max_bytes()),
    )


def fetch_bars(
    symbol: str,
    timeframe: str,
    period: str,
) -> list[Bar]:
    return bar_repository().fetch_bars(symbol, timeframe=timeframe, period=period)


def disable_force_refresh() -> bool:
    # Cost guard: prevents bypassing the cache for unbounded fresh LLM calls.
    # Unset → dev default (force_refresh honoured).
    return os.environ.get("EWL_DISABLE_FORCE_REFRESH", "").lower() in (
        "1",
        "true",
        "yes",
    )


def effective_force_refresh(requested: bool) -> bool:
    return requested and not disable_force_refresh()


def _headline(s: Scenario) -> float:
    # Rank by the displayed headline so the top scenario's tier matches its rank.
    return float((s.score_components or {}).get("total", s.score))


def top_scenario(scenarios: Iterable[Scenario]) -> Scenario | None:
    ranked = list(scenarios)
    return max(ranked, key=_headline) if ranked else None


def build_scoring_config(req: PipelineRequest) -> ScoringConfig:
    return ScoringConfig(
        k_sigma=req.k_sigma,
        log_tol_fib=req.log_tol_fib,
        pull_depth_lo=req.pull_depth_lo,
        pull_depth_hi=req.pull_depth_hi,
        pull_depth_tol=req.pull_depth_tol,
        pivot_window=req.pivot_window,
        commitment_curve=req.commitment_curve,
    )


def fetch_bars_or_502(req: PipelineRequest) -> tuple[Bar, ...]:
    """Maps any fetch failure to a 502 (upstream data error)."""
    try:
        return tuple(fetch_bars(req.symbol, timeframe=req.timeframe, period=req.period))
    except Exception as e:
        # Don't echo upstream exception text to clients (it can carry internal paths).
        _log.exception("fetch_bars failed for %s", req.symbol)
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch price data for {req.symbol!r}",
        ) from e


def execute_pipeline(req: PipelineRequest, bars: tuple[Bar, ...]) -> PipelineResult:
    # Redact engine failures to a 500 at every call site (mirrors fetch_bars_or_502),
    # so a compute crash never leaks internals nor falls to FastAPI's generic handler.
    try:
        return run_pipeline(
            bars=bars,
            scale_mode=req.scale_mode,
            atr_period=req.atr_period,
            atr_multiplier=req.atr_multiplier,
            atr_floor=req.atr_floor,
            min_bars_between=req.min_bars_between,
            scoring_config=build_scoring_config(req),
        )
    except Exception as e:
        _log.exception("run_pipeline failed for %s", req.symbol)
        raise HTTPException(
            status_code=500, detail="Pipeline computation failed"
        ) from e


def resolve_scenario(
    result: PipelineResult, scenario_id: str
) -> tuple[list[Scenario], Scenario]:
    """Return (all scenarios, the one matching `scenario_id`), or raise 404."""
    if result.report is None or not result.report.scenarios:
        raise HTTPException(
            status_code=404,
            detail="Pipeline produced no scenarios for this config",
        )
    scenarios = list(result.report.scenarios)
    scenario = next((s for s in scenarios if s.id == scenario_id), None)
    if scenario is None:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario id {scenario_id!r} not found in pipeline output",
        )
    return scenarios, scenario
