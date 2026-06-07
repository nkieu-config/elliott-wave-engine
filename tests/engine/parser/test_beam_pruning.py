from __future__ import annotations

import uuid as _uuid
from datetime import datetime, timedelta

import pytest

from engine.parser import count_waves
from engine.parser.engine.dedup import _canonical_form, _dedup_and_beam
from engine.parser.types import _Context, _Hypothesis, _Leg
from engine.types import Pivot, Segment, WaveRole
from tests.fixtures import ip_pivot, make_segments


def test_beam_order_independent_of_input_order() -> None:
    def _mk(family: str, role: WaveRole, price_end: float) -> _Hypothesis:
        leg = _Leg(
            role,
            ip_pivot(0, 0, 100, "low"),
            ip_pivot(1, 1, price_end, "high"),
        )
        ctx = _Context(family=family, legs=[leg])
        h = _Hypothesis(id=f"{family}-{price_end}", context_stack=[ctx])
        h.score = 0.286  # arbitrary; equal across hyps so only ordering matters
        return h

    h_a = _mk("3W", WaveRole.S1, 130)
    h_b = _mk("5W_SIDEWAY", WaveRole.S1, 130)
    h_c = _mk("5W_TREND", WaveRole.S1, 130)

    order1 = [h_a, h_b, h_c]
    order2 = [h_c, h_a, h_b]
    order3 = [h_b, h_c, h_a]

    out1 = [h.root.family for h in _dedup_and_beam(order1)]
    out2 = [h.root.family for h in _dedup_and_beam(order2)]
    out3 = [h.root.family for h in _dedup_and_beam(order3)]

    assert out1 == out2 == out3, (
        f"beam ordering must be input-order-independent; got {out1} vs {out2} vs {out3}"
    )


def test_beam_score_remains_primary_key() -> None:
    def _mk(family: str, score: float) -> _Hypothesis:
        leg = _Leg(
            WaveRole.S1,
            ip_pivot(0, 0, 100, "low"),
            ip_pivot(1, 1, 130, "high"),
        )
        ctx = _Context(family=family, legs=[leg])
        h = _Hypothesis(id=f"{family}-{score}", context_stack=[ctx])
        h.score = score
        return h

    high = _mk("3W", 0.9)
    mid = _mk("5W_TREND", 0.5)
    low = _mk("5W_SIDEWAY", 0.1)

    out = _dedup_and_beam([low, mid, high])
    assert [h.score for h in out] == [0.9, 0.5, 0.1]


def test_beam_depth_breaks_ties_before_hash() -> None:
    seg_leg = _Leg(
        WaveRole.S1,
        ip_pivot(0, 0, 100, "low"),
        ip_pivot(1, 1, 130, "high"),
    )

    shallow = _Hypothesis(
        id="shallow",
        context_stack=[_Context(family="3W", legs=[seg_leg])],
    )
    shallow.score = 0.5

    deep_inner = _Context(family="3W", legs=[seg_leg], parent_role=WaveRole.S1)
    deep_outer = _Context(family="5W_TREND", legs=[])
    deep = _Hypothesis(
        id="deep",
        context_stack=[deep_outer, deep_inner],
    )
    deep.score = 0.5

    out = _dedup_and_beam([deep, shallow])
    assert out[0].id == "shallow", (
        f"Occam tiebreak: shallow must rank first when scores tie; got {[h.id for h in out]}"
    )


def test_beam_span_coverage_tertiary_tiebreak() -> None:
    short_leg = _Leg(
        WaveRole.S1,
        ip_pivot(0, 0, 100, "low"),
        ip_pivot(1, 5, 130, "high"),
    )
    long_leg = _Leg(
        WaveRole.S1,
        ip_pivot(2, 10, 100, "low"),
        ip_pivot(3, 30, 130, "high"),
    )

    short_h = _Hypothesis(
        id="aaa-short",
        context_stack=[_Context(family="5W_SIDEWAY", legs=[short_leg])],
    )
    short_h.score = 0.5
    long_h = _Hypothesis(
        id="zzz-long",
        context_stack=[_Context(family="3W", legs=[long_leg])],
    )
    long_h.score = 0.5

    out = _dedup_and_beam([short_h, long_h])
    assert out[0].id == "zzz-long", (
        f"span-coverage tiebreak: long-span (20 bars) must rank ahead of "
        f"short-span (5 bars) at equal score+depth; got {[h.id for h in out]}"
    )


def test_beam_quaternary_tiebreak_uses_canonical_form_not_id() -> None:
    leg = _Leg(
        WaveRole.S1,
        ip_pivot(0, 0, 100, "low"),
        ip_pivot(1, 1, 130, "high"),
    )
    h_3w = _Hypothesis(
        id="zzz-3w",
        context_stack=[_Context(family="3W", legs=[leg])],
    )
    h_3w.score = 0.5
    h_5wt = _Hypothesis(
        id="aaa-5wt",
        context_stack=[_Context(family="5W_TREND", legs=[leg])],
    )
    h_5wt.score = 0.5

    out = _dedup_and_beam([h_5wt, h_3w])
    assert out[0].root.family == "3W", (
        f"canonical-form tiebreak: '3W' should rank ahead of '5W_TREND' "
        f"by canonical-form lex order, regardless of id; got "
        f"{[h.id for h in out]}"
    )


def test_beam_reproducible_across_runs_with_random_uuids() -> None:
    leg = _Leg(
        WaveRole.S1,
        ip_pivot(0, 0, 100, "low"),
        ip_pivot(1, 1, 130, "high"),
    )

    def _build_set() -> list[_Hypothesis]:
        out: list[_Hypothesis] = []
        for fam in ("5W_TREND", "5W_SIDEWAY", "3W"):
            h = _Hypothesis(
                id=str(_uuid.uuid4()),
                context_stack=[_Context(family=fam, legs=[leg])],
            )
            h.score = 0.5
            out.append(h)
        return out

    canon_run_1 = [_canonical_form(h) for h in _dedup_and_beam(_build_set())]
    canon_run_2 = [_canonical_form(h) for h in _dedup_and_beam(_build_set())]
    canon_run_3 = [_canonical_form(h) for h in _dedup_and_beam(_build_set())]

    assert canon_run_1 == canon_run_2 == canon_run_3, (
        f"beam contents must be reproducible across runs (independent of "
        f"random UUIDs); got\n  run1: {canon_run_1}\n  run2: {canon_run_2}\n"
        f"  run3: {canon_run_3}"
    )


@pytest.mark.slow
def test_first_divergence_tracked_when_hypotheses_drop() -> None:
    p = [100.0, 200.0, 120.0, 180.0, 130.0, 160.0]
    segs = make_segments(p)
    anchor = segs[0].start
    report = count_waves(anchor, segs, "linear")
    assert report.diagnostic.last_alive_segment_index >= 0


@pytest.mark.slow
def test_first_divergence_minus_one_when_no_drop() -> None:
    segs = make_segments([100, 130])
    anchor = segs[0].start
    report = count_waves(anchor, segs, "linear")
    assert report.diagnostic.first_divergence_index == -1


@pytest.mark.slow
def test_first_divergence_set_when_all_die() -> None:
    pivots = [
        Pivot(i, datetime(2020, 1, 1) + timedelta(weeks=i), 100 + i * 10, "low", i)
        for i in range(5)
    ]
    segs = [Segment(pivots[i], pivots[i + 1]) for i in range(4)]
    anchor = pivots[0]
    report = count_waves(anchor, segs, "linear")
    assert not report.scenarios, "all-up input must kill every hypothesis"
    assert report.diagnostic.first_divergence_index >= 0
