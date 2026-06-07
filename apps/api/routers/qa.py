"""Single-shot theory Q&A route (Layer-2, LLM + similarity retrieval). One blocking
call returning JSON — the answer is short, so SSE pacing buys nothing."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException

from apps.api import dependencies
from apps.api.schemas import QaCitation, QaRequest, QaResponse
from apps.api.services import analyst_service
from engine import Bar, Scenario

router = APIRouter(prefix="/api/v1", tags=["qa"])
_log = logging.getLogger(__name__)


@router.post("/qa", response_model=QaResponse)
async def qa(req: QaRequest) -> QaResponse:
    # Off the event loop: the 503 check, fetch+pipeline, and answer call all block.
    def _run() -> QaResponse:
        if not analyst_service.qa_available():
            raise HTTPException(
                status_code=503,
                detail="Q&A unavailable: embedder not loaded (set ANALYST_QA=1).",
            )
        scenario: Scenario | None = None
        bars: list[Bar] | None = None
        if req.scenario_id is not None:
            # Chart-aware: rebuild the scenario the user is looking at.
            fetched = dependencies.fetch_bars_or_502(req)
            result = dependencies.execute_pipeline(req, fetched)
            _scenarios, scenario = dependencies.resolve_scenario(
                result, req.scenario_id
            )
            bars = list(fetched)
        try:
            output = analyst_service.answer_question(
                req.question,
                scenario=scenario,
                bars=bars,
                scale_mode=req.scale_mode,
                force_refresh=dependencies.effective_force_refresh(req.force_refresh),
            )
        except HTTPException:
            raise
        except Exception as e:
            # Don't echo internal exception text to LAN clients.
            _log.exception("qa failed")
            raise HTTPException(status_code=500, detail="Q&A computation failed") from e
        return QaResponse(
            question=output.question,
            answer=output.answer,
            citations=[
                QaCitation(page=c.page, claim_sentence=c.claim_sentence)
                for c in output.citations
            ],
            retrieved_pages=list(output.retrieved_pages),
            out_of_scope=output.out_of_scope,
            fell_back=output.fell_back,
            cached=output.cached,
            model_id=output.model_id,
        )

    return await asyncio.to_thread(_run)
