from __future__ import annotations

from dataclasses import dataclass

from analyst.schemas.citation import CitationRef, CitationReport


@dataclass(frozen=True)
class QaOutput:
    question: str
    answer: str
    citations: tuple[CitationRef, ...]
    # Pages the similarity search surfaced — the answer's allowed-citation set.
    retrieved_pages: tuple[int, ...]
    citation_report: CitationReport
    # True when the question fell below the theory-relevance floor (no LLM call).
    out_of_scope: bool = False
    # True when the gate rejected the answer and no grounded reply was produced.
    fell_back: bool = False
    cached: bool = False
    model_id: str | None = None
