"""Deterministic scenario-id invariant (Phase-A fix).

The stateless API re-runs the pipeline to resolve a client's `scenario_id`, so
shared links must survive cache eviction / restarts — ids must derive from
structure, not parse time. Pins both halves: stable across a genuine re-parse,
unique within a run. A regression (e.g. reverting to uuid4) fails loudly.
"""

from __future__ import annotations

import pytest

from engine.parser import ScoringConfig
from engine.pipeline import clear_parser_cache, run_pipeline


def _scenario_ids(bars) -> list[str]:
    res = run_pipeline(
        bars=bars,
        scale_mode="linear",
        atr_period=14,
        atr_multiplier=3.0,
        atr_floor=0.10,
        min_bars_between=4,
        scoring_config=ScoringConfig(),
    )
    return [s.id for s in (res.report.scenarios if res.report else [])]


@pytest.mark.slow
def test_scenario_ids_stable_across_reparse(bars):
    ids1 = _scenario_ids(bars)
    clear_parser_cache()  # drop the memo so the next call truly re-parses
    ids2 = _scenario_ids(bars)
    assert ids1, "expected at least one scenario"
    assert ids1 == ids2


@pytest.mark.slow
def test_scenario_ids_unique(bars):
    ids = _scenario_ids(bars)
    # >1 so uniqueness isn't vacuously true on a thin single-scenario parse.
    assert len(ids) > 1, "expected multiple scenarios to make uniqueness meaningful"
    assert len(set(ids)) == len(ids)
