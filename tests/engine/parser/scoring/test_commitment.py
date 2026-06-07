from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from engine.parser.runtime import RuntimeContext
from engine.parser.scoring import _score_components
from engine.parser.scoring.components import (
    _commitment_factor,
    _score_components_for_display,
)
from engine.parser.scoring_config import ScoringConfig
from engine.parser.types import _Context, _Hypothesis, _Leg
from engine.types import Bar, PatternKind, WaveRole
from tests.engine.parser.scoring._helpers import _leg


def _hyp(family: str, legs: list[_Leg]) -> _Hypothesis:
    root = _Context(family=family, legs=list(legs))
    return _Hypothesis(id=str(uuid.uuid4()), context_stack=[root])


def _rt() -> RuntimeContext:
    return RuntimeContext.from_bars(None)


class TestCommitmentFactor:
    @pytest.mark.parametrize(
        "n,expected", [(1, 0.2), (2, 0.4), (3, 0.6), (4, 0.8), (5, 1.0)]
    )
    def test_5w_trend_target_is_five(self, n, expected):
        legs = [_leg((100, i), (101, i + 1)) for i in range(n)]
        h = _hyp("5W_TREND", legs)
        assert _commitment_factor(h) == pytest.approx(expected)

    def test_5w_sideway_target_is_five(self):
        h = _hyp("5W_SIDEWAY", [_leg((100, 0), (101, 1))])
        assert _commitment_factor(h) == pytest.approx(0.2)

    @pytest.mark.parametrize(
        "n,expected", [(1, 1 / 3), (2, 2 / 3), (3, 1.0)],
        ids=["1_of_3", "2_of_3", "3_of_3"],
    )
    def test_3w_target_is_three(self, n, expected):
        legs = [_leg((100, i), (101, i + 1)) for i in range(n)]
        h = _hyp("3W", legs)
        assert _commitment_factor(h) == pytest.approx(expected)

    def test_link_families_target_is_three(self):
        for fam in ("LINK_T", "LINK_S", "LINK_SE"):
            legs = [_leg((100, i), (101, i + 1)) for i in range(3)]
            h = _hyp(fam, legs)
            assert _commitment_factor(h) == pytest.approx(1.0)

    def test_link_3_group_caps_at_one(self):
        legs = [_leg((100, i), (101, i + 1)) for i in range(5)]
        h = _hyp("LINK_T", legs)
        assert _commitment_factor(h) == pytest.approx(1.0)

    def test_empty_root_returns_zero(self):
        h = _hyp("LINK_T", [])
        assert _commitment_factor(h) == 0.0


class TestCommitmentCurve:
    def test_linear_curve_is_default(self):
        h = _hyp("5W_TREND", [_leg((100, 0), (101, 1))])
        assert _commitment_factor(h) == pytest.approx(0.2)
        assert _commitment_factor(h, curve="linear") == pytest.approx(0.2)

    def test_sqrt_curve_softens_early_stage(self):
        h = _hyp("5W_TREND", [_leg((100, 0), (101, 1))])
        from math import sqrt
        assert _commitment_factor(h, curve="sqrt") == pytest.approx(sqrt(0.2))

    def test_off_curve_returns_one_regardless_of_legs(self):
        h_single = _hyp("5W_TREND", [_leg((100, 0), (101, 1))])
        assert _commitment_factor(h_single, curve="off") == 1.0
        h_empty = _hyp("LINK_T", [])
        assert _commitment_factor(h_empty, curve="off") == 1.0

    def test_curves_agree_at_full_commitment(self):
        h = _hyp("3W", [_leg((100, i), (101, i + 1)) for i in range(3)])
        for curve in ("linear", "sqrt", "off"):
            assert _commitment_factor(h, curve=curve) == pytest.approx(1.0)

    def test_curve_threaded_from_scoring_config(self):
        h = _hyp("5W_TREND", [_leg((100, 0), (101, 1))])

        rt_linear = RuntimeContext.from_bars(
            None, scoring=ScoringConfig(commitment_curve="linear"),
        )
        rt_off = RuntimeContext.from_bars(
            None, scoring=ScoringConfig(commitment_curve="off"),
        )
        c_linear = _score_components_for_display(h, "linear", runtime=rt_linear)
        c_off = _score_components_for_display(h, "linear", runtime=rt_off)
        assert c_linear["commitment"] == pytest.approx(0.2)
        assert c_off["commitment"] == 1.0


