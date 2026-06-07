from __future__ import annotations

import pytest

from engine.constants import R7_S5_MIN_RATIO_5WT
from engine.helpers import price_length
from engine.parser.families import incremental_ok as _incremental_ok
from engine.parser.types import _Context, _Leg
from engine.types import PatternKind, ScaleMode, Segment, WaveRole
from engine.verifiers import verify_3wave, verify_5wave_sideway, verify_5wave_trend
from tests.fixtures import build_5w_trend_segments, make_segments

_NON_LINK_ROLES = (
    WaveRole.S1,
    WaveRole.S2,
    WaveRole.S3,
    WaveRole.S4,
    WaveRole.S5,
)


def _build_partial_ctx(
    family: str,
    segs: list[Segment],
    num_legs: int,
) -> _Context:
    ctx = _Context(family=family, legs=[])
    for i in range(num_legs):
        leg = _Leg(
            role=_NON_LINK_ROLES[i],
            span_start=segs[i].start,
            span_end=segs[i].end,
        )
        ctx.legs.append(leg)
    return ctx


def _seg_bar_span(seg: Segment) -> int | None:
    a = seg.start.bar_index
    b = seg.end.bar_index
    if a is None or b is None:
        return None
    return abs(b - a)


def _gate_accepts_every_leg(
    family: str,
    segs: list[Segment],
    mode: ScaleMode,
) -> tuple[bool, int]:
    for i in range(1, len(segs)):
        ctx = _build_partial_ctx(family, segs, num_legs=i)
        next_seg = segs[i]
        ok = _incremental_ok(
            ctx,
            _NON_LINK_ROLES[i],
            price_length(next_seg, mode),
            mode,
            leg_bars=_seg_bar_span(next_seg),
        )
        if not ok:
            return False, i
    return True, -1


_3W_VERIFIER_PASS_FIXTURES = [
    pytest.param(
        [100.0, 130.0, 115.0, 145.0],
        PatternKind.THREE_NORMAL,
        id="3W_NORMAL",
    ),
    pytest.param(
        [100.0, 130.0, 80.0, 140.0],
        PatternKind.THREE_S2_LONGER,
        id="3W_S2_LONGER",
    ),
    pytest.param(
        [100.0, 130.0, 115.0, 123.0],
        PatternKind.THREE_S3_SHORTER,
        id="3W_S3_SHORTER",
    ),
    pytest.param(
        [100.0, 130.0, 80.0, 120.0],
        PatternKind.THREE_S2_LONGER_S3_SHORTER,
        id="3W_S2_LONGER_S3_SHORTER",
    ),
]


@pytest.mark.parametrize("prices,expected_kind", _3W_VERIFIER_PASS_FIXTURES)
def test_3w_gate_accepts_every_leg_when_verifier_accepts(
    prices: list[float],
    expected_kind: PatternKind,
) -> None:
    segs = make_segments(prices)
    result = verify_3wave(segs, "linear")
    assert result is not None and result[0] == expected_kind, (
        f"expected verifier to accept {expected_kind.value}; got {result}"
    )
    all_passed, fail_idx = _gate_accepts_every_leg("3W", segs, "linear")
    assert all_passed, (
        f"gate rejected leg {fail_idx} (role {_NON_LINK_ROLES[fail_idx].value}) "
        f"but verifier accepts the full pattern as {expected_kind.value} — "
        f"parser would have pruned this hypothesis pre-completion"
    )


def test_3w_gate_rejects_when_verifier_rejects_due_to_s3_floor() -> None:
    segs = make_segments([100.0, 130.0, 100.0, 105.0])
    assert verify_3wave(segs, "linear") is None
    all_passed, fail_idx = _gate_accepts_every_leg("3W", segs, "linear")
    assert not all_passed, "gate must reject when verifier rejects on R3 floor"
    assert fail_idx == 2, f"expected gate to fail at S3 (index 2); got {fail_idx}"


_5WT_VERIFIER_PASS_FIXTURES = [
    pytest.param(
        dict(L1=30, L2=15, L3=60, L4=20, L5=45, s2_weeks=2, s3_weeks=2, s4_weeks=2, s5_weeks=1),
        PatternKind.FIVE_TREND_S3_LONGEST,
        id="5W_TREND_S3_LONGEST",
    ),
    pytest.param(
        dict(L1=20, L2=10, L3=30, L4=15, L5=40, s2_weeks=2, s3_weeks=2, s4_weeks=2, s5_weeks=1),
        PatternKind.FIVE_TREND_S5_LONGEST,
        id="5W_TREND_S5_LONGEST",
    ),
    pytest.param(
        dict(L1=30, L2=15, L3=60, L4=40, L5=20, s2_weeks=2, s3_weeks=2, s4_weeks=2, s5_weeks=1),
        PatternKind.FIVE_TREND_S5_SHORTER,
        id="5W_TREND_S5_SHORTER",
    ),
    pytest.param(
        dict(L1=50, L2=20, L3=50, L4=25, L5=50, s2_weeks=2, s3_weeks=2, s4_weeks=2, s5_weeks=1),
        PatternKind.FIVE_TREND_EQUAL_PUSH,
        id="5W_TREND_EQUAL_PUSH",
    ),
]


