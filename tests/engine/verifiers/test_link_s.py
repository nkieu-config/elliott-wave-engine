from __future__ import annotations

import pytest

from engine.types import PatternKind, WaveNode, WaveRole
from tests.engine.verifiers._link_helpers import (
    build_3w_group as _build_3w_group,
)
from tests.engine.verifiers._link_helpers import (
    call_verify_link_s as verify_link_s,
)
from tests.engine.verifiers._link_helpers import (
    link_segment as _link_segment,
)
from tests.fixtures import make_segments


def _build_group(prices: list[float], kind: PatternKind) -> WaveNode:
    segs = make_segments(prices)
    return WaveNode(
        role=WaveRole.SET_1,
        span_start=segs[0].start,
        pattern_kind=kind,
        segments=segs,
        span_end=segs[-1].end,
    )


# Each parametrize row is (g1_prices, g1_kind, link_end_price, g2_prices, g2_kind, expected)
# where expected is the PatternKind of the link result, or None for rejection.
@pytest.mark.parametrize(
    "g1_prices, g1_kind, link_end, g2_prices, g2_kind, expected",
    [
        ([100, 130, 110, 140], PatternKind.THREE_NORMAL, 140 - 35,
         [105, 135, 115, 140], PatternKind.THREE_NORMAL, PatternKind.LINK_S),
        ([100, 130, 110, 140], PatternKind.THREE_NORMAL, 140 - 70,
         [70, 100, 80, 110], PatternKind.THREE_NORMAL, PatternKind.LINK_SE),
        ([100, 200, 120, 175, 135, 160], PatternKind.FIVE_SIDEWAY_CONTRACT, 160 - 110,
         [50, 80, 60, 90], PatternKind.THREE_NORMAL, PatternKind.LINK_S),
        ([100, 120, 105, 140, 115, 170], PatternKind.FIVE_SIDEWAY_EXPAND, 170 - 50,
         [120, 150, 130, 160], PatternKind.THREE_NORMAL, PatternKind.LINK_S),
        ([100, 130, 110, 140], PatternKind.THREE_NORMAL, 140 - 20,
         [120, 150, 130, 160], PatternKind.THREE_NORMAL, None),
        ([100, 120, 110, 145, 130, 160], PatternKind.FIVE_TREND_S3_LONGEST, 130,
         [130, 160, 140, 170], PatternKind.THREE_NORMAL, None),
        ([100, 200, 120, 175, 135, 160], PatternKind.FIVE_SIDEWAY_CONTRACT, 160 - 90,
         [70, 100, 80, 110], PatternKind.THREE_NORMAL, None),
        ([100, 130, 110, 140], PatternKind.THREE_NORMAL, 175,
         [175, 205, 185, 215], PatternKind.THREE_NORMAL, None),
        ([100, 130, 60, 75], PatternKind.THREE_S2_LONGER, 135,
         [135, 165, 145, 175], PatternKind.THREE_NORMAL, None),
    ],
    ids=[
        "two_3w_groups_link_s",
        "two_3w_groups_link_se_over_1618",
        "5w_sideway_contract_link_s",
        "5w_sideway_expand_link_s",
        "reject_link_too_small",
        "reject_5w_trend_group",
        "reject_link_below_min_for_contract",
        "reject_link_same_direction_as_trend",
        "reject_link_same_direction_when_first_set_net_flips",
    ],
)
def test_link_s_scenarios(
    g1_prices: list[float],
    g1_kind: PatternKind,
    link_end: float,
    g2_prices: list[float],
    g2_kind: PatternKind,
    expected: PatternKind | None,
) -> None:
    g1 = _build_group(g1_prices, g1_kind)
    g2 = _build_group(g2_prices, g2_kind)
    link = _link_segment(g1.segments[-1].end, end_price=link_end)
    result = verify_link_s([g1, g2], [link], "linear")
    if expected is None:
        assert result is None
    else:
        assert result is not None
        assert result[0] == expected


def test_reject_only_one_group() -> None:
    g1 = _build_3w_group([100, 130, 110, 140])
    assert verify_link_s([g1], [], "linear") is None


def test_reject_4_groups() -> None:
    groups = [
        _build_3w_group([i * 10 + 100, i * 10 + 130, i * 10 + 110, i * 10 + 140]) for i in range(4)
    ]
    links = [
        _link_segment(groups[i].segments[-1].end, groups[i + 1].segments[0].start.price)
        for i in range(3)
    ]
    assert verify_link_s(groups, links, "linear") is None
