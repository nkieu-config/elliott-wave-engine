from __future__ import annotations

import math

from engine.link_rules import link_s_ratio_mode
from engine.types import ScaleMode

from ..types import _Leg


def _log_cv_score(values: list[float], K: float = 0.5) -> float | None:
    # exp(-stddev(log(v))/K). None when <2 positive values; non-positive dropped.
    pos = [v for v in values if v > 0]
    if len(pos) < 2:
        return None
    logs = [math.log(v) for v in pos]
    mean = sum(logs) / len(logs)
    var = sum((x - mean) ** 2 for x in logs) / len(logs)
    return math.exp(-math.sqrt(var) / K)


def _legs_total_price_range(legs: list[_Leg], mode: ScaleMode) -> float:
    if not legs:
        return 0.0
    prices: list[float] = []
    for lg in legs:
        prices.append(lg.span_start.price)
        prices.append(lg.span_end.price)
    lo, hi = min(prices), max(prices)
    if mode == "linear":
        return hi - lo
    if lo <= 0:
        return 0.0  # log undefined for non-positive prices
    return math.log(hi) - math.log(lo)


def _link_s_incremental_ratio(
    prior_set: _Leg,
    link_length: float,
    mode: ScaleMode,
) -> float | None:
    # Mirrors verifiers/link_s.py:_link_size_ratio; None ⇒ undecided / verifier decides.
    if prior_set.pattern_kind is None or not prior_set.sub_legs:
        return None
    ratio_mode = link_s_ratio_mode(prior_set.pattern_kind)

    if ratio_mode == "total_range":
        rng = _legs_total_price_range(prior_set.sub_legs, mode)
        return link_length / rng if rng > 0 else None

    if ratio_mode == "s5_leg":
        if len(prior_set.sub_legs) < 5:
            return None
        s5_len = prior_set.sub_legs[4].length(mode)
        return link_length / s5_len if s5_len > 0 else None

    return None
