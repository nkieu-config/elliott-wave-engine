from analyst.diagnostics.scenario_diff import ScenarioDiff
from analyst.schemas.analysis import AnalysisResult
from analyst.schemas.bottleneck import BottleneckDiagnosis
from analyst.schemas.citation import TheoryRef
from analyst.schemas.confirmation import ConfirmationLevel, ConfirmationReport
from analyst.schemas.succession import NextPattern, SuccessionReport
from analyst.schemas.targets import Target, TargetSet
from analyst.serialization.fallback import mode_fallback


def _bottleneck() -> BottleneckDiagnosis:
    return BottleneckDiagnosis(
        slot_name="leg_smoothness",
        slot_value=0.467,
        dimension="visual",
        is_dim_minimum=True,
        is_overall_minimum=True,
        gap_to_next=0.049,
        intermediates={},
        plain_explanation="Slot leg_smoothness scored 0.467.",
        theory_ref=TheoryRef(pages=(), concept="Chart appearance",
                             binding="heuristic", note="(no theory binding)"),
    )


def _diff() -> ScenarioDiff:
    return ScenarioDiff(
        primary_rank=1,
        competitor_rank=2,
        primary_bottleneck="leg_smoothness",
        competitor_bottleneck="speed_cluster",
        slot_deltas={"speed_cluster": 0.12, "leg_smoothness": -0.04,
                     "fib_push_pairs": 0.009},
        structural_winner=1,
        visual_winner=2,
        pattern_kind_match=False,
    )


def _invalidation() -> Target:
    return Target(name="invalidation", price=98.0, type="invalidation",
                  theory_page=22, derivation="s1 origin")


def test_differentiator_fallback_summarises_diff():
    layer1 = AnalysisResult(scenario_id="t1", scenario_diffs=(_diff(),))
    out = mode_fallback("differentiator", layer1)
    assert "swing smoothness" in out
    assert "wave pacing" in out
    assert "leg_smoothness" not in out and "speed_cluster" not in out
    # Score-points, not % — the differentiator prompt forbids "+12%" framing.
    assert "+12" in out and "+12%" not in out
    assert "score points" in out
    assert "0.12" not in out
    assert "shape-and-proportion" in out and "visual-appearance" in out


def test_differentiator_fallback_no_competitor():
    layer1 = AnalysisResult(scenario_id="t1", scenario_diffs=())
    out = mode_fallback("differentiator", layer1)
    assert "no rank-2 competitor" in out.lower()


def test_outlook_fallback_applicable_confirmation():
    conf = ConfirmationReport(
        family="5W_TREND",
        levels=(
            ConfirmationLevel("L1", "trendline break", True, 207, 33),
            ConfirmationLevel("L2", "100% retrace of s5", False, None, 34),
        ),
    )
    targets = TargetSet(
        confirmation_targets=(),
        fib_flow_targets=(Target("s1_0.382", 120.0, "retracement", 101, "d"),),
        invalidation=_invalidation(),
    )
    layer1 = AnalysisResult(scenario_id="t1", confirmation=conf, targets=targets)
    out = mode_fallback("scenario_outlook", layer1)
    assert "L1" in out
    assert "L2" in out and "100% retrace of s5" in out
    assert "1 Fibonacci Flow target" in out
    assert "$98.00" in out


def test_outlook_fallback_not_applicable_and_no_fib_targets():
    conf = ConfirmationReport.not_applicable(
        family="5W_SIDEWAY",
        reason="Incomplete 5W_SIDEWAY (needs 5 legs)",
        citation=43,
    )
    targets = TargetSet(
        confirmation_targets=(), fib_flow_targets=(), invalidation=_invalidation(),
    )
    layer1 = AnalysisResult(scenario_id="t1", confirmation=conf, targets=targets)
    out = mode_fallback("scenario_outlook", layer1)
    assert "not applicable" in out.lower()
    assert "Incomplete 5-Wave Sideway" in out
    assert "5W_SIDEWAY" not in out
    assert "No Fibonacci Flow targets" in out
    assert "$98.00" in out
    assert "legs) No Fibonacci" not in out
    assert "legs). No Fibonacci" in out


def test_outlook_fallback_projects_open_pattern_wave5():
    projected = tuple(
        Target(f"wave 5 projected_{lvl}", price=100.0 + lvl * 50,
               type="projected", theory_page=111, derivation="proj")
        for lvl in (0.382, 0.618, 1.0)
    )
    targets = TargetSet(confirmation_targets=(), fib_flow_targets=projected,
                        invalidation=_invalidation())
    layer1 = AnalysisResult(scenario_id="t1", targets=targets)
    out = mode_fallback("scenario_outlook", layer1)
    assert "still open" in out
    assert "projected" in out
    assert "No Fibonacci Flow targets" not in out


def test_outlook_fallback_includes_succession():
    succ = SuccessionReport(
        family="5W_SIDEWAY", is_terminal=False, note="",
        next_patterns=(
            NextPattern(link_type="+S", next_families=("3W", "5W_SIDEWAY"),
                        link_band_near=130.0, link_band_far=None,
                        theory_pages=(57, 67, 74), rationale="…"),
        ),
    )
    layer1 = AnalysisResult(scenario_id="t1", succession=succ)
    out = mode_fallback("scenario_outlook", layer1)
    # Friendly label, not the raw +S code (which the gate is built to reject).
    assert "Sideway linkage" in out
    assert "+S" not in out
    assert "5W_SIDEWAY" not in out
    assert "5-Wave Sideway" in out


def test_outlook_fallback_terminal_succession():
    succ = SuccessionReport(family="5W_TREND", is_terminal=True,
                            next_patterns=(), note="…")
    layer1 = AnalysisResult(scenario_id="t1", succession=succ)
    out = mode_fallback("scenario_outlook", layer1)
    assert "terminal" in out.lower()


def test_explanation_fallback_is_bottleneck_explanation():
    layer1 = AnalysisResult(scenario_id="t1", bottleneck=_bottleneck())
    assert mode_fallback("explanation", layer1) == "Slot leg_smoothness scored 0.467."


def test_slot_focus_fallback_is_bottleneck_explanation():
    layer1 = AnalysisResult(scenario_id="t1", bottleneck=_bottleneck())
    assert mode_fallback("slot_focus", layer1) == "Slot leg_smoothness scored 0.467."


def test_fallback_without_bottleneck_is_graceful():
    layer1 = AnalysisResult(scenario_id="t1", bottleneck=None)
    out = mode_fallback("explanation", layer1)
    assert out and "bottleneck" in out.lower()
