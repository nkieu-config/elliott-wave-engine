# Anchor MUST come from active_pivots (pivots_to_segments matches exactly).
from __future__ import annotations

from engine.types import Pivot

__all__ = [
    "find_anchor",
]


def find_anchor(active_pivots: list[Pivot]) -> Pivot | None:
    """Pick the wave-count anchor: the lowest low among active pivots (ties → earliest)."""
    # Ties → earliest pivot (longest downstream window).
    anchor: Pivot | None = None
    for p in active_pivots:
        if p.kind != "low":
            continue
        if anchor is None or p.price < anchor.price:
            anchor = p
    return anchor
