from __future__ import annotations

from datetime import datetime

import pytest

from engine.parser.runtime import RuntimeContext
from engine.parser.scoring import (
    STRUCTURAL_SLOTS,
    VISUAL_SLOTS,
    _score_components,
)
from engine.parser.types import _Leg
from engine.types import Bar, Pivot, WaveRole
from tests.fixtures import build_hypothesis_with_legs


@pytest.fixture
def _local_counter():
    return {"n": 0}


@pytest.fixture
def make_pivot(_local_counter):
    def _factory(price: float, bar: int) -> Pivot:
        idx = _local_counter["n"]
        _local_counter["n"] += 1
        return Pivot(
            index=idx,
            time=datetime(2020, 1, 1),
            price=price,
            kind="high",
            bar_index=bar,
        )

    return _factory


@pytest.fixture
def make_leg(make_pivot):
    def _factory(p0: tuple[float, int], p1: tuple[float, int]) -> _Leg:
        return _Leg(role=WaveRole.S1, span_start=make_pivot(*p0), span_end=make_pivot(*p1))

    return _factory


def _runtime_no_bars() -> RuntimeContext:
    return RuntimeContext.from_bars(None)


def _runtime_with_bars(n: int = 30) -> RuntimeContext:
    bars = [Bar(time=datetime(2020, 1, 1), open=100, high=101, low=99, close=100) for _ in range(n)]
    return RuntimeContext.from_bars(bars)


class TestScoreComponents:
    def test_returns_dict_with_all_struct_slot_keys(self, make_leg):
        h = build_hypothesis_with_legs(
            [
                make_leg((100, 0), (110, 10)),
                make_leg((110, 10), (105, 15)),
                make_leg((105, 15), (115, 25)),
            ]
        )
        components = _score_components(h, "linear", runtime=_runtime_no_bars())
        for slot in STRUCTURAL_SLOTS:
            assert slot in components
        assert "structural_total" in components
        assert "total" in components

    def test_visual_slots_absent_when_no_bars(self, make_leg):
        h = build_hypothesis_with_legs(
            [
                make_leg((100, 0), (110, 10)),
                make_leg((110, 10), (105, 15)),
            ]
        )
        c = _score_components(h, "linear", runtime=_runtime_no_bars())
        for slot in VISUAL_SLOTS:
            assert slot not in c
        assert "visual_total" not in c

    def test_visual_slots_present_when_bars_supplied(self, make_leg):
        h = build_hypothesis_with_legs(
            [
                make_leg((100, 0), (110, 10)),
                make_leg((110, 10), (105, 15)),
            ]
        )
        c = _score_components(h, "linear", runtime=_runtime_with_bars())
        for slot in VISUAL_SLOTS:
            assert slot in c
        assert "visual_total" in c

    def test_structural_total_is_min_over_active_struct_slots(self, make_leg):
        h = build_hypothesis_with_legs(
            [
                make_leg((100, 0), (110, 10)),
                make_leg((110, 10), (109, 12)),
                make_leg((109, 12), (119, 22)),
            ]
        )
        c = _score_components(h, "linear", runtime=_runtime_no_bars())
        active = [c[s] for s in STRUCTURAL_SLOTS if c.get(s) is not None]
        assert active, "At least one structural slot should be active"
        assert c["structural_total"] == pytest.approx(min(active))

    def test_total_equals_structural_when_bars_absent(self, make_leg):
        h = build_hypothesis_with_legs(
            [
                make_leg((100, 0), (110, 10)),
                make_leg((110, 10), (109, 12)),
                make_leg((109, 12), (119, 22)),
            ]
        )
        c = _score_components(h, "linear", runtime=_runtime_no_bars())
        assert "visual_total" not in c
        assert c["total"] == pytest.approx(c["structural_total"])

    def test_total_equals_min_of_dim_totals_when_both_active(self, make_leg):
        h = build_hypothesis_with_legs(
            [
                make_leg((100, 0), (110, 10)),
                make_leg((110, 10), (105, 15)),
                make_leg((105, 15), (115, 25)),
            ]
        )
        c = _score_components(h, "linear", runtime=_runtime_with_bars())
        assert "structural_total" in c
        assert "visual_total" in c
        assert c["total"] == pytest.approx(min(c["structural_total"], c["visual_total"]))

    def test_total_is_zero_when_all_structural_slots_inactive(self, make_leg):
        h = build_hypothesis_with_legs([make_leg((100, 0), (110, 10))])
        c = _score_components(h, "linear", runtime=_runtime_no_bars())
        for slot in STRUCTURAL_SLOTS:
            assert c.get(slot) is None or slot not in c
        assert c["total"] == 0.0
        assert c["structural_total"] == 0.0


def test_score_components_verbose_returns_intermediates(sample_hypothesis_with_bars):
    h, mode, runtime = sample_hypothesis_with_bars
    from engine.parser.scoring.components import _score_components_verbose

    out = _score_components_verbose(h, mode, runtime=runtime)
    assert "speed_cluster" in out
    assert "intermediates" in out
    inter = out["intermediates"]
    assert "speed_cluster" in inter
    assert "leg_speeds" in inter["speed_cluster"]
