"""Edge-case fixtures for the deterministic serialization-invariant tests.

Builders return plain data (scenario / bars / TargetSet) fed straight to the
diagnostics + serializers — no LLM call. Reuses ``make_scenario``."""

from __future__ import annotations

from datetime import datetime, timedelta

from analyst.schemas.targets import Target, TargetSet
from engine.parser.output.types import Scenario
from engine.types import Bar, PatternKind
from tests.analyst._helpers import make_scenario


def bars_ending_at(price: float, *, n: int = 3) -> list[Bar]:
    # Only the last close matters (current price); flat series keeps it simple.
    start = datetime(2024, 1, 1)
    return [
        Bar(time=start + timedelta(days=i), open=price, high=price,
            low=price, close=price)
        for i in range(n)
    ]


def _open_scenario_from_legs(
    leg_endpoints: list[tuple[int, int, float, float]], *, family: str,
) -> Scenario:
    # (start_bar, end_bar, start_price, end_price) → contiguous pivot chain,
    # pattern_kind=None so the scenario reads as open (final wave unformed).
    sb0, _, sp0, _ = leg_endpoints[0]
    first_kind = "low" if leg_endpoints[0][3] >= sp0 else "high"
    pivots: list[tuple[float, int, str]] = [(sp0, sb0, first_kind)]
    for _sb, eb, sp, ep in leg_endpoints:
        pivots.append((ep, eb, "high" if ep >= sp else "low"))
    return make_scenario(
        family=family, pattern_kind=None, pivots=pivots, score_components={},
    )


# The chart under review: a CONTRACTING 5-Wave Sideway (peaks step down
# 199.68→170.08, troughs step up 61.34→98.01) with Wave 5 open and overshot.
CONVERGING_5WS_LEGS: list[tuple[int, int, float, float]] = [
    (0, 30, 27.55, 199.68),    # W1 up
    (30, 50, 199.68, 61.34),   # W2 down
    (50, 80, 61.34, 170.08),   # W3 up   (peak below W1 → contracting)
    (80, 110, 170.08, 98.01),  # W4 down (trough above W2 → contracting)
]


def overshoot_5ws() -> tuple[Scenario, list[Bar], TargetSet]:
    # Open converging 5W Sideway overshot: far edge 170.08, start 98.01, current
    # 263.17 → progress ≈229%, overshoot ≈129% of span ($93.09 past the edge).
    sc = _open_scenario_from_legs(CONVERGING_5WS_LEGS, family="5W_SIDEWAY")
    bars = bars_ending_at(263.17)
    targets = TargetSet(
        confirmation_targets=(),
        fib_flow_targets=(
            Target(name="proj_0", price=115.02, type="projected",
                   theory_page=111, derivation="fixture"),
            Target(name="proj_1", price=170.08, type="projected",
                   theory_page=111, derivation="fixture"),
        ),
        invalidation=Target(name="invalidation", price=98.01,
                            type="invalidation", theory_page=22,
                            derivation="fixture"),
    )
    return sc, bars, targets


def open_5ws_scenario() -> Scenario:
    """Open 5W Sideway with 4 formed legs (fifth still open) — confirmation N/A."""
    return _open_scenario_from_legs(CONVERGING_5WS_LEGS, family="5W_SIDEWAY")


def sideway_vs_three_pair() -> tuple[Scenario, Scenario]:
    """Rank-1 5W Sideway vs rank-2 3W, with score_components for the diff block."""
    primary = make_scenario(
        family="5W_SIDEWAY", pattern_kind=None, score=0.43,
        score_components={
            "leg_smoothness": 0.40, "pull_depth_discipline": 0.50,
            "speed_cluster": 0.62, "structural_total": 0.60, "visual_total": 0.55,
        },
    )
    competitor = make_scenario(
        family="3W", scenario_id="alt", score=0.31,
        pattern_kind=PatternKind.THREE_S2_LONGER,
        pivots=[(100.0, 0, "low"), (160.0, 40, "high"), (120.0, 80, "low")],
        score_components={
            "leg_smoothness": 0.40, "pull_depth_discipline": 0.62,
            "speed_cluster": 0.50, "structural_total": 0.52, "visual_total": 0.50,
        },
    )
    return primary, competitor
