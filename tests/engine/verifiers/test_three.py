from __future__ import annotations

import pytest

from engine.constants import FIB_236, FIB_2618
from engine.types import PatternKind
from engine.verifiers import verify_3wave
from tests.fixtures import make_segments

# Sentinel meaning "accept (result is not None) but don't check pattern kind".
_ANY = "any"


def test_3w_normal_up() -> None:
    segs = make_segments([100, 130, 115, 145])
    result = verify_3wave(segs, "linear")
    assert result is not None
    kind, rules = result
    assert kind == PatternKind.THREE_NORMAL
    assert all(r.passed for r in rules)


@pytest.mark.parametrize(
    "prices, expected",
    [
        ([100, 120, 80, 130], PatternKind.THREE_S2_LONGER),
        ([100, 130, 110, 120], PatternKind.THREE_S3_SHORTER),
        ([100, 120, 90, 100], PatternKind.THREE_S2_LONGER_S3_SHORTER),
        ([200, 150, 170, 130], PatternKind.THREE_NORMAL),
        ([100.0, 1100.0, 1095.0, 1200.0], None),
        ([100, 110, 80, 100], None),
        ([100, 130, 110, 113], None),
        ([100, 130, 110, 114.6], None),
        ([100, 200, 199, 250], _ANY),
        ([100, 110, 84, 200], _ANY),
        ([100, 130, 110, 114.8], _ANY),
    ],
    ids=[
        "kind_s2_longer",
        "kind_s3_shorter",
        "kind_s2_longer_and_s3_shorter",
        "kind_down_direction_normal",
        "reject_s2_too_short",
        "reject_s2_too_long",
        "reject_s3_too_short",
        "reject_just_outside_lower_s3_threshold",
        "accept_r_s2_s1_equals_lower",
        "accept_r_s2_s1_just_inside_upper",
        "accept_r_s3_s2_just_inside_threshold",
    ],
)
def test_verify_3wave_accepts_and_rejects(prices: list[float], expected: object) -> None:
    result = verify_3wave(make_segments(prices), "linear")
    if expected is None:
        assert result is None
    elif expected == _ANY:
        assert result is not None
    else:
        assert result is not None
        assert result[0] == expected


def test_reject_not_3_segments() -> None:
    segs = make_segments([100, 120])
    assert verify_3wave(segs, "linear") is None
    segs = make_segments([100, 120, 110, 130, 120])
    assert verify_3wave(segs, "linear") is None


def test_reject_not_alternating() -> None:
    from datetime import datetime, timedelta

    from engine.types import Pivot, Segment

    pivots = [
        Pivot(i, datetime(2020, 1, 1) + timedelta(weeks=i), 100 + i * 10, "low", i)
        for i in range(4)
    ]
    segs = [Segment(start=pivots[i], end=pivots[i + 1]) for i in range(3)]
    assert verify_3wave(segs, "linear") is None


def test_boundary_constants_decimal_form_unchanged() -> None:
    assert FIB_236 == 0.236
    assert FIB_2618 == 2.618


@pytest.mark.parametrize("mode", ["linear", "log"])
def test_3w_works_in_both_modes(mode: str) -> None:
    segs = make_segments([100, 130, 115, 145])
    result = verify_3wave(segs, mode)  # type: ignore[arg-type]
    assert result is not None


def test_log_mode_yields_different_measured_ratios_than_linear() -> None:
    segs = make_segments([100, 200, 150, 300])
    res_lin = verify_3wave(segs, "linear")
    res_log = verify_3wave(segs, "log")
    assert res_lin is not None and res_log is not None

    r2_lin = next(r.measured for r in res_lin[1] if r.id == "3w.r2.s2_in_range")
    r2_log = next(r.measured for r in res_log[1] if r.id == "3w.r2.s2_in_range")
    r3_lin = next(r.measured for r in res_lin[1] if r.id == "3w.r3.s3_min_size")
    r3_log = next(r.measured for r in res_log[1] if r.id == "3w.r3.s3_min_size")

    assert r2_lin == pytest.approx(0.5)
    assert r2_log == pytest.approx(0.415, abs=0.01)
    assert r3_lin == pytest.approx(3.0)
    assert r3_log == pytest.approx(2.409, abs=0.01)
    assert res_lin[0] == res_log[0] == PatternKind.THREE_NORMAL
