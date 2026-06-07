from __future__ import annotations

from engine.parser import ROOT_FAMILIES
from engine.parser.engine import seed_hypotheses
from tests.fixtures import make_segments


def test_seed_spawns_at_least_one_root_family():
    segs = make_segments([100.0, 101.0, 100.5, 102.0])
    seeds = seed_hypotheses(segs[0])
    assert seeds, "seed pool must not be empty given one valid first segment"
    families = {h.root.family for h in seeds}
    assert families <= set(ROOT_FAMILIES), (
        f"seeds must only spawn known root families; got extras: {families - set(ROOT_FAMILIES)}"
    )


def test_seed_marks_depth_correctly():
    segs = make_segments([100.0, 101.0, 100.5, 102.0])
    seeds = seed_hypotheses(segs[0])
    for h in seeds:
        assert h.depth >= 1
        assert len(h.context_stack) == h.depth


def test_seed_consumes_first_segment():
    segs = make_segments([100.0, 101.0])
    seeds = seed_hypotheses(segs[0])
    for h in seeds:
        absorbed = any(len(ctx.legs) > 0 for ctx in h.context_stack)
        assert absorbed, "seed must place the first segment somewhere in context_stack"
