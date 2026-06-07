from __future__ import annotations

from engine.types import ScaleMode, Segment

from ..runtime import RuntimeContext
from ..scoring import _score_components
from ..trace import Tracer
from ..types import _Hypothesis
from .branching import _branch
from .closing import _close_up_at_end, _try_finalize
from .dedup import _dedup_and_beam

__all__ = ["close_up_and_rescore", "process_segment"]


def process_segment(
    live: list[_Hypothesis],
    seg: Segment,
    mode: ScaleMode,
    beam_width: int,
    *,
    runtime: RuntimeContext,
) -> tuple[list[_Hypothesis], int]:
    next_live: list[_Hypothesis] = []
    for h in live:
        for nxt in _branch(h, seg, mode):
            next_live.append(nxt)
    for h in next_live:
        h.score_components = _score_components(h, mode, runtime=runtime)
        h.score = h.score_components["total"]
    n_pre_beam = len(next_live)
    next_live = _dedup_and_beam(next_live, beam_width=beam_width)
    return next_live, n_pre_beam


def close_up_and_rescore(
    live: list[_Hypothesis],
    mode: ScaleMode,
    tracer: Tracer | None,
    *,
    runtime: RuntimeContext,
) -> None:
    for h in live:
        _close_up_at_end(h, mode)
        finalized = _try_finalize(h.root, mode)
        h.score_components = _score_components(h, mode, runtime=runtime)
        h.score = h.score_components["total"]
        if tracer is not None and finalized:
            tracer.emit(
                "finalize",
                detail=(
                    f"hyp {h.id[:8]} → "
                    f"{h.root.final_kind.value if h.root.final_kind else h.root.family}"
                ),
                hyp_id=h.id,
                family=h.root.family,
                final_kind=(h.root.final_kind.value if h.root.final_kind else None),
                score=round(h.score, 4),
            )
