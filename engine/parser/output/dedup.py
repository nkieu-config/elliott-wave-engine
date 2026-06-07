from __future__ import annotations

from engine.types import WaveNode

from .types import Scenario

__all__ = [
    "dedup_user_visible_scenarios",
    "_user_visible_signature",
]


def _user_visible_signature(scenario: Scenario) -> tuple:
    def _shape(node: WaveNode) -> tuple:
        kind = node.pattern_kind.value if node.pattern_kind else "open"
        return (kind, tuple(_shape(c) for c in node.children))

    return (
        scenario.family,
        scenario.pattern_kind.value if scenario.pattern_kind else "—",
        _shape(scenario.root),
    )


def dedup_user_visible_scenarios(scenarios: list[Scenario]) -> list[Scenario]:
    deduped: dict[tuple, Scenario] = {}
    for sc in scenarios:
        sig = _user_visible_signature(sc)
        if sig not in deduped or sc.score > deduped[sig].score:
            deduped[sig] = sc
    return list(deduped.values())
