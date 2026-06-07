from analyst.serialization.slots import format_slot_grid


def test_format_slot_grid_ranks_checks_in_plain_words():
    components = {
        "speed_cluster": 0.823, "fib_push_pairs": 0.654,
        "pull_depth_discipline": 0.871, "pivot_sharpness": 0.712,
        "leg_smoothness": 0.589,
        "structural_total": 0.654, "visual_total": 0.589,
        "quality": 0.589, "commitment": 1.0, "total": 0.589,
    }
    md = format_slot_grid(components, bottleneck="leg_smoothness")
    assert "the swing smoothness check: weakest — the overall bottleneck" in md
    assert "the Fibonacci proportion check: 2nd-weakest" in md
    assert "the pullback depth check: strongest" in md
    assert "leg_smoothness" not in md
    assert "structural_total" not in md
    assert "0.589" not in md
    assert "visual-appearance side is the weaker" in md


def test_format_slot_grid_handles_no_checks():
    assert "No scoring checks" in format_slot_grid({}, bottleneck=None)
