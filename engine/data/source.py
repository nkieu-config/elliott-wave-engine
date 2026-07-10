from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from engine.types import Bar

__all__ = ["BarSource"]


class BarSource(Protocol):
    def download(self, symbol: str, *, period: str, interval: str) -> Sequence[Bar]:
        ...
