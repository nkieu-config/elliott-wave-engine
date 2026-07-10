from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol

from engine.types import Bar

__all__ = [
    "BarCache",
    "CacheKey",
]


@dataclass(frozen=True)
class CacheKey:
    symbol: str
    cache_label: str
    period: str


class BarCache(Protocol):
    def load(self, key: CacheKey, max_age: timedelta | None = None) -> Sequence[Bar] | None:
        ...

    def store(self, key: CacheKey, bars: Sequence[Bar]) -> None:
        ...

    def clear(self, symbol: str | None = None) -> int:
        ...

    def count(self) -> int:
        ...
