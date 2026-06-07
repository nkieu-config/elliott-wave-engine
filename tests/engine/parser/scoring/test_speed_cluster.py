from __future__ import annotations

import pytest

from engine.parser.scoring.structural import speed_cluster
from tests.engine.parser.scoring._helpers import _leg


class TestSpeedCluster:
    def test_perfectly_clustered_speeds(self):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (100, 20)),
            _leg((100, 20), (110, 30)),
        ]
        assert speed_cluster(legs) == pytest.approx(1.0)

    def test_inactive_when_fewer_than_two_legs(self):
        assert speed_cluster([]) is None
        assert speed_cluster([_leg((100, 0), (110, 10))]) is None

    def test_inactive_when_any_zero_bar_span(self):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (105, 10)),
        ]
        assert speed_cluster(legs) is None

    def test_inactive_when_any_zero_price(self):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (110, 20)),
        ]
        assert speed_cluster(legs) is None

    def test_spread_lowers_score(self):
        clustered = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (95, 25)),
        ]
        spread = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (95, 100)),
        ]
        sc = speed_cluster(clustered)
        ss = speed_cluster(spread)
        assert sc is not None and ss is not None
        assert sc > ss

    def test_score_in_unit_interval(self):
        legs = [
            _leg((100, 0), (200, 1)),
            _leg((200, 1), (199, 1000)),
        ]
        s = speed_cluster(legs)
        assert s is not None
        assert 0.0 <= s <= 1.0
