from __future__ import annotations

from typing import TYPE_CHECKING

from engine.degree.cluster import gann_band_fits
from engine.degree.measure import axis_for_family, measure_leg
from engine.types import ScaleMode

if TYPE_CHECKING:
    from engine.parser.types import _Context, _Leg

__all__ = ["gann_band_ok"]


def gann_band_ok(ctx: _Context, new_leg: _Leg, mode: ScaleMode) -> bool:
    # pp.94-95: Link-Wave sets and LINK connectors at the same degree.
    if not ctx.legs:
        return True
    axis = axis_for_family(ctx.family)
    new_size = measure_leg(new_leg, axis, mode)
    if new_size is None:
        return True
    for prior in ctx.legs:
        prior_size = measure_leg(prior, axis, mode)
        if prior_size is None:
            continue
        if not gann_band_fits(new_size, prior_size):
            return False
    return True
