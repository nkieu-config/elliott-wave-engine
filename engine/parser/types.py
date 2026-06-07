from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field

from engine.adaptive import Family
from engine.parser.leg_structure import (
    LINK_FAMILIES as LINK_FAMILIES,  # re-export for output layer / parser.__init__
)
from engine.parser.leg_structure import LegStructure, leg_structure_for
from engine.types import (
    PatternKind,
    Pivot,
    RuleResult,
    ScaleMode,
    TrendDir,
    WaveRole,
)

BEAM_WIDTH = 500
# Seeds: depth 1 (direct) / depth 2 (Link-Wave root+set_1); Option B grows further, capped here.
MAX_RECURSION_DEPTH = 8
HARD_TIMEOUT_MS = 30_000

# Seed family sets live in parser.families (registry imports this low module, not vice-versa).


# slots=True — beam allocates 100k+ on long charts; __dict__ adds ~30%.


@dataclass(slots=True)
class _Leg:
    role: WaveRole
    span_start: Pivot
    span_end: Pivot
    pattern_kind: PatternKind | None = None
    sub_legs: list[_Leg] = field(default_factory=list)

    @property
    def direction(self) -> TrendDir:
        return "up" if self.span_end.price > self.span_start.price else "down"

    def length(self, mode: ScaleMode) -> float:
        a, b = self.span_start.price, self.span_end.price
        if mode == "linear":
            return abs(b - a)
        if min(a, b) <= 0:
            return 0.0  # log undefined for non-positive prices
        return abs(math.log(b) - math.log(a))


@dataclass(slots=True)
class _Context:
    family: Family
    legs: list[_Leg]
    final_kind: PatternKind | None = None
    rules_log: list[RuleResult] = field(default_factory=list)
    parent_role: WaveRole | None = None
    # Bound once from `family` at construction (incl. clone); the hot leg-structure
    # properties below read off it instead of re-branching on the family string.
    struct: LegStructure = field(init=False)

    def __post_init__(self) -> None:
        self.struct = leg_structure_for(self.family)

    @property
    def trend_dir(self) -> TrendDir:
        # Link pp.56-57: trend = set_1.s1 direction (set net-span can flip on big s2).
        first = self.legs[0]
        if self.struct.is_link and first.sub_legs:
            return first.sub_legs[0].direction
        return first.direction

    @property
    def max_legs(self) -> int:
        return self.struct.max_legs

    @property
    def min_legs_to_complete(self) -> int:
        return self.struct.min_legs_to_complete

    @property
    def is_complete(self) -> bool:
        return self.struct.complete(len(self.legs))

    @property
    def next_role(self) -> WaveRole | None:
        return self.struct.next_role(len(self.legs))

    @property
    def is_set_position(self) -> bool:
        return self.struct.is_set_position(len(self.legs))


@dataclass(slots=True)
class _Hypothesis:
    id: str
    context_stack: list[_Context]
    score: float = 0.0
    score_components: dict[str, float] = field(default_factory=dict)

    @property
    def top(self) -> _Context:
        return self.context_stack[-1]

    @property
    def root(self) -> _Context:
        return self.context_stack[0]

    @property
    def depth(self) -> int:
        return len(self.context_stack)

    def clone(self) -> _Hypothesis:
        # copy.deepcopy was 94% of wall time; only lists are mutated, so shallow-copy them.
        return _Hypothesis(
            id=str(uuid.uuid4()),
            context_stack=[_clone_context(c) for c in self.context_stack],
            score=self.score,
            score_components=dict(self.score_components),
        )


def _clone_leg(leg: _Leg) -> _Leg:
    return _Leg(
        role=leg.role,
        span_start=leg.span_start,
        span_end=leg.span_end,
        pattern_kind=leg.pattern_kind,
        sub_legs=[_clone_leg(s) for s in leg.sub_legs],
    )


def _clone_context(ctx: _Context) -> _Context:
    return _Context(
        family=ctx.family,
        legs=[_clone_leg(leg) for leg in ctx.legs],
        final_kind=ctx.final_kind,
        rules_log=list(ctx.rules_log),
        parent_role=ctx.parent_role,
    )
