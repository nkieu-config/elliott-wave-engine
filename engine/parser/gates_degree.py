from __future__ import annotations

from engine.constants import (
    DEGREE_GANN_FLOOR_DIVISOR,
    R9_LINK_TIME_MULTIPLIER_LINK_T,
)
from engine.helpers import bar_span as _bar_span

from .types import _Context

__all__ = ["_five_trend_s4_degree_ok", "_link_t_link_degree_ok"]


def _five_trend_s4_degree_ok(ctx: _Context, s4_bars: int | None) -> bool:
    # S4 bars ∈ [min(S2,S3), max(S2,S3)]; True (skip) when bar_index missing.
    if s4_bars is None:
        return True
    s2_bars = _bar_span(ctx.legs[1].span_start, ctx.legs[1].span_end)
    s3_bars = _bar_span(ctx.legs[2].span_start, ctx.legs[2].span_end)
    if s2_bars is None or s3_bars is None:
        return True
    floor = min(s2_bars, s3_bars)
    ceiling = max(s2_bars, s3_bars)
    return floor <= s4_bars <= ceiling


def _link_t_link_degree_ok(ctx: _Context, link_bars: int | None) -> bool:
    # p.64: link x DIVISOR >= floor.  p.94: link > MULTIPLIER x ceiling (strict, dominant).
    if link_bars is None:
        return True
    if not ctx.legs:
        return True
    g1 = ctx.legs[0]
    if not g1.sub_legs or len(g1.sub_legs) < 2:
        return True
    g1_s2 = g1.sub_legs[1]
    g1_s2_bars = _bar_span(g1_s2.span_start, g1_s2.span_end)

    prior_set = ctx.legs[-1]
    if not prior_set.sub_legs:
        return True
    prior_push = prior_set.sub_legs[-1]
    prior_push_bars = _bar_span(prior_push.span_start, prior_push.span_end)

    if g1_s2_bars is None or prior_push_bars is None:
        return True

    floor = min(g1_s2_bars, prior_push_bars)
    ceiling = max(g1_s2_bars, prior_push_bars)
    if link_bars * DEGREE_GANN_FLOOR_DIVISOR < floor:
        return False
    return link_bars > R9_LINK_TIME_MULTIPLIER_LINK_T * ceiling
