from __future__ import annotations

import pytest

from engine.parser import Scenario, count_waves
from engine.types import OpenState, WaveNode
from tests.fixtures import make_segments

pytestmark = pytest.mark.slow


def test_scenario_has_required_fields() -> None:
    segs = make_segments([100, 130, 115, 175, 155, 200])
    report = count_waves(segs[0].start, segs, "linear")
    sc = report.scenarios[0]

    assert isinstance(sc, Scenario)
    assert isinstance(sc.root, WaveNode)
    assert isinstance(sc.open_state, OpenState)
    assert isinstance(sc.rules_log, list)

    # Deterministic for this fixture; catches wrong-but-typed regressions.
    assert isinstance(sc.id, str) and len(sc.id) == 16
    assert sc.score == pytest.approx(0.333, abs=1e-3)
    assert sc.family == "3W"
    assert len(sc.legs) == 2
    assert sc.open_state.current_role is None


def test_root_wavenode_has_proper_tree_structure() -> None:
    segs = make_segments([100, 130, 115, 175, 155, 200])
    report = count_waves(segs[0].start, segs, "linear")
    sc = next(s for s in report.scenarios if s.is_complete and s.family == "5W_TREND")

    root = sc.root
    assert root.nesting_level == 0
    assert root.parent is None
    assert len(root.children) == 5
    for _, child in enumerate(root.children):
        assert child.parent is root
        assert child.nesting_level == 1


def test_open_state_structure() -> None:
    segs = make_segments([100, 130])
    report = count_waves(segs[0].start, segs, "linear")
    sc = report.scenarios[0]

    os = sc.open_state
    assert os.current_role is not None
    assert isinstance(os.nesting_level, int)
    assert isinstance(os.next_expected, list)


def test_legs_property_returns_root_children() -> None:
    segs = make_segments([100, 130, 115, 175, 155, 200])
    report = count_waves(segs[0].start, segs, "linear")
    sc = report.scenarios[0]

    assert sc.legs is sc.root.children


def test_pattern_kind_returns_root_pattern_kind() -> None:
    segs = make_segments([100, 130, 115, 175, 155, 200])
    report = count_waves(segs[0].start, segs, "linear")
    sc = next(s for s in report.scenarios if s.is_complete)

    assert sc.pattern_kind is sc.root.pattern_kind


def test_is_complete_true_when_root_classified() -> None:
    segs = make_segments([100, 130, 115, 175, 155, 200])
    report = count_waves(segs[0].start, segs, "linear")
    complete = [sc for sc in report.scenarios if sc.is_complete]
    assert all(sc.root.span_end is not None for sc in complete)
    assert all(sc.root.pattern_kind is not None for sc in complete)


def test_open_role_proxies_to_open_state() -> None:
    segs = make_segments([100, 130])
    report = count_waves(segs[0].start, segs, "linear")
    sc = report.scenarios[0]

    assert sc.open_role == sc.open_state.current_role


def test_wavenode_direction_property() -> None:
    segs = make_segments([100, 130, 115, 175, 155, 200])
    report = count_waves(segs[0].start, segs, "linear")
    sc = next(s for s in report.scenarios if s.is_complete)

    for child in sc.root.children:
        assert child.direction in ("up", "down")


def test_wavenode_sub_legs_alias() -> None:
    segs = make_segments([100, 130, 115, 175, 155, 200])
    report = count_waves(segs[0].start, segs, "linear")
    sc = next(s for s in report.scenarios if s.is_complete)

    for child in sc.root.children:
        assert child.sub_legs is child.children


def test_count_waves_rejects_invalid_mode() -> None:
    segs = make_segments([100, 130, 115, 175, 155, 200])
    with pytest.raises(ValueError, match="mode must be 'linear' or 'log'"):
        count_waves(segs[0].start, segs, "logarithmic")  # type: ignore[arg-type]


def test_rule_result_is_frozen() -> None:
    from dataclasses import FrozenInstanceError

    from engine.types import RuleResult

    r = RuleResult(id="x.r1", passed=True, measured=1.0)
    with pytest.raises(FrozenInstanceError):
        r.passed = False  # type: ignore[misc]


def test_clone_isolates_branches_without_deepcopy() -> None:
    from datetime import datetime

    from engine.parser.types import _Context, _Hypothesis, _Leg
    from engine.types import Pivot, RuleResult, WaveRole

    p0 = Pivot(index=0, time=datetime(2020, 1, 1), price=100.0, kind="low")
    p1 = Pivot(index=1, time=datetime(2020, 1, 2), price=120.0, kind="high")
    nested = _Leg(role=WaveRole.S1, span_start=p0, span_end=p1)
    leg = _Leg(role=WaveRole.S1, span_start=p0, span_end=p1, sub_legs=[nested])
    ctx = _Context(
        family="5W_TREND", legs=[leg], rules_log=[RuleResult("r1", True)],
    )
    h = _Hypothesis(id="orig", context_stack=[ctx])

    clone = h.clone()
    assert clone is not h
    assert clone.id != h.id

    clone.context_stack[0].legs.append(_Leg(role=WaveRole.S2, span_start=p0, span_end=p1))
    clone.context_stack[0].rules_log.append(RuleResult("r2", False))
    clone.context_stack[0].legs[0].sub_legs.append(
        _Leg(role=WaveRole.S2, span_start=p0, span_end=p1)
    )
    assert len(h.context_stack[0].legs) == 1
    assert len(h.context_stack[0].rules_log) == 1
    assert len(h.context_stack[0].legs[0].sub_legs) == 1

    assert clone.context_stack[0].legs[0].span_start is h.context_stack[0].legs[0].span_start
    assert clone.context_stack[0].rules_log[0] is h.context_stack[0].rules_log[0]


def test_parser_dataclasses_use_slots() -> None:
    from engine.parser.types import _Context, _Hypothesis, _Leg

    for cls in (_Leg, _Context, _Hypothesis):
        assert hasattr(cls, "__slots__"), f"{cls.__name__} must declare __slots__"
