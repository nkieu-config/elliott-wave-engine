from __future__ import annotations

from datetime import datetime

from engine.parser.output.scenario_assembly import _deterministic_scenario_id
from engine.types import Pivot, WaveNode

FAM = "5W_TREND"


def _pivot(i: int) -> Pivot:
    return Pivot(i, datetime(2024, 1, 1), 100.0 + i, "low")


def _node(role: str, start: int, end: int, children: list[WaveNode] | None = None) -> WaveNode:
    return WaveNode(
        role=role, span_start=_pivot(start), span_end=_pivot(end),
        children=children or [],
    )


def _root() -> WaveNode:
    return _node("root", 0, 5, [_node("s1", 0, 1), _node("s2", 1, 2)])


def test_id_is_stable_for_identical_structure():
    a = _deterministic_scenario_id(_root(), None, FAM)
    b = _deterministic_scenario_id(_root(), None, FAM)
    assert a == b


def test_id_differs_when_open_subtree_present():
    root = _root()
    bare = _deterministic_scenario_id(root, None, FAM)
    with_open = _deterministic_scenario_id(root, _node("s3", 2, 3), FAM)
    assert bare != with_open  # an open_subtree must not collide with no open_subtree


def test_id_differs_between_distinct_open_subtrees():
    root = _root()
    id_a = _deterministic_scenario_id(root, _node("s3", 2, 3), FAM)
    id_b = _deterministic_scenario_id(root, _node("s3", 2, 4), FAM)  # different end pivot
    assert id_a != id_b
