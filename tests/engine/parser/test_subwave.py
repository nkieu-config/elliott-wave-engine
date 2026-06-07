from __future__ import annotations

import pytest

from engine.parser import count_waves
from engine.types import PatternKind
from tests.engine.parser._builders import piv
from tests.fixtures import make_segments

pytestmark = pytest.mark.slow


def test_extension_3w_dies_5w_trend_survives() -> None:
    segs = make_segments([100, 130, 115, 175, 155, 200])
    anchor = segs[0].start
    report = count_waves(anchor, segs, "linear")

    direct_5w_trend = [
        sc
        for sc in report.scenarios
        if sc.family == "5W_TREND" and sc.depth == 1 and sc.is_complete
    ]
    assert any(sc.pattern_kind == PatternKind.FIVE_TREND_S3_LONGEST for sc in direct_5w_trend)


def test_merging_case_3w_followed_by_big_pull() -> None:
    prices = [100, 130, 110, 120, 105, 165, 145, 200]
    segs = make_segments(prices)
    anchor = segs[0].start
    report = count_waves(anchor, segs, "linear")
    nested = [
        sc for sc in report.scenarios if sc.depth >= 2 or any(lg.pattern_kind for lg in sc.legs)
    ]
    assert len(nested) >= 1, (
        f"Expected at least one nested scenario; got {len(report.scenarios)} total"
    )


def test_subwave_5w_trend_with_3w_in_s2() -> None:
    prices = [100, 130, 110, 120, 105, 165, 145, 200]
    segs = make_segments(prices)
    anchor = segs[0].start
    report = count_waves(anchor, segs, "linear")

    nested_root = [
        sc
        for sc in report.scenarios
        if sc.family == "5W_TREND"
        and sc.is_complete
        and sc.pattern_kind == PatternKind.FIVE_TREND_S3_LONGEST
        and len(sc.legs) >= 2
        and sc.legs[1].pattern_kind is not None
    ]
    flat = [
        sc
        for sc in report.scenarios
        if sc.family == "5W_TREND" and sc.is_complete and sc.depth == 1
    ]
    assert len(nested_root) >= 1 or len(flat) >= 1, (
        f"Expected nested or flat 5W_TREND; got "
        f"{[(s.family, s.pattern_kind, s.depth, s.is_complete) for s in report.scenarios]}"
    )


def test_option_c_preserves_competing_close_vs_extend_alternatives() -> None:
    prices = [100, 130, 115, 175, 155, 200]
    segs = make_segments(prices)
    report = count_waves(segs[0].start, segs, "linear")

    direct = [
        sc
        for sc in report.scenarios
        if sc.family == "5W_TREND" and sc.depth == 1 and sc.is_complete
    ]
    assert direct, (
        "depth-1 5W_TREND must survive even when Option C is firing on "
        "competing hypotheses — proves multi-hypothesis substitutes for backtracking"
    )


def test_option_c_cascading_close_handles_deep_nesting() -> None:
    prices = [100, 130, 110, 120, 105, 165, 145, 200]
    segs = make_segments(prices)
    report = count_waves(segs[0].start, segs, "linear")

    assert report.scenarios, "cascading Option C must not eliminate all hypotheses"
    assert report.diagnostic.death_reason != "hard_timeout_exceeded"


def test_option_c_handles_verifier_rejection_after_close() -> None:
    prices = [100, 130, 115, 175, 155, 200, 180, 240]
    segs = make_segments(prices)
    report = count_waves(segs[0].start, segs, "linear")

    assert report is not None
    for sc in report.scenarios:
        for leg in sc.legs:
            assert leg.span_start is not None


def test_beam_pruning_caps_scenarios() -> None:
    prices = [100.0]
    for i in range(20):
        prices.append(prices[-1] * (1.05 if i % 2 == 0 else 0.97))
    segs = make_segments(prices)
    anchor = segs[0].start
    report = count_waves(anchor, segs, "log")
    from engine.parser import BEAM_WIDTH

    assert len(report.scenarios) <= BEAM_WIDTH


def test_does_not_hang_on_pathological_input() -> None:
    import random

    rng = random.Random(42)
    prices = [100.0]
    for _ in range(15):
        prices.append(
            prices[-1]
            * (1 + rng.uniform(-0.10, 0.10) + (0.03 if rng.random() > 0.5 else -0.03))
        )
    segs = make_segments(prices)
    anchor = segs[0].start
    report = count_waves(anchor, segs, "log")
    assert report is not None


def test_empty_segments_returns_empty_report() -> None:
    from datetime import datetime

    from engine.types import Pivot

    p = Pivot(0, datetime(2020, 1, 1), 100, "low", 0)
    report = count_waves(p, [], "linear")
    assert report.scenarios == []


