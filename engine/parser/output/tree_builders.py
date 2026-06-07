from __future__ import annotations

from engine.adaptive import ALL_LINK
from engine.types import NestingLevel, Pivot, Segment, WaveNode, WaveRole

from ..types import LINK_FAMILIES, _Context, _Leg

__all__ = [
    "_build_root_wavenode",
    "_first_pivot_in_stack",
    "_leg_to_wavenode_with_parent",
]


def _leg_to_wavenode_with_parent(
    leg: _Leg,
    parent: WaveNode,
    nesting_level: NestingLevel,
) -> WaveNode:
    from .linkwave_flattening import _flatten_linkwave_children

    if leg.pattern_kind is None or not leg.sub_legs:
        seg = Segment(start=leg.span_start, end=leg.span_end)
        return WaveNode(
            role=leg.role,
            span_start=leg.span_start,
            pattern_kind=None,
            segments=[seg],
            children=[],
            nesting_level=nesting_level,
            parent=parent,
            span_end=leg.span_end,
        )
    node = WaveNode(
        role=leg.role,
        span_start=leg.span_start,
        pattern_kind=leg.pattern_kind,
        segments=[],
        children=[],
        nesting_level=nesting_level,
        parent=parent,
        span_end=leg.span_end,
    )
    if leg.pattern_kind in ALL_LINK:
        node.children, node.sets = _flatten_linkwave_children(
            leg.sub_legs,
            node,
            nesting_level + 1,
        )
    else:
        node.children = [
            _leg_to_wavenode_with_parent(sub, node, nesting_level + 1) for sub in leg.sub_legs
        ]
    return node


def _first_pivot_in_stack(stack: list[_Context]) -> Pivot | None:
    # Depth-2/3 seeds leave root.legs empty until a sub closes; walk stack for span_start.
    for ctx in stack:
        if ctx.legs:
            return ctx.legs[0].span_start
    return None


def _build_root_wavenode(
    root_ctx: _Context,
    fallback_pivot: Pivot | None = None,
) -> WaveNode:
    from .linkwave_flattening import _flatten_linkwave_children

    span_start = root_ctx.legs[0].span_start if root_ctx.legs else fallback_pivot
    span_end = root_ctx.legs[-1].span_end if (root_ctx.legs and root_ctx.is_complete) else None

    if span_start is None:
        from datetime import datetime

        span_start = Pivot(0, datetime.min, 0.0, "low", None)

    root_node = WaveNode(
        role=WaveRole.ANCHOR,
        span_start=span_start,
        pattern_kind=root_ctx.final_kind,
        children=[],
        nesting_level=0,
        span_end=span_end,
    )
    if not root_ctx.legs:
        return root_node
    if root_ctx.family in LINK_FAMILIES:
        root_node.children, root_node.sets = _flatten_linkwave_children(
            root_ctx.legs,
            root_node,
            nesting_level=1,
        )
    else:
        root_node.children = [
            _leg_to_wavenode_with_parent(leg, root_node, nesting_level=1) for leg in root_ctx.legs
        ]
    return root_node
