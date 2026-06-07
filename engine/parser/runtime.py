from __future__ import annotations

from dataclasses import dataclass, field

from engine.types import Bar

from .scoring_config import ScoringConfig


@dataclass(frozen=True)
class RuntimeContext:
    bars: tuple[Bar, ...] = field(default_factory=tuple)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)

    @classmethod
    def from_bars(
        cls,
        bars: list[Bar] | None,
        *,
        scoring: ScoringConfig | None = None,
    ) -> RuntimeContext:
        return cls(
            bars=tuple(bars) if bars else (),
            scoring=scoring or ScoringConfig(),
        )
