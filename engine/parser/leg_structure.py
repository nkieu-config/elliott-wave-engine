# Low module (adaptive + types only) so _Context can bind a LegStructure without
# cycling through the registry.
from __future__ import annotations

from dataclasses import dataclass

from engine.adaptive import Family
from engine.types import WaveRole

ROLE_SEQ: tuple[WaveRole, ...] = (
    WaveRole.S1,
    WaveRole.S2,
    WaveRole.S3,
    WaveRole.S4,
    WaveRole.S5,
)
LINK_SET_SLOTS: tuple[WaveRole, ...] = (WaveRole.SET_1, WaveRole.SET_2, WaveRole.SET_3)


@dataclass(frozen=True, slots=True)
class LegStructure:
    is_link: bool
    max_legs: int
    min_legs_to_complete: int
    role_seq: tuple[WaveRole, ...]
    link_set_slots: tuple[WaveRole, ...] | None

    def complete(self, n: int) -> bool:
        if self.is_link:
            return n in (3, 5)  # G,L,G or G,L,G,L,G
        return n >= self.max_legs

    def next_role(self, n: int) -> WaveRole | None:
        if self.is_link:
            if n >= 5 or self.link_set_slots is None:
                return None
            return self.link_set_slots[n // 2] if n % 2 == 0 else WaveRole.LINK
        if n >= self.max_legs:
            return None
        return self.role_seq[n]

    def is_set_position(self, n: int) -> bool:
        return self.is_link and n % 2 == 0


_SIMPLE_3 = LegStructure(False, 3, 3, ROLE_SEQ, None)
_SIMPLE_5 = LegStructure(False, 5, 5, ROLE_SEQ, None)
_LINK = LegStructure(True, 5, 3, ROLE_SEQ, LINK_SET_SLOTS)

LEG_STRUCTURE: dict[Family, LegStructure] = {
    "3W": _SIMPLE_3,
    "5W_TREND": _SIMPLE_5,
    "5W_SIDEWAY": _SIMPLE_5,
    "LINK_T": _LINK,
    "LINK_S": _LINK,
    "LINK_SE": _LINK,
}

LINK_FAMILIES: frozenset[Family] = frozenset(f for f, s in LEG_STRUCTURE.items() if s.is_link)

DEFAULT_LEG_STRUCTURE = _SIMPLE_5


def leg_structure_for(family: str) -> LegStructure:
    # Unknown families fall back to simple-5 (legacy _Context `else: return 5`).
    return LEG_STRUCTURE.get(family, DEFAULT_LEG_STRUCTURE)  # type: ignore[call-overload]
