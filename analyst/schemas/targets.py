from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# "projected" = forecast (open wave 5) vs measured levels.
TargetType = Literal[
    "retracement", "internal", "external", "invalidation", "projected"
]


@dataclass(frozen=True)
class Target:
    name: str
    price: float
    type: TargetType
    theory_page: int
    derivation: str


@dataclass(frozen=True)
class TargetSet:
    confirmation_targets: tuple[Target, ...]
    fib_flow_targets: tuple[Target, ...]
    invalidation: Target
