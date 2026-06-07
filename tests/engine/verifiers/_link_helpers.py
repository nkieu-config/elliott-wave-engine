from __future__ import annotations

from datetime import timedelta

from engine.types import LinkSet, PatternKind, Pivot, Segment, WaveNode, WaveRole
from engine.verifiers import verify_link_s, verify_link_t
from tests.fixtures import make_segments


def call_verify_link_t(groups, links, mode):
    return verify_link_t(*groups_to_verifier_input(groups, links), mode)


def call_verify_link_s(groups, links, mode):
    return verify_link_s(*groups_to_verifier_input(groups, links), mode)


def build_3w_group(
    prices: list[float],
    kind: PatternKind = PatternKind.THREE_NORMAL,
    role: WaveRole = WaveRole.SET_1,
) -> WaveNode:
    segs = make_segments(prices)
    assert len(segs) == 3, f"build_3w_group: expected 4 prices → 3 segs, got {len(segs)}"
    return WaveNode(
        role=role,
        span_start=segs[0].start,
        pattern_kind=kind,
        segments=segs,
        span_end=segs[-1].end,
    )


def link_segment(
    start: Pivot,
    end_price: float,
    weeks: int = 3,
) -> Segment:
    end = Pivot(
        index=start.index + 1,
        time=start.time + timedelta(weeks=weeks),
        price=end_price,
        kind="low" if end_price < start.price else "high",
        bar_index=start.bar_index + weeks if start.bar_index is not None else None,
    )
    return Segment(start=start, end=end)


_LEG_ROLES_3W = (WaveRole.S1, WaveRole.S2, WaveRole.S3)
_LEG_ROLES_5W = (WaveRole.S1, WaveRole.S2, WaveRole.S3, WaveRole.S4, WaveRole.S5)


def groups_to_verifier_input(
    groups: list[WaveNode],
    links: list[Segment],
) -> tuple[list[LinkSet], list[WaveNode], list[Segment]]:
    sets: list[LinkSet] = []
    children: list[WaveNode] = []
    for gi, g in enumerate(groups):
        leg_start = len(children)
        if g.children:
            for leg_node in g.children:
                children.append(leg_node)
        else:
            leg_role_seq = _LEG_ROLES_5W if len(g.segments) >= 5 else _LEG_ROLES_3W
            for seg_idx, seg in enumerate(g.segments):
                role = leg_role_seq[seg_idx] if seg_idx < len(leg_role_seq) else WaveRole.S5
                children.append(
                    WaveNode(
                        role=role,
                        span_start=seg.start,
                        pattern_kind=None,
                        segments=[seg],
                        span_end=seg.end,
                    )
                )
        sets.append(
            LinkSet(
                pattern_kind=g.pattern_kind,
                leg_start=leg_start,
                leg_end=len(children) - 1,
            )
        )
        if gi < len(links):
            link_seg = links[gi]
            children.append(
                WaveNode(
                    role=WaveRole.LINK,
                    span_start=link_seg.start,
                    pattern_kind=None,
                    segments=[link_seg],
                    span_end=link_seg.end,
                )
            )
    return sets, children, links


def g2_after_link(
    link: Segment,
    leg_lengths: tuple[float, float, float],
    kind: PatternKind = PatternKind.THREE_NORMAL,
    role: WaveRole = WaveRole.SET_2,
) -> WaveNode:
    base_t = link.end.time
    base_bar = link.end.bar_index if link.end.bar_index is not None else 0
    trend_up = link.start.price > link.end.price
    s1_dir = 1.0 if trend_up else -1.0
    p0 = link.end.price
    p1 = p0 + s1_dir * leg_lengths[0]
    p2 = p1 - s1_dir * leg_lengths[1]
    p3 = p2 + s1_dir * leg_lengths[2]
    pivots = [
        Pivot(0, base_t, p0, "low" if trend_up else "high", base_bar),
        Pivot(1, base_t + timedelta(weeks=1), p1, "high" if trend_up else "low", base_bar + 1),
        Pivot(2, base_t + timedelta(weeks=2), p2, "low" if trend_up else "high", base_bar + 2),
        Pivot(3, base_t + timedelta(weeks=3), p3, "high" if trend_up else "low", base_bar + 3),
    ]
    segs = [Segment(pivots[i], pivots[i + 1]) for i in range(3)]
    return WaveNode(
        role=role,
        span_start=segs[0].start,
        pattern_kind=kind,
        segments=segs,
        span_end=segs[-1].end,
    )
