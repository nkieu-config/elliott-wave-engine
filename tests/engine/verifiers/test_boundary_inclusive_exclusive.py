from __future__ import annotations

import pytest

from engine.types import PatternKind, WaveNode, WaveRole
from engine.verifiers import (
    verify_3wave,
    verify_5wave_sideway,
    verify_5wave_trend,
)
from tests.engine.verifiers._link_helpers import (
    build_3w_group as _build_3w_group,
)
from tests.engine.verifiers._link_helpers import (
    call_verify_link_s as verify_link_s,
)
from tests.engine.verifiers._link_helpers import (
    call_verify_link_t as verify_link_t,
)
from tests.engine.verifiers._link_helpers import (
    g2_after_link as _g2_after_link,
)
from tests.engine.verifiers._link_helpers import (
    link_segment as _link_segment,
)
from tests.fixtures import build_5w_trend_segments, make_segments

_trend_up = build_5w_trend_segments

# Sentinel meaning "accept but don't check pattern kind".
_ANY = "any"


def _assert_result(result: object, expected: object) -> None:
    if expected is None:
        assert result is None
    elif expected == _ANY:
        assert result is not None
    else:
        assert result is not None
        assert result[0] == expected  # type: ignore[index]


@pytest.mark.parametrize(
    "lengths, expected",
    [
        ((40, 20, 20, 15, 30), None),
        ((40, 20, 20.01, 15, 18), _ANY),
        ((30, 30, 60, 25, 40), None),
        ((30, 29.99, 60, 25, 40), _ANY),
        ((40, 20, 60, 60, 40), None),
        ((40, 20, 60, 59.99, 40), _ANY),
        ((40, 20, 80, 50, 20), _ANY),
        ((40, 20, 80, 50, 19.0), None),
        ((50, 20, 52.5, 25, 50), PatternKind.FIVE_TREND_EQUAL_PUSH),
        ((50, 20, 53, 25, 50), PatternKind.FIVE_TREND_S3_LONGEST),
    ],
    ids=[
        "r4_strict_rejects_s3_equal_s2",
        "r4_passes_when_s3_just_above_s2",
        "r6a_strict_rejects_s2_equal_s1",
        "r6a_passes_when_s2_just_below_s1",
        "r6b_strict_rejects_s4_equal_s3",
        "r6b_passes_when_s4_just_below_s3",
        "r7_just_above_0382_passes",
        "r7_rejects_just_below_0382",
        "equal_push_at_tolerance_boundary",
        "equal_push_just_above_tolerance_is_s3_longest",
    ],
)
def test_trend_boundaries(lengths: tuple[float, ...], expected: object) -> None:
    _assert_result(verify_5wave_trend(_trend_up(*lengths), "linear"), expected)


@pytest.mark.parametrize(
    "lengths, expected",
    [
        ((100, 50, 60, 50, 30), _ANY),
        ((100, 260, 300, 200, 50), _ANY),
        ((100, 270, 300, 200, 50), None),
        ((100, 49, 60, 50, 30), None),
        ((100, 100, 99, 80, 50), PatternKind.FIVE_SIDEWAY_CONTRACT),
        ((100, 100, 99.5, 80, 50), None),
        ((100, 100, 100, 80, 50), None),
        ((100, 100, 100.1, 80, 50), PatternKind.FIVE_SIDEWAY_BALANCE),
        ((150, 120, 90, 100, 99), PatternKind.FIVE_SIDEWAY_CONTRACT),
        ((150, 120, 90, 100, 99.5), None),
        ((100, 80, 120, 100, 100.1), PatternKind.FIVE_SIDEWAY_EXPAND),
    ],
    ids=[
        "common_s2_at_lower_05_passes",
        "common_s2_just_below_upper_2618_passes",
        "common_s2_just_above_upper_rejects",
        "common_s2_just_below_lower_rejects",
        "contract_s3_at_upper_099_passes",
        "dead_zone_r_s3_above_099_below_10_rejects",
        "dead_zone_r_s3_exactly_10_rejects",
        "balance_just_above_10_passes",
        "contract_s5_at_upper_099_passes",
        "dead_zone_r_s5_above_099_rejects",
        "expand_just_above_10_passes",
    ],
)
def test_sideway_boundaries(lengths: tuple[float, ...], expected: object) -> None:
    _assert_result(verify_5wave_sideway(_trend_up(*lengths), "linear"), expected)


