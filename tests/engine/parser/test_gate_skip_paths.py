from __future__ import annotations

from engine.helpers import bar_span
from engine.parser.families import incremental_ok as _incremental_ok
from engine.parser.gates import (
    _bar_span,
    _five_trend_s4_degree_ok,
    _link_t_link_degree_ok,
)
from engine.parser.types import _Context, _Leg
from engine.types import WaveRole
from tests.fixtures import ip_pivot, ip_pivot_no_bar


def test_bar_span_returns_none_when_start_missing() -> None:
    p_no = ip_pivot_no_bar(0, 0, 100.0, "low")
    p_yes = ip_pivot(1, 5, 110.0, "high")
    assert bar_span(p_no, p_yes) is None


def test_bar_span_returns_none_when_end_missing() -> None:
    p_yes = ip_pivot(0, 0, 100.0, "low")
    p_no = ip_pivot_no_bar(1, 5, 110.0, "high")
    assert bar_span(p_yes, p_no) is None


def test_bar_span_returns_abs_difference_when_both_set() -> None:
    p_a = ip_pivot(0, 3, 100.0, "low")
    p_b = ip_pivot(1, 8, 110.0, "high")
    assert bar_span(p_a, p_b) == 5
    assert bar_span(p_b, p_a) == 5


def test_gates_bar_span_propagates_none() -> None:
    p_yes = ip_pivot(0, 0, 100.0, "low")
    p_no = ip_pivot_no_bar(1, 5, 110.0, "high")
    assert _bar_span(p_yes, p_no) is None
    assert _bar_span(p_no, p_yes) is None


def test_five_trend_s4_degree_ok_skips_when_s4_bars_none() -> None:
    ctx = _Context(
        family="5W_TREND",
        legs=[
            _Leg(WaveRole.S1, ip_pivot(0, 0, 100.0, "low"), ip_pivot(1, 1, 130.0, "high")),
            _Leg(WaveRole.S2, ip_pivot(1, 1, 130.0, "high"), ip_pivot(2, 3, 110.0, "low")),
            _Leg(WaveRole.S3, ip_pivot(2, 3, 110.0, "low"), ip_pivot(3, 4, 175.0, "high")),
        ],
    )
    assert _five_trend_s4_degree_ok(ctx, s4_bars=None) is True


def test_five_trend_s4_degree_ok_skips_when_s2_or_s3_missing_bar_index() -> None:
    ctx = _Context(
        family="5W_TREND",
        legs=[
            _Leg(WaveRole.S1, ip_pivot(0, 0, 100.0, "low"), ip_pivot(1, 1, 130.0, "high")),
            _Leg(
                WaveRole.S2,
                ip_pivot_no_bar(1, 1, 130.0, "high"),
                ip_pivot_no_bar(2, 3, 110.0, "low"),
            ),
            _Leg(WaveRole.S3, ip_pivot(2, 3, 110.0, "low"), ip_pivot(3, 4, 175.0, "high")),
        ],
    )
    assert _five_trend_s4_degree_ok(ctx, s4_bars=2) is True


def test_link_t_link_degree_ok_skips_when_link_bars_none() -> None:
    ctx = _Context(family="LINK_T", legs=[])
    assert _link_t_link_degree_ok(ctx, link_bars=None) is True


def test_link_t_link_degree_ok_skips_when_no_legs() -> None:
    ctx = _Context(family="LINK_T", legs=[])
    assert _link_t_link_degree_ok(ctx, link_bars=10) is True


def test_link_t_link_degree_ok_skips_when_first_group_lacks_s2() -> None:
    g1 = _Leg(
        WaveRole.SET_1,
        ip_pivot(0, 0, 100.0, "low"),
        ip_pivot(1, 5, 130.0, "high"),
        sub_legs=[
            _Leg(WaveRole.S1, ip_pivot(0, 0, 100.0, "low"), ip_pivot(1, 5, 130.0, "high")),
        ],
    )
    ctx = _Context(family="LINK_T", legs=[g1])
    assert _link_t_link_degree_ok(ctx, link_bars=10) is True


def test_link_t_link_degree_ok_skips_when_g1_s2_missing_bar_index() -> None:
    g1 = _Leg(
        WaveRole.SET_1,
        ip_pivot(0, 0, 100.0, "low"),
        ip_pivot(3, 6, 130.0, "high"),
        sub_legs=[
            _Leg(WaveRole.S1, ip_pivot(0, 0, 100.0, "low"), ip_pivot(1, 1, 130.0, "high")),
            _Leg(
                WaveRole.S2,
                ip_pivot_no_bar(1, 1, 130.0, "high"),
                ip_pivot_no_bar(2, 3, 110.0, "low"),
            ),
            _Leg(WaveRole.S3, ip_pivot(2, 3, 110.0, "low"), ip_pivot(3, 6, 130.0, "high")),
        ],
    )
    ctx = _Context(family="LINK_T", legs=[g1])
    assert _link_t_link_degree_ok(ctx, link_bars=10) is True


def test_incremental_ok_5w_trend_bar_index_none_passes_when_price_ok() -> None:
    ctx = _Context(
        family="5W_TREND",
        legs=[
            _Leg(WaveRole.S1, ip_pivot(0, 0, 100.0, "low"), ip_pivot(1, 1, 130.0, "high")),
            _Leg(WaveRole.S2, ip_pivot(1, 1, 130.0, "high"), ip_pivot(2, 3, 110.0, "low")),
            _Leg(WaveRole.S3, ip_pivot(2, 3, 110.0, "low"), ip_pivot(3, 4, 160.0, "high")),
        ],
    )
    assert (
        _incremental_ok(
            ctx,
            WaveRole.S4,
            leg_length=40.0,
            mode="linear",
            leg_bars=None,
        )
        is True
    )
