from __future__ import annotations

import pytest

from engine.adaptive import (
    ALL_FIVE_SIDEWAY,
    ALL_FIVE_TREND,
    ALL_LINK,
    ALL_PATTERNS,
    ALL_THREE,
    allowed_sub_families,
    allowed_sub_patterns,
    expected_direction,
    is_push_role,
)
from engine.types import PatternKind, WaveRole


def test_5w_trend_s1_no_s5_shorter_no_5w_sideway() -> None:
    allowed = allowed_sub_patterns("5W_TREND", WaveRole.S1)
    assert PatternKind.FIVE_TREND_S5_SHORTER not in allowed
    for k in ALL_FIVE_SIDEWAY:
        assert k not in allowed
    assert PatternKind.LINK_S not in allowed
    assert PatternKind.LINK_SE not in allowed
    assert PatternKind.THREE_S2_LONGER not in allowed
    assert PatternKind.THREE_S3_SHORTER not in allowed
    assert PatternKind.THREE_NORMAL in allowed
    assert PatternKind.LINK_T in allowed


def test_5w_trend_s5_allows_s5_shorter() -> None:
    allowed = allowed_sub_patterns("5W_TREND", WaveRole.S5)
    assert PatternKind.FIVE_TREND_S5_SHORTER in allowed
    for k in ALL_FIVE_SIDEWAY:
        assert k not in allowed


def test_5w_trend_pull_allows_everything() -> None:
    for role in (WaveRole.S2, WaveRole.S4):
        assert allowed_sub_patterns("5W_TREND", role) == ALL_PATTERNS


def test_5w_sideway_s5_allows_5w_sideway() -> None:
    s5 = allowed_sub_patterns("5W_SIDEWAY", WaveRole.S5)
    for k in ALL_FIVE_SIDEWAY:
        assert k in s5

    for role in (WaveRole.S1, WaveRole.S2, WaveRole.S3, WaveRole.S4):
        legs = allowed_sub_patterns("5W_SIDEWAY", role)
        for k in ALL_FIVE_SIDEWAY:
            assert k not in legs


def test_5w_sideway_no_link_s_anywhere() -> None:
    for role in (WaveRole.S1, WaveRole.S2, WaveRole.S3, WaveRole.S4, WaveRole.S5):
        allowed = allowed_sub_patterns("5W_SIDEWAY", role)
        assert PatternKind.LINK_S not in allowed
        assert PatternKind.LINK_SE not in allowed


def test_3w_push_no_5w_sideway_no_link_s() -> None:
    for role in (WaveRole.S1, WaveRole.S3):
        allowed = allowed_sub_patterns("3W", role)
        for k in ALL_FIVE_SIDEWAY:
            assert k not in allowed
        assert PatternKind.LINK_S not in allowed


def test_3w_pull_allows_everything() -> None:
    assert allowed_sub_patterns("3W", WaveRole.S2) == ALL_PATTERNS


def test_link_t_groups_must_be_3w() -> None:
    for role in (WaveRole.SET_1, WaveRole.SET_2, WaveRole.SET_3):
        allowed = allowed_sub_patterns("LINK_T", role)
        assert allowed == ALL_THREE


def test_link_t_link_segment_allows_anything() -> None:
    allowed = allowed_sub_patterns("LINK_T", WaveRole.LINK)
    assert allowed == ALL_PATTERNS


def test_link_s_groups_allow_3w_and_5w_sideway() -> None:
    for role in (WaveRole.SET_1, WaveRole.SET_2, WaveRole.SET_3):
        for fam in ("LINK_S", "LINK_SE"):
            allowed = allowed_sub_patterns(fam, role)
            assert allowed == frozenset(ALL_THREE | ALL_FIVE_SIDEWAY), (
                f"{fam} group at {role} got {allowed}"
            )


