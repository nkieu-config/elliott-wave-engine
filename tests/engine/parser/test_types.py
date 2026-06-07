import math
from datetime import datetime

import pytest

from engine.parser.types import _Leg
from engine.types import Pivot


def _leg(price_a: float, price_b: float) -> _Leg:
    t = datetime(2024, 1, 1)
    return _Leg(
        role="s1",
        span_start=Pivot(0, t, price_a, "low"),
        span_end=Pivot(1, t, price_b, "high"),
    )


def test_leg_length_linear():
    assert _leg(100.0, 120.0).length("linear") == 20.0


def test_leg_length_log_normal():
    assert _leg(100.0, 200.0).length("log") == pytest.approx(math.log(2))


def test_leg_length_log_guards_non_positive_price():
    # math.log(0) / log(<0) would raise ValueError and crash the beam search.
    assert _leg(0.0, 120.0).length("log") == 0.0
    assert _leg(100.0, 0.0).length("log") == 0.0
    assert _leg(-5.0, 120.0).length("log") == 0.0
