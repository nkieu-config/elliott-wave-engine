from __future__ import annotations

from engine.parser.types import _Leg
from engine.types import LinkSet, Segment, WaveNode, WaveRole


def _seg_to_leg(seg: Segment, role: WaveRole) -> _Leg:
    return _Leg(role=role, span_start=seg.start, span_end=seg.end)


def _legs_to_virtual_segments(legs: list[_Leg]) -> list[Segment]:
    return [Segment(start=lg.span_start, end=lg.span_end) for lg in legs]


def _leg_to_wavenode(leg: _Leg) -> WaveNode:
    if leg.pattern_kind is None or not leg.sub_legs:
        seg = Segment(start=leg.span_start, end=leg.span_end)
        return WaveNode(
            role=leg.role,
            pattern_kind=None,
            segments=[seg],
            span_start=leg.span_start,
            span_end=leg.span_end,
        )
    return WaveNode(
        role=leg.role,
        pattern_kind=leg.pattern_kind,
        segments=[Segment(start=lg.span_start, end=lg.span_end) for lg in leg.sub_legs],
        span_start=leg.span_start,
        span_end=leg.span_end,
    )


def _build_linkwave_verifier_input(
    legs: list[_Leg],
) -> tuple[list[LinkSet], list[WaveNode], list[Segment]]:
    # Mirrors output._flatten_linkwave_children; [G,L,G,L,G] → (sets, children, links).
    children: list[WaveNode] = []
    sets: list[LinkSet] = []
    links: list[Segment] = []
    for i, lg in enumerate(legs):
        if i % 2 == 0:
            if lg.pattern_kind is None or not lg.sub_legs:
                children.append(_leg_to_wavenode(lg))
                continue
            start = len(children)
            for sub in lg.sub_legs:
                children.append(_leg_to_wavenode(sub))
            sets.append(
                LinkSet(
                    pattern_kind=lg.pattern_kind,
                    leg_start=start,
                    leg_end=len(children) - 1,
                )
            )
        else:
            children.append(_leg_to_wavenode(lg))
            links.append(Segment(start=lg.span_start, end=lg.span_end))
    return sets, children, links
