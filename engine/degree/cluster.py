from __future__ import annotations

from engine.constants import (
    DEGREE_GANN_CEILING_RATIO,
    DEGREE_GANN_FLOOR_RATIO,
)

__all__ = ["gann_band_fits"]


def gann_band_fits(candidate: float, anchor: float) -> bool:
    # Degenerate anchor ⇒ True (don't poison sibling check).
    if anchor <= 0:
        return True
    ratio = candidate / anchor
    return DEGREE_GANN_FLOOR_RATIO <= ratio <= DEGREE_GANN_CEILING_RATIO
