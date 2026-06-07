from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# "overshot" = price beyond band's far edge; UI must not render as destination.
WaveStage = Literal["complete", "early", "mid", "late", "overshot", "unknown"]


@dataclass(frozen=True)
class PriceMove:
    label: str
    price: float
    pct_from_current: float


@dataclass(frozen=True)
class DecisionSummary:
    current: PriceMove
    target_low: PriceMove | None = None
    target_high: PriceMove | None = None
    invalidation: PriceMove | None = None
    # reward = mid(target) - current; risk = current - invalidation. None on inverted geometry.
    risk_reward: float | None = None
    direction: str | None = None
    horizon_bars: int | None = None
    bar_interval: str | None = None
    horizon_human: str | None = None
    stage: WaveStage = "unknown"
    open_wave_start: float | None = None
    # Open wave's own direction by Elliott alternation (distinct from band-vs-current).
    open_wave_direction: str | None = None
    # 0% = wave start, 100% = far band edge, >100% = overshot.
    wave_progress_pct: float | None = None
    # Set only at stage == "overshot": distance PAST the far edge, pre-computed
    # so narration quotes it instead of deriving it from progress%.
    overshoot_amount: float | None = None
    overshoot_pct_of_span: float | None = None


@dataclass(frozen=True)
class AlternativeBrief:
    family: str
    family_label: str
    target_low: PriceMove | None = None
    target_high: PriceMove | None = None
    invalidation: PriceMove | None = None
    direction: str | None = None
    stage: WaveStage = "unknown"