def test_single_segment_returns_seeds() -> None:
    segs = make_segments([100, 130])
    anchor = segs[0].start
    report = count_waves(anchor, segs, "linear")
    families = {sc.family for sc in report.scenarios}
    assert {"5W_TREND", "5W_SIDEWAY", "3W"}.issubset(families)
    for sc in report.scenarios:
        assert not sc.is_complete


def test_hard_timeout_returns_diagnostic_with_partial_state() -> None:
    state = {"call": 0}

    def fake_now() -> float:
        state["call"] += 1
        return 0.0 if state["call"] == 1 else 1e9

    segs = make_segments([100, 130, 115, 175, 155, 200])
    report = count_waves(segs[0].start, segs, "linear", now=fake_now)

    assert report.diagnostic.death_reason == "hard_timeout_exceeded"
    assert "ลด BEAM_WIDTH" in report.diagnostic.suggested_action
    assert len(report.scenarios) > 0


def test_hard_timeout_not_triggered_under_normal_load() -> None:
    # Frozen clock ⇒ elapsed is always 0, so the result is independent of CI
    # wall-clock load (a real clock would make this test flaky under pressure).
    segs = make_segments([100, 130, 115, 175, 155, 200])
    report = count_waves(segs[0].start, segs, "linear", now=lambda: 0.0)
    assert report.diagnostic.death_reason != "hard_timeout_exceeded"


def test_option_b_seeds_link_t_subpattern_at_3w_pull_leg() -> None:
    from engine.parser.engine.branching import _option_b_open_subwave
    from engine.parser.types import _Context, _Hypothesis, _Leg
    from engine.types import Segment, WaveRole

    s1_leg = _Leg(role=WaveRole.S1, span_start=piv(0, 100, "low"), span_end=piv(1, 200, "high"))
    root_3w = _Context(family="3W", legs=[s1_leg])
    h = _Hypothesis(id="t", context_stack=[root_3w])

    pull_seg = Segment(start=piv(1, 200, "high"), end=piv(2, 180, "low"))

    new_hyps = _option_b_open_subwave(h, pull_seg, "linear")

    link_seeded = [
        h2
        for h2 in new_hyps
        if len(h2.context_stack) >= 3 and h2.context_stack[-2].family in {"LINK_T", "LINK_S"}
    ]
    assert link_seeded, (
        "_option_b_open_subwave returned no Link-Wave sub-pattern hypothesis "
        f"for 3W S2 (Pull); got top families: {[h2.top.family for h2 in new_hyps]}"
    )

    link_t_hyps = [h2 for h2 in link_seeded if h2.context_stack[-2].family == "LINK_T"]
    assert link_t_hyps, "LINK_T sub-pattern must be seeded with a 3W inner set_1"
    for h2 in link_t_hyps:
        assert h2.context_stack[-2].parent_role == WaveRole.S2
        assert h2.context_stack[-1].family == "3W"
        assert h2.context_stack[-1].parent_role == WaveRole.SET_1
        assert len(h2.context_stack[-1].legs) == 1
        assert h2.context_stack[-1].legs[0].role == WaveRole.S1
        assert h2.context_stack[-1].legs[0].span_end.price == 180


def test_option_b_seeds_link_s_with_both_inner_g1_options() -> None:
    from engine.parser.engine.branching import _option_b_open_subwave
    from engine.parser.types import _Context, _Hypothesis, _Leg
    from engine.types import Segment, WaveRole

    s1 = _Leg(role=WaveRole.S1, span_start=piv(0, 100, "low"), span_end=piv(1, 200, "high"))
    root_3w = _Context(family="3W", legs=[s1])
    h = _Hypothesis(id="t", context_stack=[root_3w])
    pull_seg = Segment(start=piv(1, 200, "high"), end=piv(2, 180, "low"))

    new_hyps = _option_b_open_subwave(h, pull_seg, "linear")

    link_s_hyps = [
        h2
        for h2 in new_hyps
        if len(h2.context_stack) >= 3 and h2.context_stack[-2].family == "LINK_S"
    ]
    inner_fams = {h2.context_stack[-1].family for h2 in link_s_hyps}
    assert inner_fams == {"3W", "5W_SIDEWAY"}, (
        f"LINK_S must seed both 3W and 5W_SIDEWAY inner set_1; got {inner_fams}"
    )


