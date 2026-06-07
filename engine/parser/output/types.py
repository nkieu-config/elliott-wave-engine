from __future__ import annotations

from dataclasses import dataclass, field

from engine.adaptive import Family
from engine.types import (
    OpenState,
    PatternKind,
    Pivot,
    RuleResult,
    Segment,
    WaveNode,
    WaveRole,
)

__all__ = ["AnalysisReport", "DiagnosticReport", "Scenario"]


@dataclass
class DiagnosticReport:
    first_divergence_index: int = -1
    last_alive_segment_index: int = -1
    death_reason: str = ""
    suggested_action: str = ""


@dataclass
class Scenario:
    id: str
    root: WaveNode
    score: float = 0.0
    # Slots + structural_total/visual_total/quality(MIN)/commitment/total(=quality*commitment).
    score_components: dict[str, float] = field(default_factory=dict)
    open_state: OpenState = field(default_factory=OpenState)
    rules_log: list[RuleResult] = field(default_factory=list)

    # Sub-patterns not yet closed into root.legs — keeps `legs` "closed-only".
    open_subtree: WaveNode | None = None

    # Always set by to_scenario; default is dataclass-init only.
    _family: Family = "5W_TREND"

    @property
    def family(self) -> Family:
        return self._family

    @property
    def pattern_kind(self) -> PatternKind | None:
        return self.root.pattern_kind

    @property
    def is_complete(self) -> bool:
        return self.root.span_end is not None and self.root.pattern_kind is not None

    @property
    def legs(self) -> list[WaveNode]:
        return self.root.children

    @property
    def open_role(self) -> WaveRole | None:
        return self.open_state.current_role

    @property
    def depth(self) -> int:
        # 1=root only; 2=one sub; N+1=nested depth-N.
        def _sub_depth(node: WaveNode) -> int:
            extra = 0
            for c in node.children:
                if c.pattern_kind is not None:
                    extra = max(extra, _sub_depth(c) + 1)
            return extra

        return 1 + _sub_depth(self.root)


@dataclass
class AnalysisReport:
    anchor: Pivot | None = None
    segments: list[Segment] = field(default_factory=list)
    scenarios: list[Scenario] = field(default_factory=list)
    diagnostic: DiagnosticReport = field(default_factory=DiagnosticReport)
    summary: str = ""