@pytest.mark.parametrize("kwargs,expected_kind", _5WT_VERIFIER_PASS_FIXTURES)
def test_5wt_gate_accepts_every_leg_when_verifier_accepts(
    kwargs: dict,
    expected_kind: PatternKind,
) -> None:
    segs = build_5w_trend_segments(**kwargs)
    result = verify_5wave_trend(segs, "linear")
    assert result is not None and result[0] == expected_kind, (
        f"expected verifier to accept {expected_kind.value}; got {result}"
    )
    all_passed, fail_idx = _gate_accepts_every_leg("5W_TREND", segs, "linear")
    assert all_passed, (
        f"gate rejected leg {fail_idx} (role {_NON_LINK_ROLES[fail_idx].value}) "
        f"but verifier accepts as {expected_kind.value}"
    )


def test_5wt_gate_rejects_when_verifier_rejects_due_to_r6b() -> None:
    segs = build_5w_trend_segments(L1=30, L2=15, L3=40, L4=50, L5=30)
    assert verify_5wave_trend(segs, "linear") is None
    all_passed, fail_idx = _gate_accepts_every_leg("5W_TREND", segs, "linear")
    assert not all_passed
    assert fail_idx == 3, f"expected gate to fail at S4 (R6b); got fail_idx={fail_idx}"


def test_5wt_gate_rejects_when_verifier_rejects_due_to_r7() -> None:
    segs = build_5w_trend_segments(
        L1=30, L2=15, L3=60, L4=40, L5=10, s2_weeks=2, s3_weeks=2, s4_weeks=2
    )
    assert R7_S5_MIN_RATIO_5WT > 10 / 40
    assert verify_5wave_trend(segs, "linear") is None
    all_passed, fail_idx = _gate_accepts_every_leg("5W_TREND", segs, "linear")
    assert not all_passed
    assert fail_idx == 4, f"expected gate to fail at S5 (R7); got fail_idx={fail_idx}"


_5WS_VERIFIER_PASS_FIXTURES = [
    pytest.param(
        [100.0, 150.0, 110.0, 135.0, 115.0, 125.0],
        PatternKind.FIVE_SIDEWAY_CONTRACT,
        id="5W_SIDEWAY_CONTRACT",
    ),
    pytest.param(
        [100.0, 130.0, 110.0, 150.0, 125.0, 137.0],
        PatternKind.FIVE_SIDEWAY_BALANCE,
        id="5W_SIDEWAY_BALANCE",
    ),
    pytest.param(
        [100.0, 120.0, 105.0, 135.0, 110.0, 150.0],
        PatternKind.FIVE_SIDEWAY_EXPAND,
        id="5W_SIDEWAY_EXPAND",
    ),
]


@pytest.mark.parametrize("prices,expected_kind", _5WS_VERIFIER_PASS_FIXTURES)
def test_5ws_gate_accepts_every_leg_when_verifier_accepts(
    prices: list[float],
    expected_kind: PatternKind,
) -> None:
    segs = make_segments(prices)
    result = verify_5wave_sideway(segs, "linear")
    assert result is not None and result[0] == expected_kind, (
        f"expected verifier to accept {expected_kind.value}; got {result}"
    )
    all_passed, fail_idx = _gate_accepts_every_leg("5W_SIDEWAY", segs, "linear")
    assert all_passed, (
        f"gate rejected leg {fail_idx} (role {_NON_LINK_ROLES[fail_idx].value}) "
        f"but verifier accepts as {expected_kind.value}"
    )


def test_5ws_gate_rejects_when_s2_outside_window() -> None:
    segs = make_segments([100.0, 200.0, 170.0, 250.0, 200.0, 240.0])
    assert verify_5wave_sideway(segs, "linear") is None
    all_passed, fail_idx = _gate_accepts_every_leg("5W_SIDEWAY", segs, "linear")
    assert not all_passed
    assert fail_idx == 1, f"expected gate to fail at S2 (R2); got fail_idx={fail_idx}"


def test_gate_returns_true_for_unknown_family() -> None:
    seg_pivot_a = make_segments([100.0, 130.0])[0].start
    seg_pivot_b = make_segments([100.0, 130.0])[0].end
    leg = _Leg(role=WaveRole.S1, span_start=seg_pivot_a, span_end=seg_pivot_b)
    ctx = _Context(family="UNKNOWN_FAMILY", legs=[leg])
    assert _incremental_ok(ctx, WaveRole.S2, 30.0, "linear", leg_bars=1) is True
