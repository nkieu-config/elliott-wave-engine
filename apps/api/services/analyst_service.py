"""Service seam over the `analyst` package. Every analyst import is deferred into a
function body so importing this module at app startup stays light (numpy + embeddings)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from apps.api import dependencies

if TYPE_CHECKING:
    from analyst import AnalysisOutput, AnalysisResult, Analyst
    from analyst.diagnostics.education import FamilyEducation
    from analyst.schemas.qa import QaOutput
    from engine import AnalysisReport, Bar, Scenario

_log = logging.getLogger(__name__)


def _analyst() -> Analyst:
    from analyst import get_default_analyst

    return get_default_analyst()


def prewarm() -> None:
    """Build the singleton + load heavy resources off the request path."""
    from analyst import prewarm_default_analyst

    prewarm_default_analyst()


def get_model_id() -> str:
    model_id = getattr(_analyst().llm_client, "model_id", None)
    if model_id is None:
        _log.warning("llm_client has no model_id — reporting 'unknown'")
        return "unknown"
    return model_id


def family_education(family: str) -> FamilyEducation | None:
    from analyst.diagnostics.education import family_education as _family_education

    return _family_education(family)


def compute_layer1(
    scenario: Scenario,
    bars: list[Bar],
    *,
    all_scenarios: list[Scenario],
    scale_mode: str,
) -> AnalysisResult:
    return _analyst().compute_layer1(
        scenario, bars, all_scenarios=all_scenarios, scale_mode=scale_mode
    )


def compute_top_layer1(
    report: AnalysisReport | None,
    bars: list[Bar],
    *,
    scale_mode: str,
) -> AnalysisResult | None:
    """Best-effort top-scenario Layer-1 (None on failure); never blocks the pipeline response."""
    if report is None or not report.scenarios:
        return None
    top = dependencies.top_scenario(report.scenarios)
    if top is None:
        return None
    try:
        return compute_layer1(
            top, bars, all_scenarios=list(report.scenarios), scale_mode=scale_mode
        )
    except Exception:
        _log.exception(
            "eager compute_layer1 failed for top scenario %s — client will fall "
            "back to /api/scenario/layer1",
            top.id,
        )
        return None


def analyze(
    scenario: Scenario,
    bars: list[Bar],
    mode: str,
    *,
    all_scenarios: list[Scenario],
    scale_mode: str,
    force_refresh: bool,
) -> AnalysisOutput:
    return _analyst().analyze(
        scenario,
        bars,
        mode,
        all_scenarios=all_scenarios,
        scale_mode=scale_mode,
        force_refresh=force_refresh,
    )


def qa_available() -> bool:
    """Q&A needs the embedder (similarity search); off unless ANALYST_QA=1."""
    return _analyst().retriever.embedder is not None


def is_prewarmed() -> bool:
    """True if the analyst singleton is already built. Inspects the lru_cache
    without triggering a (heavy) build — safe to call from a readiness probe."""
    from analyst import get_default_analyst

    return get_default_analyst.cache_info().currsize > 0


def qa_enabled_setting() -> bool:
    """Cheap env check (no analyst build) mirroring get_default_analyst's gate."""
    import os

    return os.getenv("ANALYST_QA") == "1"


def answer_question(
    question: str,
    *,
    scenario: Scenario | None,
    bars: list[Bar] | None,
    scale_mode: str,
    force_refresh: bool,
) -> QaOutput:
    return _analyst().answer_question(
        question,
        scenario=scenario,
        bars=bars,
        scale_mode=scale_mode,
        force_refresh=force_refresh,
    )
