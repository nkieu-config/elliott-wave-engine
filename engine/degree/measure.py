from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from engine.helpers import bar_span
from engine.types import ScaleMode

if TYPE_CHECKING:
    from engine.parser.types import Family, _Leg

__all__ = ["Axis", "axis_for_family", "measure_leg"]

Axis = Literal["time", "price"]


# pp.91-95: 5W_TREND/LINK_T = TIME; others = PRICE.
_TIME_AXIS_FAMILIES: frozenset[str] = frozenset({"5W_TREND", "LINK_T"})


def axis_for_family(family: Family) -> Axis:
    return "time" if family in _TIME_AXIS_FAMILIES else "price"


def measure_leg(leg: _Leg, axis: Axis, mode: ScaleMode) -> float | None:
    if axis == "time":
        span = bar_span(leg.span_start, leg.span_end)
        if span is None or span <= 0:
            return None
        return float(span)
    pl = leg.length(mode)
    return pl if pl > 0 else None
