from __future__ import annotations

from engine import constants


def test_fib_pure_values_pinned_to_theory() -> None:
    assert constants.FIB_236 == 0.236
    assert constants.FIB_382 == 0.382
    assert constants.FIB_500 == 0.500
    assert constants.FIB_618 == 0.618
    assert constants.FIB_786 == 0.786
    assert constants.FIB_1618 == 1.618
    assert constants.FIB_2618 == 2.618


def test_3w_rule_aliases_match_theory() -> None:
    assert constants.R2_S2_MIN_RATIO_3W == 0.01
    assert constants.R2_S2_MAX_RATIO_3W == constants.FIB_2618
    assert constants.R3_S3_MIN_RATIO_3W == constants.FIB_236


def test_5w_trend_rule_aliases_match_theory() -> None:
    assert constants.R7_S5_MIN_RATIO_5WT == constants.FIB_382


def test_5w_sideway_rule_aliases_match_theory() -> None:
    assert constants.R2_S2_MIN_RATIO_5WS == constants.FIB_500
    assert constants.R2_S2_MAX_RATIO_5WS == constants.FIB_2618
    assert constants.R3_S4_MIN_RATIO_5WS == constants.FIB_500
    assert constants.R3_S4_MAX_RATIO_5WS == constants.FIB_2618


def test_5w_sideway_subtype_boundaries_match_theory() -> None:
    assert constants.R4_S3_MIN_CONTRACT_5WS == constants.FIB_500
    assert constants.R4_S3_MAX_CONTRACT_5WS == 0.99
    assert constants.R5_S5_MIN_CONTRACT_5WS == constants.FIB_236
    assert constants.R5_S5_MAX_CONTRACT_5WS == 0.99
    assert constants.SIDEWAY_EXPAND_BOUNDARY == 1.0


def test_link_t_rule_aliases_match_theory() -> None:
    assert constants.R8_LINK_MIN_RATIO_LINK_T == 0.01
    assert constants.R8_LINK_MAX_RATIO_LINK_T == constants.FIB_618
    assert constants.R9_LINK_TIME_MULTIPLIER_LINK_T == 2.0


def test_link_s_rule_aliases_match_theory() -> None:
    assert constants.R3_LINK_MIN_3W_LINK_S == constants.FIB_786
    assert constants.R3_LINK_MIN_EXPAND_LINK_S == constants.FIB_786
    assert constants.R3_LINK_MIN_5WS_LINK_S == 1.01
    assert constants.R5_LINK_SE_THRESHOLD_LINK_S == constants.FIB_1618


def test_degree_constants_match_theory() -> None:
    assert constants.DEGREE_GANN_FLOOR_RATIO == 1.0 / 3.0
    assert constants.DEGREE_GANN_CEILING_RATIO == 3.0
    assert constants.DEGREE_GANN_FLOOR_DIVISOR == 3
    assert round(1 / constants.DEGREE_GANN_FLOOR_RATIO) == constants.DEGREE_GANN_FLOOR_DIVISOR


def test_pivot_detection_defaults_pinned() -> None:
    assert constants.MIN_BARS_BETWEEN_DEFAULT == 1
    assert constants.ZIGZAG_ATR_PERIOD_DEFAULT == 14
    assert constants.ZIGZAG_ATR_MULTIPLIER_DEFAULT == 3.0
    assert constants.ZIGZAG_ATR_FLOOR_DEFAULT == 0.10


def test_equal_within_tolerance_pinned() -> None:
    assert constants.EQUAL_WITHIN_DEFAULT_TOLERANCE == 0.05
