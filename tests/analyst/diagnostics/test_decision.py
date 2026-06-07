from datetime import datetime, timedelta

import pytest

from analyst.diagnostics.decision import compute_decision_summary
from analyst.schemas.targets import Target, TargetSet
from engine.parser.output.types import Scenario
from engine.types import Bar, PatternKind
from tests.analyst._helpers import make_scenario
from tests.analyst.fixtures.scenarios import CONVERGING_5WS_LEGS


def _bars(closes: list[float]) -> list[Bar]:
    start = datetime(2024, 1, 1)
    return [
        Bar(time=start + timedelta(days=i), open=c, high=c, low=c, close=c)
        for i, c in enumerate(closes)
    ]


def _scenario(*, is_complete: bool, legs: list[tuple[int, int]]) -> Scenario:
    # Prices are 0 because callers using this helper don't read leg prices.
    return _scenario_with_leg_prices(
        is_complete=is_complete,
        leg_endpoints=[(sb, eb, 0.0, 0.0) for sb, eb in legs],
    )


def _scenario_with_leg_prices(
    *,
    is_complete: bool,
    leg_endpoints: list[tuple[int, int, float, float]],
    family: str = "5W_TREND",
) -> Scenario:
    # Contiguous pivot chain from (start_bar, end_bar, start_price, end_price);
    # pivot.kind picked by relative price so each leg's direction matches.
    if not leg_endpoints:
        # Degenerate scenario, no children.
        sc = make_scenario(
            family=family,
            pattern_kind=PatternKind.FIVE_TREND_S3_LONGEST if is_complete else None,
            pivots=[(0.0, 0, "low"), (0.0, 0, "high")],
            score_components={},
        )
        sc.root.children.clear()
        return sc
    sb0, _, sp0, _ = leg_endpoints[0]
    first_kind = "low" if leg_endpoints[0][3] >= sp0 else "high"
    pivots: list[tuple[float, int, str]] = [(sp0, sb0, first_kind)]
    for _sb, eb, sp, ep in leg_endpoints:
        pivots.append((ep, eb, "high" if ep >= sp else "low"))
    return make_scenario(
        family=family,
        pattern_kind=PatternKind.FIVE_TREND_S3_LONGEST if is_complete else None,
        pivots=pivots,
        score_components={},
    )


def _targets(
    *,
    projected: list[float] | None = None,
    invalidation_price: float | None = None,
) -> TargetSet:
    proj = tuple(
        Target(name=f"proj_{i}", price=p, type="projected",
               theory_page=111, derivation="test")
        for i, p in enumerate(projected or [])
    )
    inv = (
        Target(name="invalidation", price=invalidation_price,
               type="invalidation", theory_page=22, derivation="test")
        if invalidation_price is not None else None
    )
    return TargetSet(
        confirmation_targets=(), fib_flow_targets=proj, invalidation=inv,
    )


def test_decision_summary_returns_none_when_no_bars():
    sc = _scenario(is_complete=True, legs=[])
    assert compute_decision_summary(sc, [], None) is None


def test_decision_summary_uses_last_bar_close_as_current():
    bars = _bars([100.0, 105.0, 108.5])
    sc = _scenario(is_complete=True, legs=[])
    ds = compute_decision_summary(sc, bars, None)
    assert ds is not None
    assert ds.current.price == 108.5
    assert ds.current.pct_from_current == 0.0


def test_decision_summary_computes_pct_moves_to_targets_and_invalidation():
    bars = _bars([100.0])
    sc = _scenario(is_complete=False, legs=[(0, 10), (10, 18), (18, 30)])
    targets = _targets(projected=[125.0, 142.0], invalidation_price=90.0)
    ds = compute_decision_summary(sc, bars, targets)
    assert ds is not None
    assert ds.target_low.price == 125.0
    assert ds.target_low.pct_from_current == pytest.approx(25.0)
    assert ds.target_high.price == 142.0
    assert ds.target_high.pct_from_current == pytest.approx(42.0)
    assert ds.invalidation.price == 90.0
    assert ds.invalidation.pct_from_current == pytest.approx(-10.0)


