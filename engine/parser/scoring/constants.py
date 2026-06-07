from __future__ import annotations

import math

# Fib tables only; tunable scalars live on parser.scoring_config.ScoringConfig.

FIB_LEVELS: tuple[float, ...] = (
    0.236,
    0.382,
    0.5,
    0.618,
    0.786,
    1.0,
    1.272,
    1.618,
    2.618,
)

LOG_FIB_LEVELS: tuple[float, ...] = tuple(math.log(f) for f in FIB_LEVELS)
