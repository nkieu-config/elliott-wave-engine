"""Shared fixtures for the apps/api suite — real pipeline on cached DDOG weekly
bars (web default config); call sites are marked `slow`. Skip offline unless
EWL_REQUIRE_BARS=1 forces a hard fail.

`run_pipeline` memoizes in-process, so the fixture run and the TestClient's
`/api/v1/pipeline` call share one parse → identical deterministic scenario ids.

ISOLATION INVARIANT: these `scope="session"` fixtures must depend only on
unpatched primitives (a directly-built `BarRepository` / `run_pipeline`), never the
`pipeline_ops.*` seams that test_api.py swaps out with function-scoped
monkeypatch — else a session fixture holds real data while a later test sees the
stub → order-dependent failures. Keep new session fixtures engine-side, or scope
to `module`.
"""

from __future__ import annotations

import os

import pytest

from apps.api import pipeline_ops
from apps.api.schemas import PipelineRequest
from apps.api.serializers import serialize_analysis_result, serialize_pipeline
from apps.api.services import analyst_service
from engine.data import BarRepository
from engine.parser import ScoringConfig
from engine.pipeline import run_pipeline
from infra.market_data import ParquetCache, YFinanceSource

# Mirrors the Next.js CONFIG_DEFAULTS / the aligned API defaults.
API_CONFIG = {"symbol": "DDOG", "period": "max", "timeframe": "week", "scale_mode": "linear"}


def _missing_data(reason: str) -> None:
    """Skip when bars are absent; EWL_REQUIRE_BARS=1 turns it into a hard fail so
    a broken cache / pipeline regression can't hide behind a silent skip."""
    if os.environ.get("EWL_REQUIRE_BARS"):
        pytest.fail(f"EWL_REQUIRE_BARS set but {reason}")
    pytest.skip(reason)


@pytest.fixture(scope="session")
def bars():
    repository = BarRepository(
        source=YFinanceSource(),
        cache=ParquetCache(pipeline_ops.cache_dir()),
    )
    try:
        loaded = tuple(
            repository.fetch_bars(
                API_CONFIG["symbol"],
                timeframe=API_CONFIG["timeframe"],
                period=API_CONFIG["period"],
            )
        )
    # Only data/network absence skips; other exceptions are real bugs, propagate.
    except (FileNotFoundError, OSError, ConnectionError, ValueError) as exc:
        _missing_data(f"{API_CONFIG['symbol']} bars unavailable (no cache/network): {exc}")
    if not loaded:
        _missing_data("bars empty")
    return loaded


@pytest.fixture(scope="session")
def pipeline_result(bars):
    res = run_pipeline(
        bars=bars,
        scale_mode=API_CONFIG["scale_mode"],
        atr_period=14,
        atr_multiplier=3.0,
        atr_floor=0.10,
        min_bars_between=4,
        scoring_config=ScoringConfig(),
    )
    if res.report is None or not res.report.scenarios:
        _missing_data("pipeline produced no scenarios for the fixture config")
    return res


@pytest.fixture(scope="session")
def top_scenario(pipeline_result):
    return pipeline_ops.top_scenario(pipeline_result.report.scenarios)


@pytest.fixture(scope="session")
def payload(pipeline_result):
    # Build meta exactly as the /api/v1/pipeline route does, to match the contract.
    req = PipelineRequest(**API_CONFIG)
    meta = {
        "symbol": req.symbol,
        "period": req.period,
        "timeframe": req.timeframe,
        "generated_at": "1970-01-01T00:00:00+00:00",
        "config": req.model_dump(exclude={"symbol", "period", "timeframe"}),
    }
    return serialize_pipeline(pipeline_result, meta=meta).model_dump(mode="json")


@pytest.fixture(scope="session")
def layer1_payload(pipeline_result, top_scenario, bars):
    layer1 = analyst_service.compute_layer1(
        top_scenario,
        list(bars),
        all_scenarios=list(pipeline_result.report.scenarios),
        scale_mode=API_CONFIG["scale_mode"],
    )
    return serialize_analysis_result(layer1).model_dump(mode="json")
