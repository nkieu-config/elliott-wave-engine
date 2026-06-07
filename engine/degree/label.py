from __future__ import annotations

from engine.types import DegreeLabel, LinkSet, WaveNode

__all__ = ["assign_degree_labels"]


_LEVEL_TO_LABEL: tuple[DegreeLabel, ...] = (
    DegreeLabel.PRIMARY,
    DegreeLabel.SECONDARY,
    DegreeLabel.MINOR,
)
_MAX_LEVEL = len(_LEVEL_TO_LABEL) - 1


def _level_label(level: int) -> DegreeLabel:
    return _LEVEL_TO_LABEL[min(max(level, 0), _MAX_LEVEL)]


def assign_degree_labels(root: WaveNode | None) -> None:
    if root is None:
        return
    root.degree_label = _level_label(0)
    _walk(root, level=0)


def _walk(node: WaveNode, level: int) -> None:
    child_label = _level_label(level)
    for child in node.children:
        child.degree_label = child_label
        if child.pattern_kind is not None and child.children:
            _walk(child, level=level + 1)
    if node.sets is not None:
        node.sets = [
            LinkSet(
                pattern_kind=s.pattern_kind,
                leg_start=s.leg_start,
                leg_end=s.leg_end,
                degree_label=child_label,
            )
            for s in node.sets
        ]
