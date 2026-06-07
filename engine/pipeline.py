"""ATR ZigZag pivots → min-bar spacing → anchor → wave count → immutable PipelineResult.

Wave-count step is memoized (in-process LRU) so the stateless API can cheaply
re-resolve a client's scenario_id across requests.
"""

from __future__ import annotations

import copy
import threading
from collections import OrderedDict
from collections.abc import Sequence
from dataclasses import dataclass

from engine.anchor import find_anchor
from engine.parser import (
    AnalysisReport,
    ScoringConfig,
    count_waves,
    pivots_to_segments,
)
from engine.pivot import (
    compute_zigzag_pivots_atr,
    enforce_min_bars,
)
from engine.types import Bar, Pivot, ScaleMode


@dataclass(frozen=True)
class PipelineResult:
    # Frozen + tuple sequences so a consumer can't mutate downstream state.
    bars: tuple[Bar, ...]
    raw_pivots: tuple[Pivot, ...]
    spaced_pivots: tuple[Pivot, ...]
    active_pivots: tuple[Pivot, ...]
    selected_anchor: Pivot | None = None
    report: AnalysisReport | None = None
    load_error: str | None = None


# Wave-count memoization. Keyed on pivot identity (bar_index + price + kind) +
# config — price is in the key so same-index/different-price inputs can't collide.
# Small in-process LRU, thread-safe.
_PARSE_CACHE_MAX = 128
_parse_cache: OrderedDict[tuple, AnalysisReport | None] = OrderedDict()
_parse_cache_lock = threading.Lock()
_MISS = object()


def _count_waves_cached(
    *,
    anchor_id: tuple,
    active_pivot_ids: tuple[tuple, ...],
    bars_len: int,
    scale_mode: ScaleMode,
    atr_period: int,
    atr_multiplier: float,
    atr_floor: float,
    min_bars_between: int,
    scoring_config: ScoringConfig,
    _anchor: Pivot,
    _active_pivots: list[Pivot],
    _bars: list[Bar],
) -> AnalysisReport | None:
    # `_`-prefixed args are the live data used to compute; the remaining args
    # form the cache key (ScoringConfig is a frozen dataclass, so it hashes).
    key = (
        anchor_id,
        active_pivot_ids,
        bars_len,
        scale_mode,
        atr_period,
        atr_multiplier,
        atr_floor,
        min_bars_between,
        scoring_config,
    )
    with _parse_cache_lock:
        cached = _parse_cache.get(key, _MISS)
        if cached is not _MISS:
            _parse_cache.move_to_end(key)
            # Copy so a caller mutating a Scenario/report can't poison the cache.
            return copy.deepcopy(cached)

    # Compute outside the lock so distinct parses don't serialize on each other.
    segments = pivots_to_segments(_active_pivots, _anchor)
    result: AnalysisReport | None = (
        None
        if not segments
        else count_waves(
            _anchor,
            segments,
            scale_mode,
            bars=_bars,
            scoring_config=scoring_config,
        )
    )

    with _parse_cache_lock:
        _parse_cache[key] = result
        _parse_cache.move_to_end(key)
        while len(_parse_cache) > _PARSE_CACHE_MAX:
            _parse_cache.popitem(last=False)
    # Hand back a copy; the cache keeps the pristine original (never handed out).
    return copy.deepcopy(result)


def clear_parser_cache() -> None:
    with _parse_cache_lock:
        _parse_cache.clear()


def _invoke_count_waves(
    *,
    anchor: Pivot,
    active_pivots: Sequence[Pivot],
    bars: Sequence[Bar],
    scale_mode: ScaleMode,
    atr_period: int,
    atr_multiplier: float,
    atr_floor: float,
    min_bars_between: int,
    scoring_config: ScoringConfig,
) -> AnalysisReport | None:
    # Round floats to slider precision so identical inputs share a cache entry.
    return _count_waves_cached(
        anchor_id=(anchor.bar_index, round(anchor.price, 6), anchor.kind),
        active_pivot_ids=tuple(
            (p.bar_index, round(p.price, 6), p.kind) for p in active_pivots
        ),
        bars_len=len(bars),
        scale_mode=scale_mode,
        atr_period=int(atr_period),
        atr_multiplier=round(atr_multiplier, 2),
        atr_floor=round(atr_floor, 2),
        min_bars_between=int(min_bars_between),
        scoring_config=scoring_config,
        _anchor=anchor,
        _active_pivots=list(active_pivots),
        _bars=list(bars),
    )


def _run_pipeline_pure(
    *,
    bars: Sequence[Bar],
    scale_mode: ScaleMode,
    atr_period: int,
    atr_multiplier: float,
    atr_floor: float,
    min_bars_between: int,
    scoring_config: ScoringConfig,
    load_error: str | None,
) -> PipelineResult:
    bars_list = list(bars)
    if not bars_list:
        raw_pivots: list[Pivot] = []
    else:
        raw_pivots = compute_zigzag_pivots_atr(
            bars_list,
            atr_period=atr_period,
            atr_multiplier=atr_multiplier,
            floor_threshold=atr_floor,
        )

    spaced_pivots = enforce_min_bars(
        raw_pivots,
        min_bars=min_bars_between,
    )
    active_pivots = spaced_pivots
    selected_anchor = find_anchor(active_pivots)

    report: AnalysisReport | None = None
    if selected_anchor is not None:
        report = _invoke_count_waves(
            anchor=selected_anchor,
            active_pivots=active_pivots,
            bars=bars_list,
            scale_mode=scale_mode,
            atr_period=atr_period,
            atr_multiplier=atr_multiplier,
            atr_floor=atr_floor,
            min_bars_between=min_bars_between,
            scoring_config=scoring_config,
        )

    return PipelineResult(
        bars=tuple(bars_list),
        raw_pivots=tuple(raw_pivots),
        spaced_pivots=tuple(spaced_pivots),
        active_pivots=tuple(active_pivots),
        selected_anchor=selected_anchor,
        report=report,
        load_error=load_error,
    )


def run_pipeline(
    *,
    bars: Sequence[Bar],
    scale_mode: ScaleMode,
    min_bars_between: int,
    atr_period: int = 14,
    atr_multiplier: float = 3.0,
    atr_floor: float = 0.10,
    scoring_config: ScoringConfig | None = None,
    load_error: str | None = None,
) -> PipelineResult:
    """Run the full pipeline: bars → ATR-zigzag pivots → beam wave-count → scored scenarios."""
    return _run_pipeline_pure(
        bars=bars,
        scale_mode=scale_mode,
        atr_period=atr_period,
        atr_multiplier=atr_multiplier,
        atr_floor=atr_floor,
        min_bars_between=min_bars_between,
        scoring_config=scoring_config or ScoringConfig(),
        load_error=load_error,
    )
