from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np

from engine.parser.output.types import Scenario
from engine.types import Bar, OpenState, PatternKind, Pivot, WaveNode, WaveRole


class FakeEmbedder:
    """encode() ignores is_query; row per text from `vectors`, else `default`."""

    def __init__(self, vectors=None, *, default=(1.0, 0.0, 0.0)):
        self.vectors = vectors or {}
        self.default = default
        self.last_is_query = None

    def encode(self, texts, *, is_query: bool = False) -> np.ndarray:
        self.last_is_query = is_query
        rows = [self.vectors.get(t, self.default) for t in texts]
        return np.array(rows, dtype=np.float32)


def make_uptrend_then_drop_bars(n: int = 250) -> list[Bar]:
    """Synthetic series: rising 0.5/bar until bar 200, then falling 1.0/bar."""
    bars: list[Bar] = []
    for i in range(n):
        p = 100 + i * 0.5 if i < 200 else bars[199].close - (i - 199) * 1.0
        bars.append(Bar(time=datetime(2020, 1, 1) + timedelta(days=i),
                        open=p, high=p + 0.5, low=p - 0.5, close=p, volume=0))
    return bars


def _pv(idx: int, price: float, bar_idx: int, kind: str = "high") -> Pivot:
    return Pivot(
        index=idx,
        time=datetime(2020, 1, 1) + timedelta(days=bar_idx),
        price=price,
        kind=kind,
        bar_index=bar_idx,
    )


_DEFAULT_SCORE_COMPONENTS: dict[str, float] = {
    "speed_cluster": 0.8,
    "fib_push_pairs": 0.7,
    "pull_depth_discipline": 0.6,
    "structural_total": 0.6,
}

_DEFAULT_5WT_PIVOTS: list[tuple[float, int, str]] = [
    (100.0, 0, "low"),
    (140.0, 40, "high"),
    (120.0, 50, "low"),
    (180.0, 100, "high"),
    (150.0, 130, "low"),
    (200.0, 200, "high"),
]


def make_scenario(
    *,
    family: str = "5W_TREND",
    pattern_kind: PatternKind | None = PatternKind.FIVE_TREND_S3_LONGEST,
    pivots: list[tuple[float, int, str]] | None = None,
    score: float = 0.5,
    scenario_id: str = "t1",
    score_components: dict[str, float] | None = None,
    sets: list | None = None,
) -> Scenario:
    """Defaults: canonical 6-pivot/5-leg 5W_TREND. ``sets`` attaches to the root
    WaveNode (LINK_T/LINK_S need it), not Scenario (which has no such field)."""
    if pivots is None:
        pivots = _DEFAULT_5WT_PIVOTS
    pvs = [_pv(i, price, bar_idx, kind)
           for i, (price, bar_idx, kind) in enumerate(pivots)]
    root = WaveNode(
        role=WaveRole.ANCHOR,
        span_start=pvs[0],
        span_end=pvs[-1],
        pattern_kind=pattern_kind,
    )
    if sets is not None:
        root.sets = sets
    for i in range(len(pvs) - 1):
        # s1..s5 then LINK for legs beyond the 5th (LINK_T / LINK_S scenarios).
        role = WaveRole(f"s{i + 1}") if i < 5 else WaveRole.LINK
        leg = WaveNode(role=role, span_start=pvs[i], span_end=pvs[i + 1])
        root.children.append(leg)
    sc = Scenario(
        id=scenario_id,
        root=root,
        score=score,
        open_state=OpenState(),
        _family=family,
    )
    sc.score_components = (
        dict(score_components)
        if score_components is not None
        else dict(_DEFAULT_SCORE_COMPONENTS)
    )
    return sc
