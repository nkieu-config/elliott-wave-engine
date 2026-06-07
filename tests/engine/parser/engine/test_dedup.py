from __future__ import annotations

from engine.parser.engine import seed_hypotheses
from engine.parser.engine.dedup import _canonical_form, _dedup_and_beam
from tests.fixtures import make_segments


def test_canonical_form_is_hashable():
    segs = make_segments([100.0, 101.0, 100.5, 102.0])
    for h in seed_hypotheses(segs[0]):
        d = {_canonical_form(h): 1}
        assert d


def test_dedup_and_beam_caps_population():
    segs = make_segments([100.0, 101.0, 100.5, 102.0])
    pool = seed_hypotheses(segs[0])
    capped = _dedup_and_beam(pool, beam_width=2)
    assert len(capped) <= 2


def test_dedup_preserves_scoring_invariants():
    segs = make_segments([100.0, 101.0])
    pool = seed_hypotheses(segs[0])
    assert pool
    out = _dedup_and_beam(pool, beam_width=10)
    assert out, "a non-empty pool must yield at least one survivor"
    assert len(out) <= len(pool)
    pool_ids = {id(h) for h in pool}
    assert all(id(h) in pool_ids for h in out), "survivors must come from the input pool"
    # Dedup ranks by score descending (see dedup.py _dedup_and_beam) — that
    # ordering is the contract beam pruning relies on, so pin it directly.
    scores = [h.score for h in out]
    assert scores == sorted(scores, reverse=True), f"survivors not score-ranked: {scores}"
