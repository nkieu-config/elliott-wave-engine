from __future__ import annotations

from engine.types import Bar

from ..scoring_config import ScoringConfig
from ..types import _Leg


def _pace(leg: _Leg) -> float | None:
    if leg.span_start.bar_index is None or leg.span_end.bar_index is None:
        return None
    span = leg.span_end.bar_index - leg.span_start.bar_index
    if span <= 0:
        return None
    return abs(leg.span_end.price - leg.span_start.price) / span


def _pivot_sharpness_scores(
    legs: list[_Leg],
    bars: tuple[Bar, ...],
    cfg: ScoringConfig,
) -> list[tuple[int, float]]:
    win = cfg.pivot_window
    out: list[tuple[int, float]] = []
    for i in range(len(legs) - 1):
        pivot = legs[i].span_end
        leg_in, leg_out = legs[i], legs[i + 1]
        if pivot.bar_index is None:
            continue
        in_bar = leg_in.span_start.bar_index
        out_bar = leg_out.span_end.bar_index
        if in_bar is None or out_bar is None:
            continue
        pace_in = _pace(leg_in)
        pace_out = _pace(leg_out)
        if pace_in is None or pace_out is None or pace_in <= 0 or pace_out <= 0:
            continue
        ratios: list[float] = []
        for b_idx in range(pivot.bar_index - win + 1, pivot.bar_index + 1):
            if 0 <= b_idx < len(bars) and b_idx > in_bar:
                b = bars[b_idx]
                ratios.append(min(abs(b.close - b.open) / pace_in, 1.0))
        for b_idx in range(pivot.bar_index + 1, pivot.bar_index + win + 1):
            if 0 <= b_idx < len(bars) and b_idx <= out_bar:
                b = bars[b_idx]
                ratios.append(min(abs(b.close - b.open) / pace_out, 1.0))
        if ratios:
            out.append((i, sum(ratios) / len(ratios)))
    return out


def pivot_sharpness(
    legs: list[_Leg],
    bars: tuple[Bar, ...],
    config: ScoringConfig | None = None,
) -> float | None:
    # avg(|close-open|/leg_pace) over ±pivot_window. Linear bars→1.0, cosine-eased→low.
    cfg = config or ScoringConfig()
    if len(legs) < 2 or not bars:
        return None
    scores = _pivot_sharpness_scores(legs, bars, cfg)
    if not scores:
        return None
    return sum(s for _, s in scores) / len(scores)


def pivot_sharpness_verbose(
    legs: list[_Leg],
    bars: tuple[Bar, ...],
    config: ScoringConfig | None = None,
) -> tuple[float | None, dict]:
    cfg = config or ScoringConfig()
    if len(legs) < 2 or not bars:
        return None, {}
    scores = _pivot_sharpness_scores(legs, bars, cfg)
    if not scores:
        return None, {}
    per_pivot = [{"pivot_idx": i, "sharpness_score": s} for i, s in scores]
    return sum(s for _, s in scores) / len(scores), {"per_pivot": per_pivot}


def _leg_smoothness_data(
    legs: list[_Leg],
    bars: tuple[Bar, ...],
) -> list[tuple[int, float, float]]:
    # Drawdown: up=max(running_max-low), down=max(high-running_min).
    out: list[tuple[int, float, float]] = []
    for idx, leg in enumerate(legs):
        if leg.span_start.bar_index is None or leg.span_end.bar_index is None:
            continue
        price_len = abs(leg.span_end.price - leg.span_start.price)
        if price_len <= 0:
            continue
        start_idx = leg.span_start.bar_index
        end_idx = leg.span_end.bar_index
        leg_bars = [bars[i] for i in range(start_idx + 1, end_idx + 1) if 0 <= i < len(bars)]
        if not leg_bars:
            continue
        up = leg.span_end.price > leg.span_start.price
        max_dd = 0.0
        if up:
            running_max = leg.span_start.price
            for b in leg_bars:
                max_dd = max(max_dd, running_max - b.low)
                running_max = max(running_max, b.high)
        else:
            running_min = leg.span_start.price
            for b in leg_bars:
                max_dd = max(max_dd, b.high - running_min)
                running_min = min(running_min, b.low)
        out.append((idx, max_dd, price_len))
    return out


def leg_smoothness(
    legs: list[_Leg],
    bars: tuple[Bar, ...],
    config: ScoringConfig | None = None,
) -> float | None:
    del config
    if not legs or not bars:
        return None
    data = _leg_smoothness_data(legs, bars)
    if not data:
        return None
    scores = [max(0.0, 1.0 - max_dd / price_len) for _, max_dd, price_len in data]
    return sum(scores) / len(scores)


def leg_smoothness_verbose(
    legs: list[_Leg],
    bars: tuple[Bar, ...],
    config: ScoringConfig | None = None,
) -> tuple[float | None, dict]:
    del config
    if not legs or not bars:
        return None, {}
    data = _leg_smoothness_data(legs, bars)
    if not data:
        return None, {}
    scores: list[float] = []
    per_leg: list[dict] = []
    for idx, max_dd, price_len in data:
        leg = legs[idx]
        scores.append(max(0.0, 1.0 - max_dd / price_len))
        per_leg.append(
            {
                "leg_idx": idx,
                "max_dd": max_dd,
                "leg_length": price_len,
                "ratio": max_dd / price_len,
                # Direction so narration can't mislabel a down leg's move as "up".
                "direction": (
                    "up" if leg.span_end.price > leg.span_start.price else "down"
                ),
            }
        )
    return sum(scores) / len(scores), {"per_leg": per_leg}
