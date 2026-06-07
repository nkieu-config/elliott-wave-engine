"""Headline-score → confidence tier. Cut-offs mirror `apps/web/lib/confidence.ts`; keep in sync."""

from __future__ import annotations

from typing import NamedTuple


class ConfidenceTier(NamedTuple):
    key: str
    word: str


def confidence_tier(score: float) -> ConfidenceTier:
    # Bands aren't thirds: final = min(structural, visual) × commitment sits low.
    if score >= 0.50:
        return ConfidenceTier("high", "Strong")
    if score >= 0.25:
        return ConfidenceTier("mid", "Moderate")
    return ConfidenceTier("low", "Low")
