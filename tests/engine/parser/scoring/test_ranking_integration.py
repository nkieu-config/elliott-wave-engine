from __future__ import annotations

import pytest

from engine.parser import count_waves
from engine.types import Pivot, Segment
from tests.engine.parser._builders import piv


def _link_t_2_groups_fixture() -> tuple[list[Segment], Pivot]:
    p0 = piv(0, 100, "low", 0)
    p1 = piv(1, 130, "high", 1)
    p2 = piv(2, 115, "low", 2)
    p3 = piv(3, 145, "high", 3)
    p4 = piv(4, 130, "low", 6)
    p5 = piv(5, 160, "high", 7)
    p6 = piv(6, 145, "low", 8)
    p7 = piv(7, 175, "high", 9)
    pivs = [p0, p1, p2, p3, p4, p5, p6, p7]
    segs = [Segment(start=pivs[i], end=pivs[i + 1]) for i in range(7)]
    return segs, pivs[0]


@pytest.mark.slow
class TestRankingSanity:
    def test_top_scenario_has_meaningful_commitment(self) -> None:
        segs, anchor = _link_t_2_groups_fixture()
        report = count_waves(anchor, segs, "linear")
        assert report.scenarios, "fixture must produce scenarios"
        top = report.scenarios[0]
        commit = top.score_components.get("commitment", 0.0)
        assert commit >= 0.5, (
            f"Top scenario has commitment {commit:.3f} "
            f"(family={top.family}, sc.legs={len(top.legs)}, "
            f"is_complete={top.is_complete})"
        )

    def test_complete_pattern_appears_in_top_3(self) -> None:
        segs, anchor = _link_t_2_groups_fixture()
        report = count_waves(anchor, segs, "linear")
        top_3 = report.scenarios[:3]
        complete_in_top3 = [s for s in top_3 if s.is_complete and s.pattern_kind]
        assert complete_in_top3, (
            f"No complete pattern in top 3 — found: "
            f"{[(s.family, s.is_complete, s.pattern_kind) for s in top_3]}"
        )

    def test_link_t_complete_reaches_top_5(self) -> None:
        segs, anchor = _link_t_2_groups_fixture()
        report = count_waves(anchor, segs, "linear")
        top_5 = report.scenarios[:5]
        link_t_complete = [
            s for s in top_5
            if s.family == "LINK_T" and s.is_complete and s.pattern_kind
        ]
        assert link_t_complete, (
            f"Complete LINK_T missing from top 5 — top 5 = "
            f"{[(s.family, s.pattern_kind, s.is_complete) for s in top_5]}"
        )

    def test_no_zero_leg_root_scenario_in_top_5(self) -> None:
        segs, anchor = _link_t_2_groups_fixture()
        report = count_waves(anchor, segs, "linear")
        top_5 = report.scenarios[:5]
        zero_commit = [s for s in top_5 if s.score_components.get("commitment", 0.0) == 0.0]
        assert not zero_commit, (
            f"Zero-commitment scenario in top 5: "
            f"{[(s.family, s.score) for s in zero_commit]}"
        )

    def test_top_scenarios_have_quality_components_present(self) -> None:
        segs, anchor = _link_t_2_groups_fixture()
        report = count_waves(anchor, segs, "linear")
        for sc in report.scenarios[:5]:
            assert "quality" in sc.score_components, (
                f"scenario {sc.family}/{sc.pattern_kind} missing 'quality'"
            )
            assert "commitment" in sc.score_components, (
                f"scenario {sc.family}/{sc.pattern_kind} missing 'commitment'"
            )
