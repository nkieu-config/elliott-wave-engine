"""Invariants on the Layer-1 markdown the LLM narrates from — locks the data
feed / serializer, not the LLM's prose. No LLM call."""

from __future__ import annotations

from analyst.diagnostics.bottleneck import diagnose_bottleneck
from analyst.diagnostics.confirmation import evaluate_confirmation
from analyst.diagnostics.decision import compute_decision_summary
from analyst.diagnostics.scenario_diff import ScenarioDiff, diff_top_scenarios
from analyst.serialization.analysis_blocks import (
    _lead_descriptor,
    _slot_detail_line,
    format_bottleneck,
    format_confirmation,
    format_decision_summary,
    format_scenario_diff,
)
from tests.analyst.fixtures.scenarios import (
    bars_ending_at,
    open_5ws_scenario,
    overshoot_5ws,
    sideway_vs_three_pair,
)


def test_overshoot_line_is_distinct_from_wave_progress():
    # Progress (from the start) and overshoot (past the far edge) are different
    # numbers; both must be fed so the LLM never derives one from the other.
    sc, bars, targets = overshoot_5ws()
    ds = compute_decision_summary(sc, bars, targets)

    assert ds.stage == "overshot"
    assert ds.overshoot_amount is not None and ds.overshoot_amount > 0
    assert ds.overshoot_pct_of_span is not None and ds.overshoot_pct_of_span > 0
    assert abs(ds.overshoot_pct_of_span - (ds.wave_progress_pct - 100.0)) < 1e-6
    assert round(ds.overshoot_pct_of_span) != round(ds.wave_progress_pct)

    md = format_decision_summary(ds)
    assert "Overshoot beyond far edge:" in md
    assert "Wave progress:" in md
    assert f"{ds.wave_progress_pct:.0f}%" in md
    assert f"${ds.overshoot_amount:,.2f}" in md


def test_stage_label_is_not_doubled():
    # The stage prose already opens with its label, so the Stage line must read
    # "OVERSHOT — …" once, never "OVERSHOT — OVERSHOT — …".
    sc, bars, targets = overshoot_5ws()
    md = format_decision_summary(compute_decision_summary(sc, bars, targets))
    assert "OVERSHOT — OVERSHOT" not in md
    assert md.count("**Stage:** OVERSHOT") == 1


def test_non_overshoot_decision_has_no_overshoot_line():
    # The Overshoot line appears only at stage == overshot, never in-band.
    sc, _bars, targets = overshoot_5ws()
    ds = compute_decision_summary(sc, bars_ending_at(150.0), targets)

    assert ds.stage != "overshot"
    assert ds.overshoot_amount is None
    assert "Overshoot beyond far edge" not in format_decision_summary(ds)


def test_leg_smoothness_detail_names_the_leg_direction():
    # A down leg must be labelled "a down leg" so narration can't call its move
    # "upward"; the referent stays neutral ("net travel"), not "advance".
    down = _slot_detail_line(
        "leg_smoothness",
        {"per_leg": [{"leg_idx": 3, "ratio": 1.666, "direction": "down"}]},
    )
    assert "down leg" in down
    assert "drawdown ratio" in down and "net travel" in down and "1.0" in down
    assert "advance" not in down.lower()

    up = _slot_detail_line(
        "leg_smoothness",
        {"per_leg": [{"leg_idx": 0, "ratio": 1.2, "direction": "up"}]},
    )
    assert "up leg" in up

    # Back-compat: a per_leg without a direction key still renders cleanly.
    plain = _slot_detail_line("leg_smoothness", {"per_leg": [{"leg_idx": 1, "ratio": 1.1}]})
    assert "drawdown ratio" in plain and "leg" in plain


def test_bottleneck_weakest_check_line_does_not_double_the_word_check():
    # The slot is named without a trailing "check", so narration's "weakest
    # check is <slot>" doesn't read "... is the swing smoothness check".
    bd = diagnose_bottleneck(
        {
            "leg_smoothness": 0.2, "pivot_sharpness": 0.8,
            "intermediates": {
                "leg_smoothness": {
                    "per_leg": [{"leg_idx": 0, "ratio": 1.5, "direction": "down"}]
                }
            },
        },
        "5W_SIDEWAY",
    )
    line = next(
        ln for ln in format_bottleneck(bd).splitlines() if "Weakest check:" in ln
    )
    assert line.lower().count("check") == 1  # only the label


def test_lead_descriptor_does_not_overstate_a_sub_majority_lead():
    # The real case (43% vs 31%): a lead, but rank-1 is under 50% → "moderate",
    # never "clear"/"decisive". Guards the "clear leader" overstatement.
    moderate = _lead_descriptor(0.43, 0.31)
    assert "moderate" in moderate
    assert "clear" not in moderate and "decisive" not in moderate
    assert "decisive" in _lead_descriptor(0.62, 0.20)  # majority + wide gap
    assert "near-tie" in _lead_descriptor(0.36, 0.34)   # negligible gap


def test_scenario_diff_renders_a_lead_strength_line():
    p, c = sideway_vs_three_pair()
    md = format_scenario_diff(tuple(diff_top_scenarios([p, c])))
    assert "Lead strength:" in md


def test_lead_strength_gap_matches_the_displayed_rounded_probabilities():
    # 0.432/0.306 display as 43%/31% (gap 12); the line must read "12-point",
    # not "13" from the unrounded difference, so it agrees with the table.
    d = ScenarioDiff(
        primary_rank=1, competitor_rank=2,
        primary_bottleneck="leg_smoothness", competitor_bottleneck="leg_smoothness",
        slot_deltas={}, structural_winner=1, visual_winner=1,
        pattern_kind_match=False,
        primary_family="5W_SIDEWAY", competitor_family="3W",
        primary_probability=0.432, competitor_probability=0.306,
    )
    md = format_scenario_diff((d,))
    assert "43%" in md and "31%" in md
    assert "12-point gap" in md
    assert "13-point gap" not in md


def test_open_pattern_confirmation_says_still_open_not_needs_legs():
    # Open pattern → reason must read "fifth still open", not "needs N legs"
    # (absent), and must not leak the raw family code.
    rep = evaluate_confirmation(open_5ws_scenario(), bars_ending_at(263.17), "linear")
    md = format_confirmation(rep)

    assert "still open" in md
    assert "needs" not in md.lower()
    assert "5W_SIDEWAY" not in md
    assert "5-Wave Sideway" in md
