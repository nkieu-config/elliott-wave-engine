from __future__ import annotations

from math import inf
from typing import NamedTuple

from engine.adaptive import Family
from engine.constants import (
    R2_S2_MAX_RATIO_3W,
    R2_S2_MAX_RATIO_5WS,
    R2_S2_MIN_RATIO_3W,
    R2_S2_MIN_RATIO_5WS,
    R3_S3_MIN_RATIO_3W,
    R3_S4_MAX_RATIO_5WS,
    R3_S4_MIN_RATIO_5WS,
    R4_S3_MIN_CONTRACT_5WS,
    R5_S5_MIN_CONTRACT_5WS,
    R7_S5_MIN_RATIO_5WT,
    R8_LINK_MAX_RATIO_LINK_T,
    R8_LINK_MIN_RATIO_LINK_T,
)
from engine.helpers import bar_span as _bar_span
from engine.helpers import price_length
from engine.link_rules import link_s_min_required
from engine.types import ScaleMode, Segment, WaveRole

from .gates_degree import _five_trend_s4_degree_ok, _link_t_link_degree_ok
from .scoring.helpers import _link_s_incremental_ratio
from .types import _Context

# Per-family dispatch lives in parser.families; gates stays registry-free to avoid a cycle.
# _bar_span re-exported for `from .gates import _bar_span`.
__all__ = ["_bar_span"]


def _leg_ref_length(ctx: _Context, idx: int, mode: ScaleMode) -> float | None:
    if idx >= len(ctx.legs):
        return None
    v = ctx.legs[idx].length(mode)
    return v if v > 0 else None


class _RatioBand(NamedTuple):
    # leg_length / legs[ref_idx].length must land in the inclusive band [lo, hi].
    # hi=inf encodes a min-only rule; the 5W_SIDEWAY lows are the loosest bound
    # across Contract/Balance/Expand (the verifier re-checks the exact subtype).
    ref_idx: int
    lo: float
    hi: float


# The pure inclusive-band incremental rules (3W, 5W_SIDEWAY), as data. 5W_TREND
# and the link families use strict inequalities / degree gates, so they stay as
# handlers below.
_RATIO_BANDS: dict[tuple[Family, WaveRole], _RatioBand] = {
    ("3W", WaveRole.S2): _RatioBand(0, R2_S2_MIN_RATIO_3W, R2_S2_MAX_RATIO_3W),
    ("3W", WaveRole.S3): _RatioBand(1, R3_S3_MIN_RATIO_3W, inf),
    ("5W_SIDEWAY", WaveRole.S2): _RatioBand(0, R2_S2_MIN_RATIO_5WS, R2_S2_MAX_RATIO_5WS),
    ("5W_SIDEWAY", WaveRole.S3): _RatioBand(1, R4_S3_MIN_CONTRACT_5WS, inf),
    ("5W_SIDEWAY", WaveRole.S4): _RatioBand(2, R3_S4_MIN_RATIO_5WS, R3_S4_MAX_RATIO_5WS),
    ("5W_SIDEWAY", WaveRole.S5): _RatioBand(3, R5_S5_MIN_CONTRACT_5WS, inf),
}


def _ratio_band_ok(ctx: _Context, leg_length: float, mode: ScaleMode, band: _RatioBand) -> bool:
    ref = _leg_ref_length(ctx, band.ref_idx, mode)
    if ref is None:
        return False
    return band.lo <= leg_length / ref <= band.hi


def _incremental_ok_5w_trend(
    ctx: _Context,
    role: WaveRole,
    leg_length: float,
    mode: ScaleMode,
    leg_bars: int | None,
) -> bool:
    if role == WaveRole.S2:
        ref = _leg_ref_length(ctx, 0, mode)
        if ref is None:
            return False
        return leg_length < ref
    if role == WaveRole.S3:
        ref = _leg_ref_length(ctx, 1, mode)
        if ref is None:
            return False
        return leg_length > ref
    if role == WaveRole.S4:
        ref = _leg_ref_length(ctx, 2, mode)
        if ref is None:
            return False
        if leg_length >= ref:  # R6b — s4 < s3 (price)
            return False
        # Gann Box gate p.91: S4 bars ∈ [min(S2,S3), max(S2,S3)].
        return _five_trend_s4_degree_ok(ctx, leg_bars)
    if role == WaveRole.S5:
        ref = _leg_ref_length(ctx, 3, mode)
        if ref is None:
            return False
        return leg_length / ref >= R7_S5_MIN_RATIO_5WT
    return True


def _incremental_ok_link_t(
    ctx: _Context,
    role: WaveRole,
    leg_length: float,
    mode: ScaleMode,
    leg_bars: int | None,
) -> bool:
    # LINK role only — group positions blocked at _can_extend_with_segment.
    if role != WaveRole.LINK:
        return True
    if not ctx.legs:
        return False
    prior_set = ctx.legs[-1]
    if prior_set.sub_legs:
        s3_len = prior_set.sub_legs[-1].length(mode)
        if s3_len <= 0:
            return False
        r = leg_length / s3_len
        if not (R8_LINK_MIN_RATIO_LINK_T <= r <= R8_LINK_MAX_RATIO_LINK_T):
            return False
    return _link_t_link_degree_ok(ctx, leg_bars)


def _incremental_ok_link_s(
    ctx: _Context,
    role: WaveRole,
    leg_length: float,
    mode: ScaleMode,
    leg_bars: int | None,
) -> bool:
    del leg_bars
    if role != WaveRole.LINK:
        return True
    if not ctx.legs:
        return False
    prior_set = ctx.legs[-1]
    ratio = _link_s_incremental_ratio(prior_set, leg_length, mode)
    if ratio is None:
        return True
    return ratio >= link_s_min_required(prior_set.pattern_kind)


def bands_for_family(family: Family) -> dict[WaveRole, _RatioBand]:
    return {role: band for (fam, role), band in _RATIO_BANDS.items() if fam == family}


# LINK_T stage pre-gates, bound to the LINK_T spec as hooks — no family guard needed.


def _link_t_open_size_ok(ctx: _Context, role: WaveRole, seg: Segment, mode: ScaleMode) -> bool:
    # LINK_T R8 upper-bound pre-gate p.62: seg can only grow, so >61.8%*prior_s3 ⇒ R8 fail at close.
    if role != WaveRole.LINK or not ctx.legs:
        return True
    prior_set = ctx.legs[-1]
    if not prior_set.sub_legs:
        return True
    s3_len = prior_set.sub_legs[-1].length(mode)
    if s3_len <= 0:
        return True
    return price_length(seg, mode) <= R8_LINK_MAX_RATIO_LINK_T * s3_len


def _link_t_r7_close_ok(
    closed: _Context, parent_ctx: _Context, parent_role: WaveRole, mode: ScaleMode
) -> bool:
    # LINK_T R7 p.62: closing 3W set's s1 must exceed prior link length (else in-progress absorbs tiny sets).
    if parent_role not in (WaveRole.SET_2, WaveRole.SET_3):
        return True
    if not parent_ctx.legs or not closed.legs:
        return True
    prior_link = parent_ctx.legs[-1]
    s1_len = closed.legs[0].length(mode)
    link_len = prior_link.length(mode)
    return not (link_len > 0 and s1_len <= link_len)