def test_link_s_link_segment_allows_5w_trend_3w_normal_link_t() -> None:
    for fam in ("LINK_S", "LINK_SE"):
        allowed = allowed_sub_patterns(fam, WaveRole.LINK)
        for k in ALL_FIVE_TREND:
            assert k in allowed
        assert PatternKind.THREE_NORMAL in allowed
        assert PatternKind.LINK_T in allowed
        for k in ALL_FIVE_SIDEWAY:
            assert k not in allowed
        assert PatternKind.THREE_S2_LONGER not in allowed
        assert PatternKind.LINK_S not in allowed
        assert PatternKind.LINK_SE not in allowed


def test_link_family_rejects_5w_leg_role() -> None:
    for role in (WaveRole.S1, WaveRole.S2, WaveRole.S3, WaveRole.S4, WaveRole.S5):
        with pytest.raises(ValueError, match="is not a leg of family"):
            allowed_sub_patterns("LINK_T", role)
        with pytest.raises(ValueError, match="is not a leg of family"):
            allowed_sub_patterns("LINK_S", role)


def test_allowed_sub_families_for_5w_trend_s1() -> None:
    fams = allowed_sub_families("5W_TREND", WaveRole.S1)
    assert "5W_TREND" in fams
    assert "3W" in fams
    assert "LINK_T" in fams
    assert "5W_SIDEWAY" not in fams
    assert "LINK_S" not in fams


def test_is_push_role() -> None:
    for role in (WaveRole.S1, WaveRole.S3, WaveRole.S5):
        assert is_push_role("5W_TREND", role)
        assert is_push_role("3W", role)
    for role in (WaveRole.S2, WaveRole.S4):
        assert not is_push_role("5W_TREND", role)


def test_is_push_role_link_groups_with_trend() -> None:
    for role in (WaveRole.SET_1, WaveRole.SET_2, WaveRole.SET_3):
        assert is_push_role("LINK_T", role)
        assert is_push_role("LINK_S", role)


def test_is_push_role_link_segment_is_pull() -> None:
    assert not is_push_role("LINK_T", WaveRole.LINK)
    assert not is_push_role("LINK_S", WaveRole.LINK)


def test_is_push_role_anchor_raises() -> None:
    with pytest.raises(ValueError, match="has no Push/Pull classification"):
        is_push_role("5W_TREND", WaveRole.ANCHOR)


def test_expected_direction_up_trend() -> None:
    assert expected_direction("5W_TREND", WaveRole.S1, "up") == "up"
    assert expected_direction("5W_TREND", WaveRole.S2, "up") == "down"
    assert expected_direction("5W_TREND", WaveRole.S3, "up") == "up"
    assert expected_direction("5W_TREND", WaveRole.S5, "up") == "up"


def test_expected_direction_down_trend() -> None:
    assert expected_direction("5W_TREND", WaveRole.S1, "down") == "down"
    assert expected_direction("5W_TREND", WaveRole.S2, "down") == "up"


def test_expected_direction_link_groups_with_trend() -> None:
    for role in (WaveRole.SET_1, WaveRole.SET_2, WaveRole.SET_3):
        assert expected_direction("LINK_T", role, "up") == "up"
        assert expected_direction("LINK_S", role, "down") == "down"


def test_expected_direction_link_connector_against_trend() -> None:
    assert expected_direction("LINK_T", WaveRole.LINK, "up") == "down"
    assert expected_direction("LINK_S", WaveRole.LINK, "down") == "up"


def test_expected_direction_rejects_anchor_role() -> None:
    with pytest.raises(ValueError, match="has no Push/Pull classification"):
        expected_direction("5W_TREND", WaveRole.ANCHOR, "up")


def test_unknown_family_raises() -> None:
    with pytest.raises(ValueError, match="unknown family"):
        allowed_sub_patterns("UNKNOWN", WaveRole.S1)


def test_all_patterns_count() -> None:
    assert ALL_PATTERNS == ALL_FIVE_TREND | ALL_FIVE_SIDEWAY | ALL_THREE | ALL_LINK
    assert len(ALL_PATTERNS) == 15