def test_decision_summary_risk_reward_uses_band_midpoint():
    bars = _bars([100.0])
    sc = _scenario(is_complete=False, legs=[(0, 10), (10, 18)])
    targets = _targets(projected=[125.0, 142.0], invalidation_price=90.0)
    ds = compute_decision_summary(sc, bars, targets)
    assert ds.risk_reward == pytest.approx(3.35, abs=0.01)
    assert ds.direction == "up"


def test_decision_summary_direction_down_when_band_below_current():
    bars = _bars([100.0])
    sc = _scenario(is_complete=False, legs=[(0, 5), (5, 10)])
    targets = _targets(projected=[70.0, 80.0], invalidation_price=110.0)
    ds = compute_decision_summary(sc, bars, targets)
    assert ds.direction == "down"
    assert ds.risk_reward is not None


def test_decision_summary_refuses_rr_when_geometry_is_inverted():
    bars = _bars([100.0])
    sc = _scenario(is_complete=False, legs=[(0, 5), (5, 10)])
    targets = _targets(projected=[125.0, 142.0], invalidation_price=120.0)
    ds = compute_decision_summary(sc, bars, targets)
    assert ds.direction == "up"
    assert ds.risk_reward is None


def test_decision_summary_horizon_is_median_formed_leg_duration():
    bars = _bars([100.0])
    sc = _scenario(is_complete=False, legs=[(0, 10), (10, 18), (18, 30)])
    targets = _targets(projected=[125.0])
    ds = compute_decision_summary(sc, bars, targets)
    assert ds.horizon_bars == 10


def test_decision_summary_horizon_none_when_pattern_complete():
    bars = _bars([100.0])
    sc = _scenario(is_complete=True, legs=[(0, 10), (10, 20)])
    targets = _targets(projected=[120.0])
    ds = compute_decision_summary(sc, bars, targets)
    assert ds.horizon_bars is None


def test_decision_summary_no_targets_yields_no_band_no_rr():
    bars = _bars([100.0])
    sc = _scenario(is_complete=False, legs=[(0, 5), (5, 10)])
    ds = compute_decision_summary(sc, bars, None)
    assert ds is not None
    assert ds.current.price == 100.0
    assert ds.target_low is None
    assert ds.target_high is None
    assert ds.invalidation is None
    assert ds.risk_reward is None
    assert ds.direction is None


def test_decision_summary_stage_overshot_when_current_past_band():
    bars = _bars([212.49])
    sc = _scenario_with_leg_prices(is_complete=False, leg_endpoints=CONVERGING_5WS_LEGS)
    targets = _targets(projected=[115.02, 170.08], invalidation_price=98.01)
    ds = compute_decision_summary(sc, bars, targets)
    assert ds.stage == "overshot"
    assert ds.open_wave_start == 98.01
    assert ds.wave_progress_pct is not None
    assert ds.wave_progress_pct > 100


@pytest.mark.parametrize(
    ("close", "expected_stage"),
    [(140.0, "mid"), (100.0, "early")],
    ids=["mid_inside_band", "early_near_wave_start"],
)
def test_decision_summary_stage_by_current_close(close, expected_stage):
    bars = _bars([close])
    sc = _scenario_with_leg_prices(is_complete=False, leg_endpoints=CONVERGING_5WS_LEGS)
    targets = _targets(projected=[115.02, 170.08], invalidation_price=98.01)
    ds = compute_decision_summary(sc, bars, targets)
    assert ds.stage == expected_stage


def test_decision_summary_stage_complete_when_pattern_closed():
    bars = _bars([100.0])
    sc = _scenario_with_leg_prices(
        is_complete=True,
        leg_endpoints=[(0, 10, 50.0, 100.0), (10, 20, 100.0, 75.0)],
    )
    targets = _targets(projected=[120.0])
    ds = compute_decision_summary(sc, bars, targets)
    assert ds.stage == "complete"


