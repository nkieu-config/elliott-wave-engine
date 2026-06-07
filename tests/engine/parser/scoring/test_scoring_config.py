from __future__ import annotations

import pytest

from engine.parser.runtime import RuntimeContext
from engine.parser.scoring import _score_components
from engine.parser.scoring.structural import (
    fib_push_pairs,
    pull_depth_discipline,
    speed_cluster,
)
from engine.parser.scoring_config import ScoringConfig
from tests.engine.parser.scoring._helpers import _leg
from tests.fixtures import build_hypothesis_with_legs


class TestDefaults:
    def test_default_config_pins_canonical_scalars(self):
        # ScoringConfig is the single source of truth for these scalars; pin the
        # canonical defaults so an accidental change is a deliberate test update.
        cfg = ScoringConfig()
        assert cfg.k_sigma == 0.5
        assert cfg.log_tol_fib == 0.05
        assert cfg.pull_depth_lo == 0.382
        assert cfg.pull_depth_hi == 0.618
        assert cfg.pull_depth_tol == 0.15
        assert cfg.pivot_window == 2

    def test_runtime_carries_default_config(self):
        rt = RuntimeContext.from_bars(None)
        assert isinstance(rt.scoring, ScoringConfig)
        assert rt.scoring == ScoringConfig()

    @pytest.mark.parametrize(
        "fn",
        [speed_cluster, fib_push_pairs, pull_depth_discipline],
        ids=["speed_cluster", "fib_push_pairs", "pull_depth_discipline"],
    )
    def test_slot_with_no_config_matches_slot_with_default_config(self, fn):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (105, 15)),
            _leg((105, 15), (115, 25)),
        ]
        assert fn(legs) == fn(legs, ScoringConfig())


class TestKSigma:
    def test_tighter_k_sigma_lowers_speed_cluster_for_irregular_paces(self):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (104, 15)),
            _leg((104, 15), (118, 22)),
        ]
        loose = ScoringConfig(k_sigma=0.5)
        tight = ScoringConfig(k_sigma=0.1)
        v_loose = speed_cluster(legs, loose)
        v_tight = speed_cluster(legs, tight)
        assert v_loose is not None and v_tight is not None
        assert v_tight < v_loose


class TestPullDepthWindow:
    def test_wider_window_raises_pull_score_for_borderline_depth(self):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (107, 15)),
        ]
        narrow = ScoringConfig(pull_depth_lo=0.382, pull_depth_hi=0.618)
        wide = ScoringConfig(pull_depth_lo=0.20, pull_depth_hi=0.70)
        v_narrow = pull_depth_discipline(legs, narrow)
        v_wide = pull_depth_discipline(legs, wide)
        assert v_narrow is not None and v_wide is not None
        assert v_wide > v_narrow


class TestLogTolFib:
    def test_tighter_tolerance_lowers_score_for_off_fib_ratios(self):
        legs = [
            _leg((100, 0), (110, 10)),
            _leg((110, 10), (105, 15)),
            _leg((105, 15), (120, 25)),
        ]
        loose = ScoringConfig(log_tol_fib=0.05)
        tight = ScoringConfig(log_tol_fib=0.01)
        v_loose = fib_push_pairs(legs, loose)
        v_tight = fib_push_pairs(legs, tight)
        assert v_loose is not None and v_tight is not None
        assert v_tight < v_loose


class TestOrchestrator:
    def test_score_components_uses_runtime_scoring(self):
        h = build_hypothesis_with_legs(
            [
                _leg((100, 0), (110, 10)),
                _leg((110, 10), (104, 15)),
                _leg((104, 15), (118, 22)),
            ]
        )
        rt_default = RuntimeContext.from_bars(None)
        rt_tight = RuntimeContext.from_bars(
            None,
            scoring=ScoringConfig(k_sigma=0.1),
        )
        c_default = _score_components(h, "linear", runtime=rt_default)
        c_tight = _score_components(h, "linear", runtime=rt_tight)
        assert c_default["speed_cluster"] != pytest.approx(c_tight["speed_cluster"])
