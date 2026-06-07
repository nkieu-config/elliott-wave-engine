from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from engine.parser import (
    count_waves,
    pivots_to_segments,
)
from engine.types import PatternKind, Pivot
from tests.fixtures import make_segments

pytestmark = pytest.mark.slow


def test_walk_through_5w_trend_s3_longest() -> None:
    segs = make_segments([100, 130, 115, 175, 155, 200])
    anchor = segs[0].start
    report = count_waves(anchor, segs, "linear")

    assert len(report.scenarios) >= 1
    matching = [
        sc
        for sc in report.scenarios
        if sc.family == "5W_TREND"
        and sc.is_complete
        and sc.pattern_kind == PatternKind.FIVE_TREND_S3_LONGEST
        and sc.depth == 1
    ]
    assert len(matching) >= 1, (
        f"Expected at least one direct 5W_TREND_S3_LONGEST, "
        f"got scenarios: {[(s.family, s.pattern_kind, s.depth) for s in report.scenarios]}"
    )


def test_3w_completes_at_3_segments() -> None:
    segs = make_segments([100, 130, 115, 145])
    anchor = segs[0].start
    report = count_waves(anchor, segs, "linear")
    direct_3w = [
        sc for sc in report.scenarios if sc.family == "3W" and sc.is_complete and sc.depth == 1
    ]
    assert any(sc.pattern_kind == PatternKind.THREE_NORMAL for sc in direct_3w)


def test_3w_root_dies_when_4th_segment_with_no_subwave_path() -> None:
    segs = make_segments([100, 130, 115, 145, 130])
    anchor = segs[0].start
    report = count_waves(anchor, segs, "linear")
    direct_complete_3w = [
        sc
        for sc in report.scenarios
        if sc.family == "3W"
        and sc.is_complete
        and sc.depth == 1
        and all(lg.pattern_kind is None for lg in sc.legs)
    ]
    assert direct_complete_3w == []


def test_5w_sideway_recognized() -> None:
    p = [100.0, 200.0, 120.0, 180.0, 135.0, 170.0]
    segs = make_segments(p)
    anchor = segs[0].start
    report = count_waves(anchor, segs, "linear")
    direct_side = [
        sc
        for sc in report.scenarios
        if sc.family == "5W_SIDEWAY" and sc.is_complete and sc.depth == 1
    ]
    assert any(
        sc.pattern_kind in (PatternKind.FIVE_SIDEWAY_CONTRACT, PatternKind.FIVE_SIDEWAY_BALANCE)
        for sc in direct_side
    )


def test_seed_opens_all_root_families() -> None:
    segs = make_segments([100, 130])
    anchor = segs[0].start
    report = count_waves(anchor, segs, "linear")
    families = {sc.family for sc in report.scenarios}
    assert {"5W_TREND", "5W_SIDEWAY", "3W"}.issubset(families)
    for sc in report.scenarios:
        assert not sc.is_complete


def test_5w_trend_survives_5w_sideway_dies_with_strong_trend() -> None:
    segs = make_segments([100, 130, 120, 180, 165, 220])
    anchor = segs[0].start
    report = count_waves(anchor, segs, "linear")

    families_complete = {sc.family for sc in report.scenarios if sc.is_complete}
    assert "5W_SIDEWAY" not in families_complete


def test_no_scenarios_when_directions_mismatched() -> None:
    from engine.types import Pivot, Segment

    pivots = [
        Pivot(i, datetime(2020, 1, 1) + timedelta(weeks=i), 100 + i * 10, "low", i)
        for i in range(4)
    ]
    segs = [Segment(start=pivots[i], end=pivots[i + 1]) for i in range(3)]
    anchor = pivots[0]
    report = count_waves(anchor, segs, "linear")
    completed = [sc for sc in report.scenarios if sc.is_complete]
    assert len(completed) == 0


def test_pivots_to_segments_from_anchor() -> None:
    pivots = [
        Pivot(0, datetime(2020, 1, 1), 100, "low", 0),
        Pivot(1, datetime(2020, 1, 8), 120, "high", 1),
        Pivot(2, datetime(2020, 1, 15), 110, "low", 2),
        Pivot(3, datetime(2020, 1, 22), 140, "high", 3),
    ]
    anchor = pivots[1]
    segs = pivots_to_segments(pivots, anchor)
    assert len(segs) == 2
    assert segs[0].start.price == 120
    assert segs[-1].end.price == 140


def test_pivots_to_segments_anchor_not_found() -> None:
    pivots = [
        Pivot(0, datetime(2020, 1, 1), 100, "low", 0),
        Pivot(1, datetime(2020, 1, 8), 120, "high", 1),
    ]
    fake_anchor = Pivot(0, datetime(2025, 1, 1), 200, "low", 0)
    segs = pivots_to_segments(pivots, fake_anchor)
    assert segs == []


def test_pivots_to_segments_empty() -> None:
    assert pivots_to_segments([], Pivot(0, datetime(2020, 1, 1), 100, "low", 0)) == []


