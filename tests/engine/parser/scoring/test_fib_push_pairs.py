from __future__ import annotations

import pytest

from engine.parser.scoring.structural import fib_push_pairs
from tests.engine.parser.scoring._helpers import _leg


class TestFibPushPairs:
    def test_two_pushes_at_perfect_618_ratio(self):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (105, 15)),
            _leg((105, 15), (121.18, 30)),
        ]
        assert fib_push_pairs(legs) == pytest.approx(1.0, abs=0.001)

    def test_two_pushes_at_perfect_equal(self):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (105, 15)),
            _leg((105, 15), (115, 25)),
        ]
        assert fib_push_pairs(legs) == pytest.approx(1.0, abs=0.001)

    def test_non_fib_ratio_scores_lower(self):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (105, 15)),
            _leg((105, 15), (119.2, 25)),
        ]
        s = fib_push_pairs(legs)
        assert s is not None
        assert s < 0.5

    def test_inactive_with_one_push(self):
        legs = [_leg((100, 0), (110, 10))]
        assert fib_push_pairs(legs) is None

    def test_inactive_when_push_has_zero_size(self):
        legs = [
            _leg((100, 0), (100, 10)),
            _leg((100, 10), (95, 15)),
            _leg((95, 15), (105, 25)),
        ]
        assert fib_push_pairs(legs) is None

    def test_three_pushes_averages_pair_scores(self):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (105, 15)),
            _leg((105, 15), (121.18, 30)),
            _leg((121.18, 30), (113.09, 39)),
            _leg((113.09, 39), (123.09, 49)),
        ]
        assert fib_push_pairs(legs) == pytest.approx(1.0, abs=0.01)
