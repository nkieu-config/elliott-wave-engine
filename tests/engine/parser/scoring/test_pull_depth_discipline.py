from __future__ import annotations

import pytest

from engine.parser.scoring.structural import pull_depth_discipline
from tests.engine.parser.scoring._helpers import _leg


class TestPullDepthDiscipline:
    def test_half_retracement_perfect(self):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (105, 15)),
        ]
        assert pull_depth_discipline(legs) == pytest.approx(1.0)

    def test_382_depth_perfect(self):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (106.18, 15)),
        ]
        assert pull_depth_discipline(legs) == pytest.approx(1.0)

    def test_too_deep_pull(self):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (100.5, 15)),
        ]
        s = pull_depth_discipline(legs)
        assert s is not None
        assert s < 0.2

    def test_too_shallow_pull(self):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (109, 12)),
        ]
        s = pull_depth_discipline(legs)
        assert s is not None
        assert s < 0.5

    def test_multiple_pairs_averaged(self):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (105, 15)),
            _leg((105, 15), (120, 30)),
            _leg((120, 30), (112.5, 35)),
        ]
        assert pull_depth_discipline(legs) == pytest.approx(1.0)

    def test_inactive_when_no_push_pull_pair(self):
        legs = [_leg((100, 0), (110, 10))]
        assert pull_depth_discipline(legs) is None

    def test_inactive_when_push_zero(self):
        legs = [
            _leg((100, 0), (100, 10)),
            _leg((100, 10), (95, 15)),
        ]
        assert pull_depth_discipline(legs) is None
