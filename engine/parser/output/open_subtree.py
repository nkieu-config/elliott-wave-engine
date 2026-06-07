from __future__ import annotations

from engine.types import WaveNode

from ..types import LINK_FAMILIES, _Context

__all__ = ["_build_open_subcontext_chain"]


def _build_open_subcontext_chain(
    stack: list[_Context],
    start_idx: int,
    parent: WaveNode,
) -> WaveNode | None:
    from .linkwave_flattening import (
        _flatten_linkwave_children,
        _merge_open_into_linkwave,
    )
    from .tree_builders import _leg_to_wavenode_with_parent

    if start_idx >= len(stack):
        return None
    ctx = stack[start_idx]
    if ctx.parent_role is None:
        return None
    if not ctx.legs and start_idx + 1 >= len(stack):
        return None

    span_start = ctx.legs[0].span_start if ctx.legs else parent.span_start
    span_end = ctx.legs[-1].span_end if ctx.legs else None

    node = WaveNode(
        role=ctx.parent_role,
        span_start=span_start,
        pattern_kind=ctx.final_kind,
        segments=[],
        children=[],
        nesting_level=parent.nesting_level + 1,
        parent=parent,
        span_end=span_end,
    )

    if ctx.family in LINK_FAMILIES:
        flat, sets = _flatten_linkwave_children(
            ctx.legs,
            node,
            node.nesting_level + 1,
        )
        node.children = flat
        node.sets = sets
        if start_idx + 1 < len(stack):
            _merge_open_into_linkwave(node, stack, start_idx + 1)
        return node

    children: list[WaveNode] = [
        _leg_to_wavenode_with_parent(leg, node, nesting_level=node.nesting_level + 1)
        for leg in ctx.legs
    ]
    deeper = _build_open_subcontext_chain(stack, start_idx + 1, node)
    if deeper is not None:
        children.append(deeper)
    node.children = children
    return node
