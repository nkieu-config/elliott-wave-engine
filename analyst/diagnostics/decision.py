from __future__ import annotations

import statistics

from analyst.schemas.decision import (
    AlternativeBrief,
    DecisionSummary,
    PriceMove,
    WaveStage,
)
from analyst.schemas.targets import TargetSet
from engine import Bar, Scenario
from engine.display import family_label


def _pct(current: float, level: float) -> float:
    if current <= 0:
        return 0.0
    return (level - current) / current * 100.0


def _projection_band(targets: TargetSet | None) -> tuple[float, float] | None:
    # Prefer projected (open) > confirmation (closed) > full fib_flow.
    if targets is None:
        return None
    for bucket in (
        [t for t in targets.fib_flow_targets if t.type == "projected"],
        list(targets.confirmation_targets),
        list(targets.fib_flow_targets),
    ):
        if bucket:
            prices = [t.price for t in bucket]
            return (min(prices), max(prices))
    return None


def _open_wave_start_price(scenario: Scenario) -> float | None:
    if scenario.is_complete or not scenario.legs:
        return None
    last_formed = None
    for leg in scenario.legs:
        if (
            leg.span_end is not None
            and leg.span_end.price is not None
        ):
            last_formed = leg
    if last_formed is None:
        return None
    return float(last_formed.closed_end.price)


def _open_wave_direction(scenario: Scenario) -> str | None:
    # Elliott alternation: open wave goes opposite last formed leg.
    if scenario.is_complete or not scenario.legs:
        return None
    last_formed = None
    for leg in scenario.legs:
        if (
            leg.span_start is not None and leg.span_end is not None
            and leg.span_start.price is not None
            and leg.span_end.price is not None
        ):
            last_formed = leg
    if last_formed is None:
        return None
    last_direction_up = (
        last_formed.closed_end.price > last_formed.span_start.price
    )
    return "down" if last_direction_up else "up"


def _bar_interval(bars: list[Bar]) -> str | None:
    # Median (not mean) — weekend gaps / missing bars shouldn't skew.
    if len(bars) < 2:
        return None
    deltas = [
        (bars[i].time - bars[i - 1].time).total_seconds()
        for i in range(1, len(bars))
    ]
    if not deltas:
        return None
    median_sec = statistics.median(deltas)
    common = {
        60: "1m", 300: "5m", 900: "15m", 1800: "30m",
        3600: "1h", 14400: "4h", 86400: "1d", 604800: "1w",
    }
    # Smallest log-ratio distance is robust to daily-bar slip.
    best = min(common, key=lambda k: abs(median_sec / k - 1))
    if abs(median_sec / best - 1) > 0.25:
        return None
    return common[best]


_INTERVAL_SECONDS: dict[str, int] = {
    "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
    "1h": 3600, "4h": 14400, "1d": 86400, "1w": 604800,
}


def _format_horizon_human(bars: int | None, interval: str | None) -> str | None:
    # No leading "~" — callers compose the approximation marker.
    if bars is None or interval is None or interval not in _INTERVAL_SECONDS:
        return None
    seconds = bars * _INTERVAL_SECONDS[interval]
    minutes = seconds / 60
    hours = seconds / 3600
    days = seconds / 86400
    weeks = days / 7
    months = days / 30.44
    if minutes < 60:
        return f"{int(minutes)} minutes"
    if hours < 24:
        return f"{int(hours)} hours"
    if days < 14:
        return f"{int(days)} days"
    if weeks < 8:
        return f"{int(weeks)} weeks"
    if months < 18:
        return f"{int(months)} months"
    return f"{months / 12:.1f} years"


# Late only past 80%, overshot >100% so hair-over bands flag promptly.
_STAGE_EARLY_MAX = 25.0
_STAGE_MID_MAX = 80.0
_STAGE_LATE_MAX = 100.0
_STAGE_OVERSHOT_MIN = 100.0


def _stage(progress_pct: float | None, *, is_complete: bool) -> WaveStage:
    if is_complete:
        return "complete"
    if progress_pct is None:
        return "unknown"
    if progress_pct < 0:
        return "early"
    if progress_pct < _STAGE_EARLY_MAX:
        return "early"
    if progress_pct < _STAGE_MID_MAX:
        return "mid"
    if progress_pct < _STAGE_LATE_MAX:
        return "late"
    return "overshot"


def _far_edge(band: tuple[float, float] | None, start: float | None) -> float | None:
    # Band end farther from start = the edge the wave heads for.
    if band is None or start is None:
        return None
    lo, hi = band
    return hi if abs(hi - start) >= abs(lo - start) else lo


def _wave_progress_pct(
    current: float, band: tuple[float, float] | None, start: float | None,
) -> float | None:
    # 0 = wave start, 100 = far band edge, >100 = overshot. Far edge = end farther from start.
    far = _far_edge(band, start)
    if far is None or start is None:
        return None
    span = far - start
    if span == 0:
        return None
    return (current - start) / span * 100.0


