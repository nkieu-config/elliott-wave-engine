from __future__ import annotations

from analyst._fingerprint import PIPELINE_FINGERPRINT
from analyst.client.ollama_client import OllamaClient
from analyst.diagnostics.chart_primitives import trendline_at
from analyst.diagnostics.education import family_education
from analyst.diagnostics.targets import compute_targets
from analyst.orchestrator import (
    Analyst,
    analyze,
    build_analyst,
    get_default_analyst,
    prewarm_default_analyst,
)
from analyst.schemas.analysis import AnalysisResult
from analyst.schemas.bottleneck import BottleneckDiagnosis
from analyst.schemas.output import AnalysisOutput
from analyst.schemas.targets import TargetSet
from analyst.taxonomy import GLOSSARY, humanize_family_codes
from analyst.theory.chunker import Chunk
from analyst.theory.citation_map import concept_for_page
from analyst.theory.embedder import Embedder

__all__ = [
    "Analyst",
    "analyze",
    "build_analyst",
    "get_default_analyst",
    "prewarm_default_analyst",
    "OllamaClient",
    "Chunk",
    "Embedder",
    "PIPELINE_FINGERPRINT",
    "AnalysisOutput",
    "AnalysisResult",
    "BottleneckDiagnosis",
    "TargetSet",
    "GLOSSARY",
    "compute_targets",
    "concept_for_page",
    "family_education",
    "humanize_family_codes",
    "trendline_at",
]
