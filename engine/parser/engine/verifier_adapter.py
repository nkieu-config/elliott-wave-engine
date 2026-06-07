from __future__ import annotations

from engine.adaptive import Family
from engine.types import PatternKind, RuleResult, ScaleMode

from ..families import FAMILY_SPECS
from ..types import _Leg
from ._helpers import _build_linkwave_verifier_input, _legs_to_virtual_segments

__all__ = ["_run_verifier"]


def _run_verifier(
    family: Family,
    legs: list[_Leg],
    mode: ScaleMode,
) -> tuple[PatternKind, list[RuleResult]] | None:
    spec = FAMILY_SPECS.get(family)
    if spec is None:
        return None
    if spec.input_adapter == "simple":
        return spec.verifier(_legs_to_virtual_segments(legs), mode)
    sets, children, links = _build_linkwave_verifier_input(legs)
    return spec.verifier(sets, children, links, mode)
