from __future__ import annotations

from datetime import datetime, timedelta

from engine.types import Pivot

_BASE = datetime(2020, 1, 1)


def piv(idx: int, price: float, kind: str, bar: int | None = None) -> Pivot:
    """Pivot at week ``bar`` (defaults to ``idx``) — the parser tests' canonical builder."""
    b = idx if bar is None else bar
    return Pivot(
        index=idx,
        time=_BASE + timedelta(weeks=b),
        price=price,
        kind=kind,  # type: ignore[arg-type]
        bar_index=b,
    )
