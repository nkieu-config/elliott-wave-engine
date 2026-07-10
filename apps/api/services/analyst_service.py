"""Service seam over the `analyst` package, and the composition root that wires it
to its infrastructure adapters. Every analyst import is deferred into a function
body so importing this module at app startup stays light (numpy + embeddings)."""

from __future__ import annotations

import functools
import importlib.util
import logging
import os
from typing import TYPE_CHECKING

from apps.api import pipeline_ops

if TYPE_CHECKING:
    from analyst import AnalysisOutput, AnalysisResult, Analyst
    from analyst.diagnostics.education import FamilyEducation
    from analyst.schemas.qa import QaOutput
    from engine import AnalysisReport, Bar, Scenario

_log = logging.getLogger(__name__)


def _embedder_requested() -> bool:
    return (
        os.getenv("ANALYST_GROUNDING_CHECK") == "1" or os.getenv("ANALYST_QA") == "1"
    )


def _grounding_extra_installed() -> bool:
    # find_spec, not import: Embedder loads torch lazily and this runs on the
    # readiness probe. Without it a wrong env yields a 500 on first encode(),
    # not the 503 the route and UI are written for.
    return importlib.util.find_spec("sentence_transformers") is not None


def _build_embedder():
    # Embedder powers the soft grounding check (advisory) AND Q&A similarity
    # (required there). It pulls torch via sentence-transformers, so default off:
    # Layer-1 and narration are unaffected (by_pages/grounding no-op when None).
    # Opt in with ANALYST_GROUNDING_CHECK=1 or ANALYST_QA=1 (need grounding extra).
    if not _embedder_requested():
        return None
    if not _grounding_extra_installed():
        _log.warning(
            "ANALYST_QA/ANALYST_GROUNDING_CHECK is set but sentence-transformers is "
            "missing; embedder disabled (install the `grounding` extra to enable Q&A)"
        )
        return None
    from analyst.theory.embedder import Embedder  # heavy: pulls torch

    return Embedder()


@functools.lru_cache(maxsize=1)
def _analyst() -> Analyst:
    from analyst import build_analyst, load_default_corpus
    from infra.llm import OllamaClient

    chunks, embeddings = load_default_corpus()
    return build_analyst(
        chunks=chunks,
        embeddings=embeddings,
        embedder=_build_embedder(),
        llm_client=OllamaClient(),
    )


def prewarm() -> None:
    """Build the singleton + load heavy resources off the request path."""
    # Warms corpus + lru_cache; when grounding is enabled also loads the
    # SentenceTransformer (10-30s the first request would otherwise pay).
    embedder = _analyst().retriever.embedder
    if embedder is not None:
        prewarm_embedder = getattr(embedder, "prewarm", None)
        if callable(prewarm_embedder):
            prewarm_embedder()


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
    top = pipeline_ops.top_scenario(report.scenarios)
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


def is_prewarmed() -> bool:
    """True if the analyst singleton is already built. Inspects the lru_cache
    without triggering a (heavy) build — safe to call from a readiness probe."""
    return _analyst.cache_info().currsize > 0


def qa_enabled_setting() -> bool:
    """Cheap check (no analyst build) mirroring _analyst's embedder gate."""
    return os.getenv("ANALYST_QA") == "1" and _grounding_extra_installed()


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