def test_decision_summary_bar_interval_detected_from_bar_series():
    bars = _bars([100.0, 101.0, 102.0])
    sc = _scenario_with_leg_prices(
        is_complete=False,
        leg_endpoints=[(0, 5, 50.0, 80.0), (5, 10, 80.0, 60.0),
                       (10, 18, 60.0, 90.0)],
    )
    targets = _targets(projected=[110.0])
    ds = compute_decision_summary(sc, bars, targets)
    assert ds.bar_interval == "1d"
    # Formed-leg durations 5/5/8 → median 5; 5 × 1d formats as "5 days".
    assert ds.horizon_bars == 5
    assert ds.horizon_human == "5 days"


def test_alternative_brief_carries_alternative_decision_geometry():
    from analyst.diagnostics.decision import compute_alternative_brief
    bars = _bars([100.0])
    primary = _scenario_with_leg_prices(
        is_complete=False, leg_endpoints=[(0, 5, 50.0, 80.0), (5, 10, 80.0, 95.0)],
        family="5W_SIDEWAY",
    )
    alt = _scenario_with_leg_prices(
        is_complete=False, leg_endpoints=[(0, 5, 50.0, 80.0), (5, 10, 80.0, 95.0)],
        family="3W",
    )
    alt_targets = _targets(projected=[70.0, 80.0], invalidation_price=110.0)
    brief = compute_alternative_brief(primary, alt, bars, alt_targets)
    assert brief is not None
    assert brief.family == "3W"
    assert brief.direction == "down"
    assert brief.invalidation is not None
    assert brief.invalidation.price == 110.0


def test_alternative_brief_none_when_alternative_is_primary():
    from analyst.diagnostics.decision import compute_alternative_brief
    bars = _bars([100.0])
    sc = _scenario_with_leg_prices(
        is_complete=False, leg_endpoints=[(0, 5, 50.0, 80.0)],
        family="5W_SIDEWAY",
    )
    targets = _targets(projected=[120.0])
    assert compute_alternative_brief(sc, sc, bars, targets) is None


def test_open_wave_direction_inferred_from_last_formed_leg():
    # regression: v2.10
    bars = _bars([100.0])
    sc = _scenario_with_leg_prices(is_complete=False, leg_endpoints=CONVERGING_5WS_LEGS)
    targets = _targets(projected=[115.0, 170.0])
    ds = compute_decision_summary(sc, bars, targets)
    assert ds.open_wave_direction == "up"


def test_open_wave_direction_down_when_last_formed_leg_was_up():
    bars = _bars([100.0])
    sc = _scenario_with_leg_prices(
        is_complete=False,
        leg_endpoints=[
            (0, 10, 50.0, 100.0),
            (10, 20, 100.0, 60.0),
            (20, 30, 60.0, 130.0),
        ],
    )
    targets = _targets(projected=[80.0, 100.0])
    ds = compute_decision_summary(sc, bars, targets)
    assert ds.open_wave_direction == "down"


def test_open_wave_direction_none_when_pattern_complete():
    bars = _bars([100.0])
    sc = _scenario_with_leg_prices(
        is_complete=True,
        leg_endpoints=[(0, 10, 50.0, 100.0), (10, 20, 100.0, 75.0)],
    )
    ds = compute_decision_summary(sc, bars, _targets(projected=[120.0]))
    assert ds.open_wave_direction is None


def test_score_intermediates_surfaced_on_analysis_result():
    # regression: v2.12
    from analyst.schemas.analysis import AnalysisResult
    ar = AnalysisResult(scenario_id="test")
    assert ar.score_intermediates == {}


def test_format_horizon_human_no_leading_tilde():
    # regression: v2.10
    from analyst.diagnostics.decision import _format_horizon_human
    h = _format_horizon_human(82, "1w")
    assert h is not None
    assert not h.startswith("~"), f"horizon should not lead with ~: {h!r}"
    h2 = _format_horizon_human(82, "1d")
    assert h2 is not None
    assert not h2.startswith("~")
