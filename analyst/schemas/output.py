from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from analyst.schemas.analysis import AnalysisResult
from analyst.schemas.citation import CitationRef, CitationReport

Mode = Literal["explanation", "slot_focus", "differentiator", "scenario_outlook"]


@dataclass(frozen=True)
class AnalysisOutput:
    scenario_id: str
    mode: Mode
    layer1: AnalysisResult
    narration: str | None
    citations: tuple[CitationRef, ...]
    citation_report: CitationReport
    model_id: str | None
    prompt_version: str
    cached: bool
    # True when narration is the deterministic template (LLM disabled or gate rejected).
    fell_back: bool = False
    # Raw pre-gate LLM output (last attempt). None for template-only/legacy entries.
    raw_narration: str | None = None
