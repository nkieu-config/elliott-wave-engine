from __future__ import annotations

FIB_236: float = 0.236
FIB_382: float = 0.382
FIB_500: float = 0.500
FIB_618: float = 0.618
FIB_786: float = 0.786
FIB_1618: float = 1.618
FIB_2618: float = 2.618


# 3W pp.46-50
R2_S2_MIN_RATIO_3W: float = 0.01
R2_S2_MAX_RATIO_3W: float = FIB_2618
R3_S3_MIN_RATIO_3W: float = FIB_236


# 5W_TREND pp.30-32
R7_S5_MIN_RATIO_5WT: float = FIB_382


# 5W_SIDEWAY pp.36-43
R2_S2_MIN_RATIO_5WS: float = FIB_500
R2_S2_MAX_RATIO_5WS: float = FIB_2618
R3_S4_MIN_RATIO_5WS: float = FIB_500
R3_S4_MAX_RATIO_5WS: float = FIB_2618

R4_S3_MIN_CONTRACT_5WS: float = FIB_500
R4_S3_MAX_CONTRACT_5WS: float = 0.99
R5_S5_MIN_CONTRACT_5WS: float = FIB_236
R5_S5_MAX_CONTRACT_5WS: float = 0.99

# Contract/Balance (<1) vs Expand (>1) on s3 and s5.
SIDEWAY_EXPAND_BOUNDARY: float = 1.0


# LINK_T pp.62, 94
R8_LINK_MIN_RATIO_LINK_T: float = 0.01
R8_LINK_MAX_RATIO_LINK_T: float = FIB_618

# Strict: ratio == 2.0 does NOT satisfy "ใหญ่เกิน 200%".
R9_LINK_TIME_MULTIPLIER_LINK_T: float = 2.0


# LINK_S / +SE pp.71-78, 95
R3_LINK_MIN_3W_LINK_S: float = FIB_786
R3_LINK_MIN_EXPAND_LINK_S: float = FIB_786
R3_LINK_MIN_5WS_LINK_S: float = 1.01

R5_LINK_SE_THRESHOLD_LINK_S: float = FIB_1618


# Degree pp.88-97
DEGREE_GANN_FLOOR_RATIO: float = 1.0 / 3.0

# MUST equal 1/FLOOR for reciprocal band.
DEGREE_GANN_CEILING_RATIO: float = 3.0

# Integer-safe inverse for ``link × DIVISOR ≥ floor``; MUST equal round(1/FLOOR).
DEGREE_GANN_FLOOR_DIVISOR: int = 3


# 1 = disabled. Drops spike-and-revert noise surviving ZigZag %.
MIN_BARS_BETWEEN_DEFAULT: int = 1

# ATR ZigZag: threshold = max(MULT × ATR(period)/close, FLOOR). 14 bars ≈ 3.5mo weekly.
ZIGZAG_ATR_PERIOD_DEFAULT: int = 14
ZIGZAG_ATR_MULTIPLIER_DEFAULT: float = 3.0
ZIGZAG_ATR_FLOOR_DEFAULT: float = 0.10


# Equal-push tolerance p.27 (unspecified — 5% pragmatic).
EQUAL_WITHIN_DEFAULT_TOLERANCE: float = 0.05