class TestEdgeCases:
    def test_unknown_family_falls_back_to_default_target(self):
        h = _hyp("WAT_NEW_FAMILY", [_leg((100, 0), (101, 1))])  # type: ignore[arg-type]
        assert h.root.min_legs_to_complete == 5
        assert _commitment_factor(h) == pytest.approx(0.2)

    def test_off_curve_with_empty_root_still_yields_zero_total(self):
        h = _hyp("LINK_T", [])
        rt = RuntimeContext.from_bars(
            None, scoring=ScoringConfig(commitment_curve="off"),
        )
        c = _score_components_for_display(h, "linear", runtime=rt)
        assert c["commitment"] == 1.0
        assert c["quality"] == 0.0
        assert c["total"] == 0.0

    def test_visual_quality_participates_in_commitment_weighting(self):
        h = _hyp("5W_TREND", [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (105, 15)),
        ])
        bars = [
            Bar(time=datetime(2020, 1, 1), open=100, high=101, low=99, close=100)
            for _ in range(30)
        ]
        rt = RuntimeContext.from_bars(bars, scoring=ScoringConfig())
        c = _score_components_for_display(h, "linear", runtime=rt)

        assert "visual_total" in c
        struct = c["structural_total"]
        vis = c["visual_total"]
        assert c["quality"] == pytest.approx(min(struct, vis))
        assert c["commitment"] == pytest.approx(0.4)
        assert c["total"] == pytest.approx(c["quality"] * c["commitment"])

    def test_pattern_kind_set_does_not_change_commitment(self):
        legs = [_leg((100, i), (110, i + 1)) for i in range(3)]
        h_open = _hyp("3W", legs)
        h_done = _hyp("3W", legs)
        h_done.root.final_kind = PatternKind.THREE_NORMAL
        assert _commitment_factor(h_open) == _commitment_factor(h_done)

    def test_curve_monotonic_in_root_legs(self):
        for curve in ("linear", "sqrt"):
            prev = -1.0
            for n in range(0, 6):
                legs = [_leg((100, i), (101, i + 1)) for i in range(n)]
                h = _hyp("5W_TREND", legs)
                v = _commitment_factor(h, curve=curve)
                assert v >= prev, (
                    f"{curve} curve non-monotonic: n={n} gave {v}, prev was {prev}"
                )
                prev = v


class TestDisplayScoringSurface:
    def test_components_include_quality_and_commitment(self):
        h = _hyp("3W", [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (105, 15)),
            _leg((105, 15), (115, 25)),
        ])
        c = _score_components_for_display(h, "linear", runtime=_rt())
        assert "quality" in c
        assert "commitment" in c
        assert "total" in c

    def test_total_equals_quality_times_commitment(self):
        h = _hyp("3W", [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (105, 15)),
            _leg((105, 15), (115, 25)),
        ])
        c = _score_components_for_display(h, "linear", runtime=_rt())
        assert c["total"] == pytest.approx(c["quality"] * c["commitment"])


class TestRanking:
    def test_complete_pattern_outranks_single_leg_with_pretty_slots(self):
        inner_3w_legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (105, 13)),
            _leg((105, 13), (115, 16)),
        ]
        set_1 = _Leg(
            role=WaveRole.SET_1,
            span_start=inner_3w_legs[0].span_start,
            span_end=inner_3w_legs[-1].span_end,
            pattern_kind=None,
            sub_legs=inner_3w_legs,
        )

        single_leg = _hyp("LINK_T", [set_1])
        c_single = _score_components_for_display(
            single_leg, "linear", runtime=_rt(),
        )

        complete = _hyp("3W", inner_3w_legs)
        c_complete = _score_components_for_display(
            complete, "linear", runtime=_rt(),
        )

        assert c_single["quality"] == pytest.approx(c_complete["quality"])
        assert c_complete["commitment"] == pytest.approx(1.0)
        assert c_single["commitment"] == pytest.approx(1 / 3)
        assert c_complete["total"] > c_single["total"]

    def test_more_legs_outrank_fewer_at_equal_quality(self):
        legs_4 = [_leg((100, i), (101, i + 1)) for i in range(4)]
        legs_2 = [_leg((100, i), (101, i + 1)) for i in range(2)]
        h4 = _hyp("5W_TREND", legs_4)
        h2 = _hyp("5W_TREND", legs_2)
        c4 = _score_components_for_display(h4, "linear", runtime=_rt())
        c2 = _score_components_for_display(h2, "linear", runtime=_rt())
        assert c4["quality"] == pytest.approx(c2["quality"])
        assert c4["commitment"] > c2["commitment"]
        assert c4["total"] > c2["total"]


class TestBeamUnaffected:
    def test_beam_components_have_no_commitment_or_quality_keys(self):
        h = _hyp("5W_TREND", [_leg((100, 0), (101, 1))])
        c = _score_components(h, "linear", runtime=_rt())
        assert "quality" not in c
        assert "commitment" not in c

    def test_beam_total_unaffected_by_family(self):
        totals = []
        for fam in ("3W", "5W_TREND", "LINK_T"):
            h = _hyp(fam, [_leg((100, 0), (110, 5)), _leg((110, 5), (105, 8))])
            c = _score_components(h, "linear", runtime=_rt())
            totals.append(c["total"])
        assert totals[0] == pytest.approx(totals[1]) == pytest.approx(totals[2])
