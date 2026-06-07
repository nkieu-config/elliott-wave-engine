from __future__ import annotations

from engine.helpers import bar_span
from engine.parser.types import BEAM_WIDTH, _Hypothesis, _Leg


def _canonical_form(h: _Hypothesis) -> tuple:
    # Family (not kind) since subtype unset until close; leaf direction included.
    top = h.top
    tree_shape = tuple(_canonical_leg(lg) for lg in h.root.legs)
    return (
        h.root.family,
        top.family,
        top.next_role.value if top.next_role else "complete",
        tree_shape,
        h.depth,
    )


def _canonical_leg(leg: _Leg) -> tuple:
    if leg.pattern_kind is None:
        return ("seg", leg.direction)
    return (leg.pattern_kind.value, tuple(_canonical_leg(s) for s in leg.sub_legs))


def _hypothesis_total_bar_span(h: _Hypothesis) -> int:
    # 0 when no legs or bar_index missing — sorts last.
    legs = h.root.legs
    if not legs:
        return 0
    span = bar_span(legs[0].span_start, legs[-1].span_end)
    return 0 if span is None else span


def _dedup_and_beam(
    hyps: list[_Hypothesis],
    beam_width: int = BEAM_WIDTH,
) -> list[_Hypothesis]:
    # Tie-break: score↓, depth↑ (Occam), span↓, canon↑ (deterministic).
    by_canon: dict[tuple, _Hypothesis] = {}
    for h in hyps:
        key = _canonical_form(h)
        if key not in by_canon or h.score > by_canon[key].score:
            by_canon[key] = h

    ranked = sorted(
        by_canon.items(),
        key=lambda item: (
            -item[1].score,
            item[1].depth,
            -_hypothesis_total_bar_span(item[1]),
            item[0],
        ),
    )
    return [h for _, h in ranked[:beam_width]]
