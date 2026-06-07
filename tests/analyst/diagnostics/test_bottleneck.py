from analyst.diagnostics.bottleneck import diagnose_bottleneck


def test_diagnose_picks_lowest_active_slot():
    score_components = {
        "speed_cluster": 0.82,
        "fib_push_pairs": 0.65,
        "pull_depth_discipline": 0.87,
        "pivot_sharpness": 0.71,
        "leg_smoothness": 0.58,
        "structural_total": 0.65,
        "visual_total": 0.58,
        "intermediates": {
            "leg_smoothness": {"per_leg": [{"leg_idx": 0, "ratio": 0.4}]},
            "speed_cluster": {"leg_speeds": [1.0, 1.5]},
        },
    }
    bd = diagnose_bottleneck(score_components, "5W_TREND")
    assert bd.slot_name == "leg_smoothness"
    assert bd.dimension == "visual"
    assert bd.is_overall_minimum is True
    assert bd.theory_ref.binding == "heuristic"
    assert "swing smoothness" in bd.plain_explanation
    assert "leg_smoothness" not in bd.plain_explanation


def test_diagnose_gap_to_next():
    sc = {
        "speed_cluster": 0.5, "fib_push_pairs": 0.6,
        "pull_depth_discipline": 0.7, "structural_total": 0.5,
        "intermediates": {"speed_cluster": {"leg_speeds": [1, 2]}},
    }
    bd = diagnose_bottleneck(sc, "5W_TREND")
    assert abs(bd.gap_to_next - 0.1) < 1e-6


def test_speed_cluster_explanation_handles_zero_speed():
    sc = {
        "speed_cluster": 0.5,
        "fib_push_pairs": 0.9,
        "pull_depth_discipline": 0.9,
        "structural_total": 0.5,
        "intermediates": {"speed_cluster": {"leg_speeds": [0.0, 1.5]}},
    }
    bd = diagnose_bottleneck(sc, "5W_TREND")
    assert bd.slot_name == "speed_cluster"
    assert "extreme" in bd.plain_explanation


def test_is_overall_minimum_uses_quality_not_total():
    sc = {
        "speed_cluster": 0.8,
        "fib_push_pairs": 0.7,
        "pull_depth_discipline": 0.6,
        "structural_total": 0.6,
        "visual_total": 0.9,
        "quality": 0.6,
        "total": 0.6 * 0.4,
        "commitment": 0.4,
        "intermediates": {"pull_depth_discipline": {"pairs": []}},
    }
    bd = diagnose_bottleneck(sc, "5W_TREND")
    assert bd.slot_name == "pull_depth_discipline"
    assert bd.is_overall_minimum is True


def test_fib_push_pairs_bottleneck_cites_family_correct_pages():
    sc = {
        "speed_cluster": 0.9,
        "fib_push_pairs": 0.4,
        "pull_depth_discipline": 0.8,
        "structural_total": 0.4,
        "intermediates": {"fib_push_pairs": {"pairs": []}},
    }
    bd_trend = diagnose_bottleneck(sc, "5W_TREND")
    bd_side = diagnose_bottleneck(sc, "5W_SIDEWAY")
    assert bd_trend.slot_name == bd_side.slot_name == "fib_push_pairs"
    assert set(bd_trend.theory_ref.pages) == {101, 110}
    assert set(bd_side.theory_ref.pages) == {103, 111}
    assert 110 not in bd_side.theory_ref.pages