@pytest.mark.parametrize(
    "prices, expected",
    [
        ([100, 200, 199, 250], _ANY),
        ([100, 110, 84, 200], _ANY),
        ([100, 110, 83.7, 200], None),
        ([100, 1100, 1095, 1200], None),
        ([100, 200, 100, 124], _ANY),
        ([100, 200, 100, 123.5], None),
        ([100, 130, 100, 150], PatternKind.THREE_NORMAL),
        ([100, 150, 120, 150], PatternKind.THREE_NORMAL),
    ],
    ids=[
        "r2_at_lower_001_passes",
        "r2_just_below_upper_2618_passes",
        "r2_just_above_2618_rejects",
        "r2_just_below_001_rejects",
        "r3_just_above_0236_passes",
        "r3_just_below_0236_rejects",
        "subtype_s2_equal_s1_is_normal_not_longer",
        "subtype_s3_equal_s2_is_normal_not_shorter",
    ],
)
def test_3w_boundaries(prices: list[float], expected: object) -> None:
    _assert_result(verify_3wave(make_segments(prices), "linear"), expected)


@pytest.mark.parametrize(
    "link_end, g2_legs, expected",
    [
        (125, (15, 8, 20), None),
        (125, (15.01, 8, 20), _ANY),
        (140 - 18.54, (40, 15, 30), _ANY),
        (140 - 18.6, (40, 15, 30), None),
        (140 - 0.3, (40, 15, 30), _ANY),
    ],
    ids=[
        "r7_strict_rejects_s1_equal_link",
        "r7_passes_when_s1_just_above_link",
        "r8_at_upper_0618_passes",
        "r8_just_above_0618_rejects",
        "r8_at_lower_001_passes",
    ],
)
def test_link_t_boundaries(
    link_end: float, g2_legs: tuple[float, float, float], expected: object
) -> None:
    g1 = _build_3w_group([100, 130, 110, 140])
    link = _link_segment(g1.segments[-1].end, end_price=link_end)
    g2 = _g2_after_link(link, leg_lengths=g2_legs)
    _assert_result(verify_link_t([g1, g2], [link], "linear"), expected)


def _build_node(prices: list[float], kind: PatternKind) -> WaveNode:
    segs = make_segments(prices)
    return WaveNode(
        role=WaveRole.SET_1,
        span_start=segs[0].start,
        pattern_kind=kind,
        segments=segs,
        span_end=segs[-1].end,
    )


_CONTRACT_G1_PRICES = [100, 200, 120, 175, 135, 160]
_THREE_KIND = PatternKind.THREE_NORMAL
_CONTRACT_KIND = PatternKind.FIVE_SIDEWAY_CONTRACT


@pytest.mark.parametrize(
    "g1_prices, g1_kind, link_end, g2_prices, expected",
    [
        ([100, 130, 110, 140], _THREE_KIND, 140 - 32, [108, 138, 118, 145], PatternKind.LINK_S),
        ([100, 130, 110, 140], _THREE_KIND, 140 - 31.4, [108.6, 138, 118, 145], None),
        (_CONTRACT_G1_PRICES, _CONTRACT_KIND, 160 - 101, [59, 89, 69, 99], _ANY),
        (_CONTRACT_G1_PRICES, _CONTRACT_KIND, 160 - 100.5, [60, 90, 70, 100], None),
        ([100, 130, 110, 140], _THREE_KIND, 140 - 64.72, [76, 105, 85, 115], PatternKind.LINK_S),
        ([100, 130, 110, 140], _THREE_KIND, 140 - 64.8, [76, 105, 85, 115], PatternKind.LINK_SE),
    ],
    ids=[
        "3w_just_above_floor_0786_passes",
        "3w_just_below_floor_rejects",
        "contract_at_floor_101_passes",
        "contract_just_below_101_rejects",
        "se_at_exactly_1618_stays_link_s",
        "se_just_above_1618_promotes",
    ],
)
def test_link_s_boundaries(
    g1_prices: list[float],
    g1_kind: PatternKind,
    link_end: float,
    g2_prices: list[float],
    expected: object,
) -> None:
    g1 = _build_node(g1_prices, g1_kind)
    link = _link_segment(g1.segments[-1].end, end_price=link_end)
    g2 = _build_3w_group(g2_prices)
    _assert_result(verify_link_s([g1, g2], [link], "linear"), expected)
