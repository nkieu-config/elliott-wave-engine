from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from analyst.schemas.citation import TheoryRef


@dataclass(frozen=True)
class BottleneckDiagnosis:
    slot_name: str
    slot_value: float
    dimension: Literal["structural", "visual"]
    is_dim_minimum: bool
    is_overall_minimum: bool
    gap_to_next: float
    intermediates: dict[str, Any]
    plain_explanation: str
    theory_ref: TheoryRef
