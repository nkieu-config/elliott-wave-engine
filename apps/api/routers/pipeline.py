"""Pipeline + deterministic Layer-1 analyst routes (no LLM)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from apps.api import pipeline_ops
from apps.api.schemas import Layer1Request, PipelineRequest
from apps.api.schemas_responses import (
    EducationResponse,
    Layer1Response,
    PipelineResponse,
)
from apps.api.serializers import serialize_analysis_result, serialize_pipeline
from apps.api.services import analyst_service

router = APIRouter(prefix="/api/v1", tags=["pipeline"])
_log = logging.getLogger(__name__)


# Handlers return plain serializer dicts; response_model validates that output.
@router.post("/pipeline", response_model=PipelineResponse)
def pipeline(req: PipelineRequest) -> dict[str, Any]:
    _log.info(
        "pipeline req: %s %s %s atr=%d/%.2f/%.2f minbars=%d",
        req.symbol,
        req.period,
        req.timeframe,
        req.atr_period,
        req.atr_multiplier,
        req.atr_floor,
        req.min_bars_between,
    )
    bars = pipeline_ops.fetch_bars_or_502(req)
    result = pipeline_ops.execute_pipeline(req, bars)

    meta = {
        "symbol": req.symbol,
        "period": req.period,
        "timeframe": req.timeframe,
        "generated_at": datetime.now(UTC).isoformat(),
        "config": req.model_dump(exclude={"symbol", "period", "timeframe"}),
    }

    # Eagerly compute top-scenario Layer-1 so the client hydrates without a second
    # roundtrip. Best-effort: failure is logged but doesn't block the response.
    top_layer1 = analyst_service.compute_top_layer1(
        result.report, list(bars), scale_mode=req.scale_mode
    )
    top_layer1_payload = serialize_analysis_result(top_layer1) if top_layer1 else None

    return serialize_pipeline(
        result,
        meta=meta,
        top_scenario_layer1=top_layer1_payload,
    )


@router.post("/scenario/layer1", response_model=Layer1Response)
def scenario_layer1(req: Layer1Request) -> dict[str, Any]:
    bars = pipeline_ops.fetch_bars_or_502(req)
    result = pipeline_ops.execute_pipeline(req, bars)
    scenarios, scenario = pipeline_ops.resolve_scenario(result, req.scenario_id)

    try:
        layer1 = analyst_service.compute_layer1(
            scenario,
            list(bars),
            all_scenarios=scenarios,
            scale_mode=req.scale_mode,
        )
    except Exception as e:
        # Don't echo internal exception text to LAN clients.
        _log.exception("compute_layer1 failed for scenario %s", scenario.id)
        raise HTTPException(status_code=500, detail="Layer-1 computation failed") from e

    return serialize_analysis_result(layer1)


@router.get("/scenario/education", response_model=EducationResponse)
def scenario_education(
    family: str = Query(min_length=1, max_length=32, pattern=r"^[A-Z0-9_]+$"),
) -> dict[str, Any]:
    """Static (no LLM) education entry for a wave family."""
    edu = analyst_service.family_education(family)
    if edu is None:
        raise HTTPException(
            status_code=404,
            detail=f"No education entry for family {family!r}",
        )
    return {
        "family": family,
        "title": edu.title,
        "one_line": edu.one_line,
        "rules": list(edu.rules),
        "visual_cues": list(edu.visual_cues),
    }
