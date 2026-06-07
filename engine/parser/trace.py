from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any


@dataclass
class TraceEvent:
    t_ms: float
    kind: str  # seed|step|beam|close_up|finalize|timeout
    seg_index: int = -1  # -1 = boundary
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)


class Tracer:
    def __init__(self) -> None:
        self._t0 = perf_counter()
        self.events: list[TraceEvent] = []

    def emit(
        self,
        kind: str,
        *,
        seg_index: int = -1,
        detail: str = "",
        **data: Any,
    ) -> None:
        self.events.append(
            TraceEvent(
                t_ms=(perf_counter() - self._t0) * 1000.0,
                kind=kind,
                seg_index=seg_index,
                detail=detail,
                data=data,
            )
        )

    def __len__(self) -> int:
        return len(self.events)

    def __iter__(self):
        return iter(self.events)
