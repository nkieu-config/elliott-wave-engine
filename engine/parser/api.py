from __future__ import annotations

import logging
import time
from collections.abc import Callable

from engine.types import Bar, Pivot, ScaleMode, Segment

from .engine import (
    close_up_and_rescore,
    process_segment,
    seed_hypotheses,
)
from .output import (
    AnalysisReport,
    DiagnosticTracker,
    build_diagnostic,
    dedup_user_visible_scenarios,
    to_scenario,
)
from .runtime import RuntimeContext
from .scoring_config import ScoringConfig
from .trace import Tracer
from .types import BEAM_WIDTH, HARD_TIMEOUT_MS, _Hypothesis

logger = logging.getLogger("engine.parser.api")

__all__ = ["count_waves", "pivots_to_segments"]


def pivots_to_segments(pivots: list[Pivot], anchor: Pivot) -> list[Segment]:
    idx = -1
    for i, p in enumerate(pivots):
        if p.time == anchor.time and p.price == anchor.price and p.kind == anchor.kind:
            idx = i
            break
    if idx < 0:
        logger.warning(
            "pivots_to_segments: anchor not found in pivots "
            "(time=%s price=%s kind=%s, n_pivots=%d) — returning empty segments",
            anchor.time, anchor.price, anchor.kind, len(pivots),
        )
        return []
    if idx >= len(pivots) - 1:
        logger.warning(
            "pivots_to_segments: anchor is the last pivot (idx=%d/%d) — "
            "no segments to derive",
            idx, len(pivots) - 1,
        )
        return []
    return [Segment(start=pivots[i], end=pivots[i + 1]) for i in range(idx, len(pivots) - 1)]


def count_waves(
    anchor: Pivot,
    segments: list[Segment],
    mode: ScaleMode,
    *,
    bars: list[Bar] | None = None,
    scoring_config: ScoringConfig | None = None,
    _dedup_user_form: bool = True,
    tracer: Tracer | None = None,
    beam_width: int | None = None,
    hard_timeout_ms: int | None = None,
    now: Callable[[], float] = time.monotonic,
) -> AnalysisReport:
    """Beam-search the wave count from an anchor + segments into a ranked AnalysisReport."""
    if mode not in ("linear", "log"):
        raise ValueError(
            f"count_waves: mode must be 'linear' or 'log', got {mode!r}"
        )

    bw, timeout_ms = _resolve_run_params(beam_width, hard_timeout_ms)
    runtime = RuntimeContext.from_bars(bars, scoring=scoring_config)

    if not segments:
        logger.info("count_waves: empty segments — returning empty report")
        return AnalysisReport(anchor=anchor)

    t_start = now()
    deadline = t_start + timeout_ms / 1000.0
    logger.info(
        "count_waves: parsing %d segments (mode=%s, beam=%d, budget=%dms)",
        len(segments),
        mode,
        bw,
        timeout_ms,
    )
    live: list[_Hypothesis] = seed_hypotheses(segments[0])
    diag = DiagnosticTracker()
    diag.observe_seed(live)

    if tracer is not None:
        tracer.emit(
            "seed",
            seg_index=0,
            detail=f"spawned {len(live)} hypotheses",
            n_live=len(live),
            families=sorted({h.top.family for h in live}),
        )

    timed_out = False
    timeout_at_segment = -1

    for i, s in enumerate(segments[1:], start=1):
        if now() > deadline:
            timed_out = True
            timeout_at_segment = i
            logger.warning(
                "count_waves: hard timeout at segment %d (budget=%dms, n_live=%d)",
                i,
                timeout_ms,
                len(live),
            )
            if tracer is not None:
                tracer.emit(
                    "timeout",
                    seg_index=i,
                    detail=f"hard timeout at segment {i}",
                    n_live=len(live),
                )
            break

        next_live, n_pre_beam = process_segment(
            live,
            s,
            mode,
            bw,
            runtime=runtime,
        )

        if tracer is not None:
            tracer.emit(
                "step",
                seg_index=i,
                detail=(
                    f"branched {len(live)}→{n_pre_beam}→{len(next_live)} "
                    f"(culled {n_pre_beam - len(next_live)})"
                ),
                n_live_in=len(live),
                n_pre_beam=n_pre_beam,
                n_live_out=len(next_live),
                n_culled=n_pre_beam - len(next_live),
                seg_direction=s.direction,
            )

        diag.observe_step(next_live, i)
        live = next_live
        if not live:
            logger.debug("count_waves: all hypotheses dead at segment %d", i)
            if tracer is not None:
                tracer.emit(
                    "step",
                    seg_index=i,
                    detail="all hypotheses dead",
                    n_live_out=0,
                )
            break

    # Skip under timeout — close_up itself can be expensive on a deep stack.
    if not timed_out:
        close_up_and_rescore(
            live,
            mode,
            tracer,
            runtime=runtime,
        )
        live = [h for h in live if not (h.root.is_complete and h.root.final_kind is None)]

    if tracer is not None:
        tracer.emit(
            "done",
            detail=(f"{len(live)} live hypotheses · timed_out={timed_out}"),
            n_live=len(live),
            timed_out=timed_out,
        )

    scenarios = [to_scenario(h, mode, runtime=runtime) for h in live]
    if _dedup_user_form:
        scenarios = dedup_user_visible_scenarios(scenarios)
    # Total order: tie-break equal scores on the content-hash id so the ranking
    # (and the top scenario shown) is deterministic regardless of upstream order.
    scenarios.sort(key=lambda sc: (-sc.score, sc.id))

    diag_report = build_diagnostic(
        scenarios_empty=not scenarios,
        timed_out=timed_out,
        timeout_at_segment=timeout_at_segment,
        n_segments=len(segments),
        first_divergence=diag.first_divergence,
        last_alive=diag.last_alive,
        root_completed_at=diag.root_completed_at,
        timeout_ms=timeout_ms,
    )

    logger.info(
        "count_waves: produced %d scenarios in %.1fms (timed_out=%s)",
        len(scenarios),
        (now() - t_start) * 1000.0,
        timed_out,
    )

    return AnalysisReport(
        anchor=anchor,
        segments=segments,
        scenarios=scenarios,
        diagnostic=diag_report,
    )


def _resolve_run_params(
    beam_width: int | None,
    hard_timeout_ms: int | None,
) -> tuple[int, int]:
    bw = BEAM_WIDTH if beam_width is None else max(1, int(beam_width))
    timeout_ms = HARD_TIMEOUT_MS if hard_timeout_ms is None else max(1, int(hard_timeout_ms))
    return bw, timeout_ms