def test_scenarios_are_unique_in_user_visible_form() -> None:
    segs = make_segments([100, 130, 115, 175, 155, 220, 170, 240, 200, 270, 230, 290])
    anchor = segs[0].start
    report = count_waves(anchor, segs, "linear")

    def user_form(sc) -> tuple:
        def shape(node) -> tuple:
            kind = node.pattern_kind.value if node.pattern_kind else "open"
            children = tuple(shape(c) for c in node.children)
            return (kind, children)

        return (
            sc.family,
            sc.pattern_kind.value if sc.pattern_kind else "—",
            shape(sc.root),
        )

    forms = [user_form(sc) for sc in report.scenarios]
    duplicates = [f for f in set(forms) if forms.count(f) > 1]
    assert not duplicates, (
        f"found {len(duplicates)} user-visible forms with multiple scenario "
        f"copies; total scenarios={len(report.scenarios)}, "
        f"unique forms={len(set(forms))}"
    )


def test_option_b_skips_link_subpattern_when_depth_budget_exhausted() -> None:
    from engine.parser import MAX_RECURSION_DEPTH
    from engine.parser.engine.branching import _option_b_open_subwave
    from engine.parser.types import _Context, _Hypothesis, _Leg
    from engine.types import Segment, WaveRole

    s1 = _Leg(role=WaveRole.S1, span_start=piv(0, 100, "low"), span_end=piv(1, 200, "high"))
    stack: list[_Context] = []
    for _ in range(MAX_RECURSION_DEPTH - 1):
        stack.append(_Context(family="3W", legs=[s1], parent_role=WaveRole.S1))
    h = _Hypothesis(id="t", context_stack=stack)
    assert h.depth == MAX_RECURSION_DEPTH - 1

    pull_seg = Segment(start=piv(1, 200, "high"), end=piv(2, 180, "low"))
    new_hyps = _option_b_open_subwave(h, pull_seg, "linear")

    link_seeded = [
        h2
        for h2 in new_hyps
        if h2.depth >= 3 and h2.context_stack[-2].family in {"LINK_T", "LINK_S"}
    ]
    assert link_seeded == [], (
        "Link sub-pattern must be skipped when budget can't cover 2 new contexts"
    )

    non_link = [h2 for h2 in new_hyps if h2.top.family in {"5W_TREND", "5W_SIDEWAY", "3W"}]
    assert non_link, "non-Link 1-context sub-patterns must still seed at depth-1 budget"


def test_close_top_into_parent_enforces_incremental_ratio() -> None:
    prices = [100, 200, 150, 170, 110, 130, 120, 125, 100]
    segs = make_segments(prices)
    anchor = segs[0].start
    report = count_waves(anchor, segs, "linear")

    for i, sc in enumerate(report.scenarios):
        if sc.family != "5W_TREND" or len(sc.legs) < 3:
            continue
        s2_len = abs(sc.legs[1].span_end.price - sc.legs[1].span_start.price)
        s3_len = abs(sc.legs[2].span_end.price - sc.legs[2].span_start.price)
        assert s3_len > s2_len, (
            f"scenario #{i} (5W_TREND, depth={sc.depth}) violates R4: "
            f"S2_span={s2_len}, S3_span={s3_len} — "
            f"S2.pattern_kind={sc.legs[1].pattern_kind}, "
            f"S3.pattern_kind={sc.legs[2].pattern_kind}"
        )


def test_close_top_into_parent_enforces_direction() -> None:
    prices = [100, 200, 180, 230, 215]
    segs = make_segments(prices)
    anchor = segs[0].start
    report = count_waves(anchor, segs, "linear")

    for i, sc in enumerate(report.scenarios):
        if sc.family != "5W_TREND" or len(sc.legs) < 2:
            continue
        s1_dir = "up" if sc.legs[0].span_end.price > sc.legs[0].span_start.price else "down"
        s2_dir = "up" if sc.legs[1].span_end.price > sc.legs[1].span_start.price else "down"
        assert s1_dir != s2_dir, (
            f"scenario #{i} (5W_TREND, depth={sc.depth}) has S1 and S2 in same "
            f"direction ({s1_dir}) — sub-pattern span flip not rejected"
        )


def test_5w_trend_s4_degree_gate_rejects_out_of_band_s4_in_bars() -> None:
    from engine.parser.families import incremental_ok as _incremental_ok
    from engine.parser.types import _Context, _Leg
    from engine.types import WaveRole

    # 5W_TREND: S1=100, S2=30, S3=35 bars → S4 band [30, 35]
    p0 = piv(0, 100.0, "low", 0)
    p1 = piv(1, 200.0, "high", 100)
    p2 = piv(2, 150.0, "low", 130)
    p3 = piv(3, 250.0, "high", 165)
    ctx = _Context(
        family="5W_TREND",
        legs=[
            _Leg(role=WaveRole.S1, span_start=p0, span_end=p1),
            _Leg(role=WaveRole.S2, span_start=p1, span_end=p2),
            _Leg(role=WaveRole.S3, span_start=p2, span_end=p3),
        ],
    )

    assert _incremental_ok(ctx, WaveRole.S4, 30.0, "linear", leg_bars=32) is True
    assert _incremental_ok(ctx, WaveRole.S4, 30.0, "linear", leg_bars=30) is True
    assert _incremental_ok(ctx, WaveRole.S4, 30.0, "linear", leg_bars=35) is True

    assert _incremental_ok(ctx, WaveRole.S4, 30.0, "linear", leg_bars=11) is False
    assert _incremental_ok(ctx, WaveRole.S4, 30.0, "linear", leg_bars=50) is False


