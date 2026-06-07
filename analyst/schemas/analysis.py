from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from analyst.schemas.bottleneck import BottleneckDiagnosis
    from analyst.schemas.confirmation import ConfirmationReport
    from analyst.schemas.decision import AlternativeBrief, DecisionSummary
    from analyst.schemas.succession import SuccessionReport
    from analyst.schemas.targets import TargetSet


@dataclass(frozen=True)
class AnalysisResult:
    scenario_id: str
    bottleneck: BottleneckDiagnosis | None = None
    confirmation: ConfirmationReport | None = None
    targets: TargetSet | None = None
    succession: SuccessionReport | None = None
    decision: DecisionSummary | None = None
    alternative: AlternativeBrief | None = None
    # Per-slot intermediates power 2nd/3rd weakest detail (not just bottleneck).
    score_intermediates: dict = field(default_factory=dict)
    scenario_diffs: tuple = ()  # tuple[ScenarioDiff, ...]
