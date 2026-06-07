from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NextPattern:
    # link_band_far=None when +S has no upper bound; both None when too few legs.
    link_type: str
    next_families: tuple[str, ...]
    link_band_near: float | None
    link_band_far: float | None
    theory_pages: tuple[int, ...]
    rationale: str
    # Anchor-independent — known even while the band can't anchor (open pattern).
    link_wave_size: float | None = None


@dataclass(frozen=True)
class SuccessionReport:
    family: str
    is_terminal: bool
    next_patterns: tuple[NextPattern, ...]
    note: str
