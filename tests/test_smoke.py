from __future__ import annotations

from datetime import datetime


def test_import_types() -> None:
    from engine.types import (
        Bar,
        OpenState,
        PatternKind,
        Pivot,
        RuleResult,
        Segment,
        WaveNode,
        WaveRole,
    )

    assert PatternKind.FIVE_TREND_S3_LONGEST.value == "5W_TREND_S3_LONGEST"
    assert WaveRole.S1.value == "s1"
    assert OpenState().current_role is None
    anchor = Pivot(0, datetime(2020, 1, 1), 100.0, "low", 0)
    assert WaveNode(role=WaveRole.ANCHOR, span_start=anchor).children == []
    assert Bar(time=datetime(2020, 1, 1), open=1.0, high=2.0, low=0.5, close=1.5).volume == 0.0
    assert RuleResult("smoke.r1", True).measured is None
    assert (
        Segment(start=anchor, end=Pivot(1, datetime(2020, 1, 8), 110.0, "high", 1)).direction
        == "up"
    )


def test_import_helpers() -> None:
    from engine import helpers

    assert callable(helpers.price_length)
    assert callable(helpers.alternates)
    assert callable(helpers.equal_within)


def test_import_verifiers() -> None:
    from engine.verifiers import (
        verify_3wave,
        verify_5wave_sideway,
        verify_5wave_trend,
        verify_link_s,
        verify_link_t,
    )

    assert callable(verify_5wave_trend)
    assert callable(verify_5wave_sideway)
    assert callable(verify_3wave)
    assert callable(verify_link_t)
    assert callable(verify_link_s)


def test_import_modules() -> None:
    from engine import adaptive, anchor, parser, pivot

    assert hasattr(adaptive, "allowed_sub_patterns")
    assert hasattr(anchor, "find_anchor")
    assert hasattr(parser, "count_waves")
    assert hasattr(pivot, "compute_zigzag_pivots_atr")
