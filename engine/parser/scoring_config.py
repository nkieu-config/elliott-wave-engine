from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# Top-level (not scoring/) — avoids runtime→scoring/components→runtime cycle.

CommitmentCurve = Literal["linear", "sqrt", "off"]


@dataclass(frozen=True)
class ScoringConfig:
    # log(3)/2 — ceiling for log-space stddev under Gann ratio ≤3.
    k_sigma: float = 0.5
    # ~5% multiplicative log-space Fib tolerance.
    log_tol_fib: float = 0.05
    # Pull in [lo, hi] ⇒ 1.0; outside decays with tol.
    pull_depth_lo: float = 0.382
    pull_depth_hi: float = 0.618
    pull_depth_tol: float = 0.15
    # ±window bars around each pivot for sharpness/smoothness scans.
    pivot_window: int = 2

    commitment_curve: CommitmentCurve = "linear"