def _horizon_bars(scenario: Scenario) -> int | None:
    # Median formed-leg duration — same-degree principle proxy.
    if scenario.is_complete:
        return None
    durations: list[int] = []
    for leg in scenario.legs:
        end = leg.span_end
        start_bar = leg.span_start.bar_index
        if end is None or end.bar_index is None or start_bar is None:
            continue
        durations.append(end.bar_index - start_bar)
    if len(durations) < 2:
        return None
    return int(statistics.median(durations))


def _risk_reward(
    current: float, band: tuple[float, float] | None, invalidation: float | None,
) -> tuple[float | None, str | None]:
    if band is None:
        return None, None
    mid = sum(band) / 2.0
    direction = "up" if mid > current else "down"
    if invalidation is None:
        return None, direction
    reward = abs(mid - current)
    risk = abs(current - invalidation)
    # Refuse ratio on inverted geometry — misleading number worse than none.
    if direction == "up" and invalidation >= current:
        return None, direction
    if direction == "down" and invalidation <= current:
        return None, direction
    if risk <= 0:
        return None, direction
    return reward / risk, direction


def compute_decision_summary(
    scenario: Scenario,
    bars: list[Bar],
    targets: TargetSet | None,
) -> DecisionSummary | None:
    if not bars:
        return None
    current_price = bars[-1].close
    current = PriceMove(
        label="Current", price=current_price, pct_from_current=0.0,
    )

    band = _projection_band(targets)
    invalidation_price = (
        targets.invalidation.price
        if targets is not None and targets.invalidation is not None
        else None
    )

    target_low = (
        PriceMove(
            label="Lower target",
            price=band[0],
            pct_from_current=_pct(current_price, band[0]),
        )
        if band is not None else None
    )
    target_high = (
        PriceMove(
            label="Upper target",
            price=band[1],
            pct_from_current=_pct(current_price, band[1]),
        )
        if band is not None else None
    )
    invalidation = (
        PriceMove(
            label="Invalidation",
            price=invalidation_price,
            pct_from_current=_pct(current_price, invalidation_price),
        )
        if invalidation_price is not None else None
    )
    rr, direction = _risk_reward(current_price, band, invalidation_price)
    horizon = _horizon_bars(scenario)
    interval = _bar_interval(bars)
    horizon_human = _format_horizon_human(horizon, interval)
    open_start = _open_wave_start_price(scenario)
    open_dir = _open_wave_direction(scenario)
    progress_pct = _wave_progress_pct(current_price, band, open_start)
    stage = _stage(progress_pct, is_complete=scenario.is_complete)
    # Distance past the far edge, quoted directly so narration never derives it.
    overshoot_amount: float | None = None
    overshoot_pct_of_span: float | None = None
    if stage == "overshot" and progress_pct is not None:
        far = _far_edge(band, open_start)
        if far is not None:
            overshoot_amount = abs(current_price - far)
            overshoot_pct_of_span = progress_pct - 100.0
    return DecisionSummary(
        current=current,
        target_low=target_low,
        target_high=target_high,
        invalidation=invalidation,
        risk_reward=rr,
        direction=direction,
        horizon_bars=horizon,
        bar_interval=interval,
        horizon_human=horizon_human,
        stage=stage,
        open_wave_start=open_start,
        open_wave_direction=open_dir,
        wave_progress_pct=progress_pct,
        overshoot_amount=overshoot_amount,
        overshoot_pct_of_span=overshoot_pct_of_span,
    )


def compute_alternative_brief(
    primary: Scenario,
    alternative: Scenario,
    bars: list[Bar],
    alt_targets: TargetSet | None,
) -> AlternativeBrief | None:
    if alternative is primary or not bars:
        return None
    current_price = bars[-1].close
    band = _projection_band(alt_targets)
    invalidation_price = (
        alt_targets.invalidation.price
        if alt_targets is not None and alt_targets.invalidation is not None
        else None
    )
    target_low = (
        PriceMove(
            label="Alt lower",
            price=band[0],
            pct_from_current=_pct(current_price, band[0]),
        )
        if band is not None else None
    )
    target_high = (
        PriceMove(
            label="Alt upper",
            price=band[1],
            pct_from_current=_pct(current_price, band[1]),
        )
        if band is not None else None
    )
    invalidation = (
        PriceMove(
            label="Alt invalidation",
            price=invalidation_price,
            pct_from_current=_pct(current_price, invalidation_price),
        )
        if invalidation_price is not None else None
    )
    _, direction = _risk_reward(current_price, band, invalidation_price)
    open_start = _open_wave_start_price(alternative)
    progress_pct = _wave_progress_pct(current_price, band, open_start)
    stage = _stage(progress_pct, is_complete=alternative.is_complete)
    family_code = alternative.family or ""
    return AlternativeBrief(
        family=family_code,
        family_label=family_label(family_code, friendly=True) or family_code,
        target_low=target_low,
        target_high=target_high,
        invalidation=invalidation,
        direction=direction,
        stage=stage,
    )