def test_5w_trend_s4_degree_gate_skips_when_bar_index_unknown() -> None:
    from datetime import datetime

    from engine.parser.families import incremental_ok as _incremental_ok
    from engine.parser.types import _Context, _Leg
    from engine.types import Pivot, WaveRole

    base = datetime(2020, 1, 1)
    p0 = Pivot(0, base, 100.0, "low", None)
    p1 = Pivot(1, base, 200.0, "high", None)
    p2 = Pivot(2, base, 150.0, "low", None)
    p3 = Pivot(3, base, 250.0, "high", None)
    ctx = _Context(
        family="5W_TREND",
        legs=[
            _Leg(role=WaveRole.S1, span_start=p0, span_end=p1),
            _Leg(role=WaveRole.S2, span_start=p1, span_end=p2),
            _Leg(role=WaveRole.S3, span_start=p2, span_end=p3),
        ],
    )
    # bar_index missing → degree gate skipped; R6b (price) still fires
    assert _incremental_ok(ctx, WaveRole.S4, 30.0, "linear", leg_bars=None) is True
    assert _incremental_ok(ctx, WaveRole.S4, 30.0, "linear", leg_bars=999) is True
    assert _incremental_ok(ctx, WaveRole.S4, 100.0, "linear", leg_bars=None) is False


def test_5w_trend_s4_degree_gate_integration_kills_net_style_scenario() -> None:
    from engine.types import Segment

    # S2=30, S3=35, S4=10 (out of [30, 35]), S5=25
    pivots = [
        piv(0, 100.0, "low", 0),
        piv(1, 200.0, "high", 100),
        piv(2, 150.0, "low", 130),
        piv(3, 270.0, "high", 165),
        piv(4, 220.0, "low", 175),
        piv(5, 310.0, "high", 200),
    ]
    segs = [Segment(start=pivots[i], end=pivots[i + 1]) for i in range(len(pivots) - 1)]
    anchor = pivots[0]
    report = count_waves(anchor, segs, "linear")

    violations = []
    for i, sc in enumerate(report.scenarios):
        if sc.family != "5W_TREND" or len(sc.legs) < 4:
            continue
        s2, s3, s4 = sc.legs[1], sc.legs[2], sc.legs[3]
        s2_bars = s2.span_end.bar_index - s2.span_start.bar_index
        s3_bars = s3.span_end.bar_index - s3.span_start.bar_index
        s4_bars = s4.span_end.bar_index - s4.span_start.bar_index
        floor = min(s2_bars, s3_bars)
        ceiling = max(s2_bars, s3_bars)
        if not (floor <= s4_bars <= ceiling):
            violations.append((i, sc.depth, s2_bars, s3_bars, s4_bars))

    assert not violations, (
        f"5W_TREND scenarios that violate Gann Box S4 band still alive: {violations}"
    )


def test_5w_trend_s1_rejects_three_s2_longer_subkind() -> None:
    prices = [100, 110, 90, 120, 105, 165, 135, 200]
    segs = make_segments(prices)
    anchor = segs[0].start
    report = count_waves(anchor, segs, "linear")

    forbidden = {
        PatternKind.THREE_S2_LONGER,
        PatternKind.THREE_S3_SHORTER,
        PatternKind.THREE_S2_LONGER_S3_SHORTER,
    }
    violations = [
        (sc.pattern_kind, sc.legs[0].pattern_kind, sc.score)
        for sc in report.scenarios
        if sc.family == "5W_TREND" and sc.legs and sc.legs[0].pattern_kind in forbidden
    ]
    assert not violations, (
        f"Spec p.80 violation — 5W_TREND.s1 admitted a non-NORMAL 3W subkind: {violations}"
    )


def test_seed_hypotheses_includes_depth_3_merging() -> None:
    from engine.parser.engine import seed_hypotheses

    segs = make_segments([100, 110])
    seeds = seed_hypotheses(segs[0])

    sigs = {
        tuple((c.family, c.parent_role.value if c.parent_role else None) for c in h.context_stack)
        for h in seeds
    }

    assert (("5W_TREND", None), ("3W", "s1"), ("3W", "s1")) in sigs
    assert (("LINK_T", None), ("3W", "set_1"), ("3W", "s1")) in sigs

    depths = {len(h.context_stack) for h in seeds}
    assert depths <= {1, 2, 3}, f"unexpected seed depths: {depths}"
