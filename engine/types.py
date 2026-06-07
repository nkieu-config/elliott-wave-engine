from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Literal

__all__ = [
    "ScaleMode",
    "TrendDir",
    "PivotKind",
    "NestingLevel",
    "PatternKind",
    "WaveRole",
    "DegreeLabel",
    "Pivot",
    "Bar",
    "Segment",
    "RuleResult",
    "LinkSet",
    "WaveNode",
    "OpenState",
]

ScaleMode = Literal["linear", "log"]
TrendDir = Literal["up", "down"]
PivotKind = Literal["high", "low"]


class PatternKind(StrEnum):
    FIVE_TREND_S1_LONGEST = "5W_TREND_S1_LONGEST"
    FIVE_TREND_S3_LONGEST = "5W_TREND_S3_LONGEST"
    FIVE_TREND_S5_LONGEST = "5W_TREND_S5_LONGEST"
    FIVE_TREND_S5_SHORTER = "5W_TREND_S5_SHORTER"
    FIVE_TREND_EQUAL_PUSH = "5W_TREND_EQUAL_PUSH"

    FIVE_SIDEWAY_CONTRACT = "5W_SIDEWAY_CONTRACT"
    FIVE_SIDEWAY_BALANCE = "5W_SIDEWAY_BALANCE"
    FIVE_SIDEWAY_EXPAND = "5W_SIDEWAY_EXPAND"

    THREE_NORMAL = "3W_NORMAL"
    THREE_S2_LONGER = "3W_S2_LONGER"
    THREE_S3_SHORTER = "3W_S3_SHORTER"
    THREE_S2_LONGER_S3_SHORTER = "3W_S2_LONGER_S3_SHORTER"

    LINK_T = "LINK_T"
    LINK_S = "LINK_S"
    LINK_SE = "LINK_SE"


class WaveRole(StrEnum):
    ANCHOR = "anchor"
    S1 = "s1"
    S2 = "s2"
    S3 = "s3"
    S4 = "s4"
    S5 = "s5"
    LINK = "link"
    # Parser-internal; flattened public WaveNode tree exposes s1..s5/link directly.
    SET_1 = "set_1"
    SET_2 = "set_2"
    SET_3 = "set_3"


class DegreeLabel(StrEnum):
    # p.96 names 3; cap at MINOR for deeper clusters.
    PRIMARY = "primary"
    SECONDARY = "secondary"
    MINOR = "minor"


@dataclass(frozen=True)
class Pivot:
    index: int
    time: datetime
    price: float
    kind: PivotKind
    bar_index: int | None = None


@dataclass(frozen=True)
class Bar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass(frozen=True)
class Segment:
    start: Pivot
    end: Pivot

    @property
    def direction(self) -> TrendDir:
        return "up" if self.end.price > self.start.price else "down"

    @property
    def time_length_seconds(self) -> float:
        return (self.end.time - self.start.time).total_seconds()

    # price_length lives in engine.helpers (depends on ScaleMode).


@dataclass(frozen=True)
class RuleResult:
    id: str  # e.g. "5wt.r4.s3_gt_s2"
    passed: bool
    measured: float | None = None
    detail: str = ""


# Parse tree depth (0=root). Distinct from EW degree (lives in degree_label).
NestingLevel = int


@dataclass(frozen=True)
class LinkSet:
    # leg_start/leg_end inclusive indices into parent's children; LINK legs belong to no set.
    pattern_kind: PatternKind
    leg_start: int
    leg_end: int
    degree_label: DegreeLabel | None = None


@dataclass
class WaveNode:
    # READ-ONLY after count_waves returns — mutation corrupts cached scenarios.
    role: WaveRole
    span_start: Pivot
    pattern_kind: PatternKind | None = None
    segments: list[Segment] = field(default_factory=list)
    children: list[WaveNode] = field(default_factory=list)
    nesting_level: NestingLevel = 0
    parent: WaveNode | None = field(default=None, repr=False)
    span_end: Pivot | None = None

    # Post-parse by engine.degree.assign_degree_labels.
    degree_label: DegreeLabel | None = None

    # Only set when pattern_kind is LINK_T/LINK_S/LINK_SE.
    sets: list[LinkSet] | None = None

    @property
    def direction(self) -> TrendDir:
        if self.span_end is None:
            raise ValueError("Cannot infer direction from open WaveNode (span_end is None)")
        return "up" if self.span_end.price > self.span_start.price else "down"

    @property
    def sub_legs(self) -> list[WaveNode]:
        return self.children


@dataclass
class OpenState:
    current_role: WaveRole | None = None
    # Root-context role; differs from current_role when sub-pattern open. None once root full.
    root_role: WaveRole | None = None
    current_pattern: PatternKind | None = None
    nesting_level: NestingLevel = 0
    next_expected: list[WaveRole] = field(default_factory=list)