def test_diagnostic_when_no_scenarios() -> None:
    from engine.types import Pivot, Segment

    pivots = [Pivot(i, datetime(2020, 1, 1) + timedelta(weeks=i), 100, "low", i) for i in range(3)]
    segs = [Segment(start=pivots[i], end=pivots[i + 1]) for i in range(2)]
    anchor = pivots[0]
    report = count_waves(anchor, segs, "linear")
    assert not report.scenarios
    assert report.diagnostic.death_reason != ""
    assert report.diagnostic.suggested_action != ""


@pytest.mark.parametrize("mode", ["linear", "log"])
def test_works_in_both_modes(mode: str) -> None:
    segs = make_segments([100, 130, 115, 175, 155, 200])
    anchor = segs[0].start
    report = count_waves(anchor, segs, mode)  # type: ignore[arg-type]
    assert len(report.scenarios) >= 1


def _make_leg(role, start_price: float, end_price: float, start_idx: int = 0) -> object:
    from engine.parser.types import _Leg
    from engine.types import Pivot

    base = datetime(2020, 1, 1)
    start_kind = "low" if start_price < end_price else "high"
    end_kind = "high" if end_price > start_price else "low"
    return _Leg(
        role=role,
        span_start=Pivot(
            start_idx, base + timedelta(weeks=start_idx), start_price, start_kind, start_idx
        ),  # type: ignore[arg-type]
        span_end=Pivot(
            start_idx + 1, base + timedelta(weeks=start_idx + 1), end_price, end_kind, start_idx + 1
        ),  # type: ignore[arg-type]
    )


def test_5w_sideway_incremental_rejects_s3_below_lower_bound() -> None:
    from engine.parser.families import incremental_ok as _incremental_ok
    from engine.parser.types import _Context
    from engine.types import WaveRole

    s1 = _make_leg(WaveRole.S1, 100, 200, start_idx=0)
    s2 = _make_leg(WaveRole.S2, 200, 150, start_idx=1)
    ctx = _Context(family="5W_SIDEWAY", legs=[s1, s2])

    assert _incremental_ok(ctx, WaveRole.S3, leg_length=10.0, mode="linear") is False, (
        "incremental should reject r_s3_s2 = 0.2 (no subtype allows < 0.5)"
    )


def test_5w_sideway_incremental_accepts_s3_at_or_above_lower_bound() -> None:
    from engine.parser.families import incremental_ok as _incremental_ok
    from engine.parser.types import _Context
    from engine.types import WaveRole

    s1 = _make_leg(WaveRole.S1, 100, 200, start_idx=0)
    s2 = _make_leg(WaveRole.S2, 200, 150, start_idx=1)
    ctx = _Context(family="5W_SIDEWAY", legs=[s1, s2])

    assert _incremental_ok(ctx, WaveRole.S3, leg_length=25.0, mode="linear") is True
    assert _incremental_ok(ctx, WaveRole.S3, leg_length=40.0, mode="linear") is True
    assert _incremental_ok(ctx, WaveRole.S3, leg_length=75.0, mode="linear") is True


def test_5w_sideway_incremental_rejects_s5_below_lower_bound() -> None:
    from engine.parser.families import incremental_ok as _incremental_ok
    from engine.parser.types import _Context
    from engine.types import WaveRole

    s1 = _make_leg(WaveRole.S1, 100, 200, start_idx=0)
    s2 = _make_leg(WaveRole.S2, 200, 150, start_idx=1)
    s3 = _make_leg(WaveRole.S3, 150, 220, start_idx=2)
    s4 = _make_leg(WaveRole.S4, 220, 180, start_idx=3)
    ctx = _Context(family="5W_SIDEWAY", legs=[s1, s2, s3, s4])

    assert _incremental_ok(ctx, WaveRole.S5, leg_length=5.0, mode="linear") is False, (
        "incremental should reject r_s5_s4 = 0.125 (below the 0.236 floor)"
    )


def test_5w_sideway_incremental_accepts_s5_at_or_above_lower_bound() -> None:
    from engine.parser.families import incremental_ok as _incremental_ok
    from engine.parser.types import _Context
    from engine.types import WaveRole

    s1 = _make_leg(WaveRole.S1, 100, 200, start_idx=0)
    s2 = _make_leg(WaveRole.S2, 200, 150, start_idx=1)
    s3 = _make_leg(WaveRole.S3, 150, 220, start_idx=2)
    s4 = _make_leg(WaveRole.S4, 220, 180, start_idx=3)
    ctx = _Context(family="5W_SIDEWAY", legs=[s1, s2, s3, s4])

    assert _incremental_ok(ctx, WaveRole.S5, leg_length=40 * 0.236, mode="linear") is True
    assert _incremental_ok(ctx, WaveRole.S5, leg_length=32.0, mode="linear") is True
    assert _incremental_ok(ctx, WaveRole.S5, leg_length=60.0, mode="linear") is True
