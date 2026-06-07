from __future__ import annotations

import uuid

from engine.adaptive import Family, allowed_sub_families
from engine.parser.engine._helpers import _seg_to_leg
from engine.parser.families import (
    KNOWN_SUB_FAMILIES,
    LINK_INNER_SET1_FAMILIES,
    SIMPLE_ROOT_FAMILIES,
)
from engine.parser.types import _Context, _Hypothesis
from engine.types import Segment, WaveRole

_ROOT_FAMILIES: tuple[Family, ...] = SIMPLE_ROOT_FAMILIES

# Link-Wave roots and the families their first set (set_1) may take (registry-derived).
_LINK_SET1: tuple[tuple[Family, tuple[Family, ...]], ...] = tuple(
    LINK_INNER_SET1_FAMILIES.items()
)


def _sub_families(family: Family, role: WaveRole) -> tuple[Family, ...]:
    return tuple(f for f in allowed_sub_families(family, role) if f in KNOWN_SUB_FAMILIES)


def _seed_chain(first_seg: Segment, *links: tuple[Family, WaveRole | None]) -> _Hypothesis:
    # Only the deepest (leaf) context gets first_seg as its s1; shallower start empty.
    last = len(links) - 1
    stack = [
        _Context(
            family=fam,
            legs=[_seg_to_leg(first_seg, WaveRole.S1)] if i == last else [],
            parent_role=parent_role,
        )
        for i, (fam, parent_role) in enumerate(links)
    ]
    return _Hypothesis(id=str(uuid.uuid4()), context_stack=stack)


def seed_hypotheses(first_seg: Segment) -> list[_Hypothesis]:
    # Depth-3 seeds load-bearing: Option B can't deepen sub.s1 after first_seg placed.
    # Ordering (all depth-2 before all depth-3, simple before link) is preserved as-is.
    hyps: list[_Hypothesis] = []

    hyps.extend(_seed_chain(first_seg, (fam, None)) for fam in _ROOT_FAMILIES)

    for root_fam in _ROOT_FAMILIES:
        for sub_fam in _sub_families(root_fam, WaveRole.S1):
            hyps.append(_seed_chain(first_seg, (root_fam, None), (sub_fam, WaveRole.S1)))

    for root_fam in _ROOT_FAMILIES:
        for sub_fam in _sub_families(root_fam, WaveRole.S1):
            for sub_sub_fam in _sub_families(sub_fam, WaveRole.S1):
                hyps.append(
                    _seed_chain(
                        first_seg,
                        (root_fam, None),
                        (sub_fam, WaveRole.S1),
                        (sub_sub_fam, WaveRole.S1),
                    )
                )

    for link_fam, g1_fams in _LINK_SET1:
        for g1_fam in g1_fams:
            hyps.append(_seed_chain(first_seg, (link_fam, None), (g1_fam, WaveRole.SET_1)))

    for link_fam, g1_fams in _LINK_SET1:
        for g1_fam in g1_fams:
            for inner_fam in _sub_families(g1_fam, WaveRole.S1):
                hyps.append(
                    _seed_chain(
                        first_seg,
                        (link_fam, None),
                        (g1_fam, WaveRole.SET_1),
                        (inner_fam, WaveRole.S1),
                    )
                )

    return hyps
