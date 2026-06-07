from __future__ import annotations

import pytest

from engine.parser.scoring.structural import (
    fib_push_pairs,
    fib_push_pairs_verbose,
    pull_depth_discipline,
    pull_depth_discipline_verbose,
    speed_cluster,
    speed_cluster_verbose,
)
from engine.parser.scoring.visual import (
    leg_smoothness,
    leg_smoothness_verbose,
    pivot_sharpness,
    pivot_sharpness_verbose,
)

_STRUCTURAL_PAIRS = [
    (speed_cluster, speed_cluster_verbose),
    (fib_push_pairs, fib_push_pairs_verbose),
    (pull_depth_discipline, pull_depth_discipline_verbose),
]
_VISUAL_PAIRS = [
    (pivot_sharpness, pivot_sharpness_verbose),
    (leg_smoothness, leg_smoothness_verbose),
]


def _assert_consistent(scalar, verbose_result) -> None:
    verbose_value, intermediates = verbose_result
    assert scalar == verbose_value
    assert isinstance(intermediates, dict)
    if scalar is None:
        assert intermediates == {}
    else:
        assert intermediates, "an active slot must return non-empty intermediates"


@pytest.mark.parametrize(
    "scalar_fn,verbose_fn",
    _STRUCTURAL_PAIRS,
    ids=["speed_cluster", "fib_push_pairs", "pull_depth_discipline"],
)
def test_structural_scalar_matches_verbose(
    scalar_fn, verbose_fn, sample_hypothesis_with_bars
) -> None:
    h, _mode, _runtime = sample_hypothesis_with_bars
    legs = h.root.legs
    _assert_consistent(scalar_fn(legs), verbose_fn(legs))


@pytest.mark.parametrize(
    "scalar_fn,verbose_fn",
    _VISUAL_PAIRS,
    ids=["pivot_sharpness", "leg_smoothness"],
)
def test_visual_scalar_matches_verbose(
    scalar_fn, verbose_fn, sample_hypothesis_with_bars
) -> None:
    h, _mode, runtime = sample_hypothesis_with_bars
    legs = h.root.legs
    bars = runtime.bars
    _assert_consistent(scalar_fn(legs, bars), verbose_fn(legs, bars))
