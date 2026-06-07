"""Shared request→pipeline helpers. Routers call these via the module so a single
monkeypatch point covers every route in tests."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable

from fastapi import HTTPException

from apps.api.schemas import PipelineRequest
from engine import (
    Bar,
    PipelineResult,
    Scenario,
    ScoringConfig,
    fetch_bars,
    run_pipeline,
)

_log = logging.getLogger(__name__)


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
    return run_pipeline(
        bars=bars,
        scale_mode=req.scale_mode,
        atr_period=req.atr_period,
        atr_multiplier=req.atr_multiplier,
        atr_floor=req.atr_floor,
        min_bars_between=req.min_bars_between,
        scoring_config=build_scoring_config(req),
    )


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
