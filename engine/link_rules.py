"""Shared LINK_S sizing rule (R3). At package root to dodge the verifier/scoring import graph."""

from __future__ import annotations

from engine.adaptive import KIND_TO_FAMILY
from engine.constants import (
    R3_LINK_MIN_3W_LINK_S,
    R3_LINK_MIN_5WS_LINK_S,
    R3_LINK_MIN_EXPAND_LINK_S,
)
from engine.types import PatternKind


def link_s_min_required(kind: PatternKind | None) -> float:
    # inf for kinds with no LINK_S succession ⇒ gate fails closed.
    if kind is None:
        return float("inf")
    if kind in (PatternKind.FIVE_SIDEWAY_CONTRACT, PatternKind.FIVE_SIDEWAY_BALANCE):
        return R3_LINK_MIN_5WS_LINK_S
    if kind == PatternKind.FIVE_SIDEWAY_EXPAND:
        return R3_LINK_MIN_EXPAND_LINK_S
    if KIND_TO_FAMILY.get(kind) == "3W":
        return R3_LINK_MIN_3W_LINK_S
    return float("inf")


def link_s_ratio_mode(kind: PatternKind | None) -> str | None:
    # LINK_S ratio denominator: "total_range" (3W/Contract/Balance), "s5_leg"
    # (Expand), None (no ratio). Only the kind→mode dispatch is shared.
    if kind is None:
        return None
    if KIND_TO_FAMILY.get(kind) == "3W":
        return "total_range"
    if kind == PatternKind.FIVE_SIDEWAY_EXPAND:
        return "s5_leg"
    if kind in (PatternKind.FIVE_SIDEWAY_CONTRACT, PatternKind.FIVE_SIDEWAY_BALANCE):
        return "total_range"
    return None
