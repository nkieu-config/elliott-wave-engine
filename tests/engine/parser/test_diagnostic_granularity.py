from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from engine.parser import count_waves
from engine.parser.output import build_diagnostic
from engine.types import Pivot, Segment
from tests.fixtures import make_segments


def test_anchor_not_important_pivot_when_all_die_within_two_segments() -> None:
    pivots = [
        Pivot(i, datetime(2020, 1, 1) + timedelta(weeks=i), 100 + i * 10, "low", i)
        for i in range(4)
    ]
    segs = [Segment(pivots[i], pivots[i + 1]) for i in range(3)]
    anchor = pivots[0]
    report = count_waves(anchor, segs, "linear")

    assert not report.scenarios, "monotone sequence should kill every hypothesis"
    assert report.diagnostic.death_reason == "anchor_not_important_pivot"
    assert "anchor" in report.diagnostic.suggested_action.lower()
    assert "Important High/Low" in report.diagnostic.suggested_action


def test_clean_count_leaves_diagnostic_empty() -> None:
    segs = make_segments([100, 130, 115, 175, 155, 200])
    report = count_waves(segs[0].start, segs, "linear")
    assert report.scenarios, "expected at least one scenario for clean 5W_TREND"
    assert report.diagnostic.death_reason == ""
    assert report.diagnostic.suggested_action == ""


def test_build_diagnostic_healthy_path_returns_empty_strings() -> None:
    diag = build_diagnostic(
        scenarios_empty=False,
        timed_out=False,
        timeout_at_segment=-1,
        n_segments=10,
        first_divergence=-1,
        last_alive=9,
        root_completed_at=-1,
    )
    assert diag.death_reason == ""
    assert diag.suggested_action == ""
    assert diag.last_alive_segment_index == 9


def test_build_diagnostic_timeout_dominates_other_signals() -> None:
    diag = build_diagnostic(
        scenarios_empty=True,
        timed_out=True,
        timeout_at_segment=42,
        n_segments=100,
        first_divergence=20,
        last_alive=41,
        root_completed_at=30,
    )
    assert diag.death_reason == "hard_timeout_exceeded"
    assert "ลด BEAM_WIDTH" in diag.suggested_action
    assert "42" in diag.suggested_action and "100" in diag.suggested_action


def test_build_diagnostic_cause_2_root_completed_with_trailing_segments() -> None:
    diag = build_diagnostic(
        scenarios_empty=True,
        timed_out=False,
        timeout_at_segment=-1,
        n_segments=10,
        first_divergence=6,
        last_alive=8,
        root_completed_at=5,
    )
    assert diag.death_reason == "root_pattern_completed_but_segments_remain"
    assert "5" in diag.suggested_action
    assert "ก่อนหน้า" in diag.suggested_action or "ใหญ่กว่า" in diag.suggested_action


def test_build_diagnostic_cause_2_takes_priority_over_cause_1_signals() -> None:
    diag = build_diagnostic(
        scenarios_empty=True,
        timed_out=False,
        timeout_at_segment=-1,
        n_segments=8,
        first_divergence=3,
        last_alive=1,
        root_completed_at=1,
    )
    assert diag.death_reason == "root_pattern_completed_but_segments_remain"


def test_build_diagnostic_cause_1_anchor_not_pivot() -> None:
    diag = build_diagnostic(
        scenarios_empty=True,
        timed_out=False,
        timeout_at_segment=-1,
        n_segments=5,
        first_divergence=1,
        last_alive=0,
        root_completed_at=-1,
    )
    assert diag.death_reason == "anchor_not_important_pivot"
    assert "Important High/Low" in diag.suggested_action


def test_build_diagnostic_cause_3_rules_too_strict() -> None:
    diag = build_diagnostic(
        scenarios_empty=True,
        timed_out=False,
        timeout_at_segment=-1,
        n_segments=12,
        first_divergence=4,
        last_alive=6,
        root_completed_at=-1,
    )
    assert diag.death_reason == "rules_too_strict_or_pivot_noise"
    assert "4" in diag.suggested_action
    assert "Min-bars" in diag.suggested_action or "ZigZag" in diag.suggested_action


def test_build_diagnostic_cause_3_without_first_divergence_omits_focus_zone() -> None:
    diag = build_diagnostic(
        scenarios_empty=True,
        timed_out=False,
        timeout_at_segment=-1,
        n_segments=6,
        first_divergence=-1,
        last_alive=3,
        root_completed_at=-1,
    )
    assert diag.death_reason == "rules_too_strict_or_pivot_noise"
    assert "focus zone" not in diag.suggested_action


@pytest.mark.parametrize(
    "cause_state",
    [
        dict(
            scenarios_empty=True,
            timed_out=False,
            timeout_at_segment=-1,
            n_segments=4,
            first_divergence=2,
            last_alive=1,
            root_completed_at=-1,
        ),
        dict(
            scenarios_empty=True,
            timed_out=False,
            timeout_at_segment=-1,
            n_segments=10,
            first_divergence=6,
            last_alive=8,
            root_completed_at=5,
        ),
        dict(
            scenarios_empty=True,
            timed_out=False,
            timeout_at_segment=-1,
            n_segments=12,
            first_divergence=4,
            last_alive=6,
            root_completed_at=-1,
        ),
    ],
    ids=["cause1_anchor", "cause2_root_completed", "cause3_rules_strict"],
)
def test_build_diagnostic_carries_index_fields_unchanged(cause_state) -> None:
    diag = build_diagnostic(**cause_state)
    assert diag.first_divergence_index == cause_state["first_divergence"]
    assert diag.last_alive_segment_index == cause_state["last_alive"]
