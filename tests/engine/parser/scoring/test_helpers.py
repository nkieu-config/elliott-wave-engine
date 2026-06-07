from __future__ import annotations

import pytest

from engine.parser.scoring.helpers import _log_cv_score


class TestLogCvScore:
    def test_perfect_cluster_returns_one(self):
        assert _log_cv_score([2.0, 2.0, 2.0]) == pytest.approx(1.0)

    def test_decay_with_spread(self):
        tight = _log_cv_score([1.0, 1.1, 0.9])
        loose = _log_cv_score([1.0, 3.0, 0.33])
        assert tight is not None and loose is not None
        assert tight > loose

    def test_returns_none_when_fewer_than_two_positive(self):
        assert _log_cv_score([]) is None
        assert _log_cv_score([1.0]) is None
        assert _log_cv_score([0.0, -1.0]) is None
        assert _log_cv_score([1.0, 0.0]) is None

    def test_k_lowers_score_for_same_spread(self):
        v = [1.0, 2.0]
        s_large_k = _log_cv_score(v, K=1.0)
        s_small_k = _log_cv_score(v, K=0.3)
        assert s_large_k > s_small_k
