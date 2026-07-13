# Worked Examples

What the system actually outputs on real charts — including the two cases where it outputs a low
confidence score, and nothing at all. A page of only flattering examples would be marketing; the
failures are here because the whole argument of this project is that you can _see_ why a count
scored the way it did, and that argument is only worth anything if it survives the bad cases.

> Numbers below are real pipeline output, not illustrations. They were produced from cached price
> data through **2026-07-06** at the default configuration (linear scale, ATR period 14,
> multiplier 3.0, floor 10%, min-bars 4). [Reproduce them](#reproducing-these) with one script.

## Contents

- [How to read a score](#how-to-read-a-score)
- [1. DDOG weekly — a nested count (the demo default)](#1-ddog-weekly--a-nested-count-the-demo-default)
- [2. AAPL daily — a complete pattern with a passing rule trail](#2-aapl-daily--a-complete-pattern-with-a-passing-rule-trail)
- [3. NVDA weekly — when the system says it isn't confident](#3-nvda-weekly--when-the-system-says-it-isnt-confident)
- [4. AAPL weekly / max — when the system produces nothing](#4-aapl-weekly--max--when-the-system-produces-nothing)
- [What these examples are not](#what-these-examples-are-not)
- [Reproducing these](#reproducing-these)

## How to read a score

Every scenario carries five slot scores. They do not average — they compose by **minimum**, so the
headline number is always the weakest link:

```
structural_total = min(speed_cluster, fib_push_pairs, pull_depth_discipline)
visual_total     = min(pivot_sharpness, leg_smoothness)
quality          = min(structural_total, visual_total)
total            = quality × commitment        # commitment = legs closed / legs needed
```

A slot that doesn't apply is omitted (a one-leg hypothesis has no push _pairs_ to compare, so
`fib_push_pairs` is absent). The arithmetic is shown in each example below, so you can check it.

## 1. DDOG weekly — a nested count (the demo default)

`?symbol=DDOG&timeframe=week&period=max` — 356 bars, 12 active pivots, anchor **27.55 (2019-10-21)**.
The engine returns **22 ranked scenarios**. The top one:

| Slot                      | Score      |                                             |
| ------------------------- | ---------- | ------------------------------------------- |
| `speed_cluster`           | 0.5371     |                                             |
| `fib_push_pairs`          | 0.6440     |                                             |
| `pull_depth_discipline`   | **0.5160** | ← structural weakest link                   |
| `structural_total`        | 0.5160     | = min of the three above                    |
| `pivot_sharpness`         | 0.9632     |                                             |
| `leg_smoothness`          | **0.4670** | ← visual weakest link, and the overall one  |
| `visual_total`            | 0.4670     |                                             |
| `quality`                 | 0.4670     | = min(0.5160, 0.4670)                       |
| `commitment`              | 0.8000     | 4 of 5 legs closed                          |
| **`total`**               | **0.3736** | = 0.4670 × 0.8000                           |

A `5W_SIDEWAY` in progress, four legs closed, currently inside leg 5. What makes it worth reading
is the recursion: legs 2, 3 and 4 are not straight lines — each is itself a completed `3W_NORMAL`
sub-pattern with three children of its own. That is the wave grammar doing what it claims to do,
and it is what the click-to-drill interaction in the UI is navigating.

Note also what the score refuses to do. `pivot_sharpness` is nearly perfect at 0.9632, and it buys
the count nothing: `leg_smoothness` at 0.4670 sets the ceiling, and the headline lands there. A
weighted sum would have averaged that 0.96 into the result and reported a more confident number
than the chart deserves.

## 2. AAPL daily — a complete pattern with a passing rule trail

`?symbol=AAPL&timeframe=day&period=2y` — 502 bars, 13 active pivots, anchor **168.32 (2025-04-08)**.
**52 scenarios**; the top one is a **complete** `3W_NORMAL` (`commitment = 1.0` — nothing left to
close), and because it's complete, it carries the full verifier trail:

| Rule                | Passed | Measured | Threshold      |
| ------------------- | ------ | -------- | -------------- |
| `3w.r1.count_3_alt` | ✅     | —        | 3 legs, alternating |
| `3w.r2.s2_in_range` | ✅     | 0.3767   | `[0.01, 2.618]` |
| `3w.r3.s3_min_size` | ✅     | 1.6072   | `>= 0.236`      |

This is the auditability claim in its concrete form. The count is not asserted — it is *derived*,
and each rule reports the number it measured against the bound it had to clear. Wave 2 retraced
37.67% of wave 1 (inside the permitted range); wave 3 came in at 1.61× (comfortably past the 0.236
floor). Anyone who disagrees with the count can point at the specific rule and the specific number.

Its score breakdown:

```
speed_cluster 0.4813 · fib_push_pairs 0.6635 · pull_depth_discipline 0.9653  → structural 0.4813
pivot_sharpness 1.0000 · leg_smoothness 0.6550                               → visual     0.6550
quality = min(0.4813, 0.6550) = 0.4813 · commitment 1.0                      → total      0.4813
```

Every rule passes and the retracement discipline is near-textbook (0.9653) — and the count still
only scores 0.48, because the legs' pace is uneven (`speed_cluster` 0.4813). A rule-legal count is
not automatically a good-looking one, and the score says so.

## 3. NVDA weekly — when the system says it isn't confident

`?symbol=NVDA&timeframe=week&period=5y` — 262 bars, but only **8 active pivots**. The top scenario
scores **0.0009**.

```
speed_cluster 0.1807 · pull_depth_discipline 0.0026   → structural 0.0026   ← bottleneck
pivot_sharpness 0.9881 · leg_smoothness 0.5540        → visual     0.5540
quality = min(0.0026, 0.5540) = 0.0026 · commitment 0.3333 (1 of 3 legs) → total 0.0009
```

Look at the pivots and the number stops being surprising:

```
2022-10-10  low      10.80   ← anchor
2025-10-27  high    212.17
2026-03-30  low     164.27
2026-05-11  high    236.54
```

One enormous push — 10.80 to 212.17 across three years, with no intermediate pivot surviving the
ATR threshold — and then a retracement of only ~24% of it, against a slot that plateaus on the
theory's 38.2–61.8% band. There is barely any wave structure here to grade: one closed leg, a
shallow pull, and no push pairs to compare (`fib_push_pairs` is absent entirely).

**The right output for this chart is a near-zero confidence score, and that is what comes back.**
The system still ranks 14 hypotheses and still lets you drill into them — it simply refuses to
claim any of them is good, and names `pull_depth_discipline` as the reason. A tool that returned a
confident-looking count here would be lying to you.

## 4. AAPL weekly / max — when the system produces nothing

`?symbol=AAPL&timeframe=week&period=max` — 2,379 bars back to 1980, 94 active pivots.
**Zero scenarios.** No count survives the beam.

This is a genuine limitation, not a caught exception. But the engine does not fail silently — it
returns a `DiagnosticReport` naming the cause:

| Field                  | Value                                                                 |
| ---------------------- | --------------------------------------------------------------------- |
| `death_reason`         | `root_pattern_completed_but_segments_remain`                          |
| `first_divergence_index` | 6                                                                   |
| `last_alive_segment_index` | 51                                                                |

Read plainly: the anchor the system picked (the all-time low, 1982) completes its root pattern by
segment 6, but 88 segments of price history remain after it. The anchor is the start of a structure
far too small for the window — 45 years of data cannot be one wave count anchored at the beginning.
The engine detects this specific shape of failure and says so, and the UI surfaces that hint
instead of an empty chart.

`MSFT` at `week` / `max` fails the same way for a different reason
(`rules_too_strict_or_pivot_noise` — hypotheses die mid-parse around segment 16).

The practical read: **this engine analyzes a structure, not an entire price history.** Narrow the
window and it works — the same symbol at `week` / `5y` returns 51 scenarios with a healthy top
score of 0.42, and at `day` / `2y` returns the fully-verified count in
[example 2](#2-aapl-daily--a-complete-pattern-with-a-passing-rule-trail). Choosing the analysis
window is a judgment the user still has to make, and the system does not make it for them.

## What these examples are not

They are not a benchmark. There is no labeled dataset of "correct" Elliott Wave counts to score
against — expert analysts disagree on the same chart, which is the premise the whole project starts
from. So these examples demonstrate that the output is **inspectable and honest about its own
confidence**; they do not demonstrate that it is *right*, and no claim on this page should be read
as making that stronger claim. See
[tradeoffs.md](tradeoffs.md#count-quality-is-auditable-not-benchmarked).

## Reproducing these

Every figure above comes from `run_pipeline` at default settings. To regenerate:

```python
from pathlib import Path

from engine import ScoringConfig, run_pipeline
from engine.data.cache import CacheKey
from infra.market_data import ParquetCache

bars = ParquetCache(Path("data")).load(
    CacheKey(symbol="AAPL", cache_label="daily", period="2y"), max_age=None
)
result = run_pipeline(
    bars=bars,
    scale_mode="linear",
    atr_period=14,
    atr_multiplier=3.0,
    atr_floor=0.10,
    min_bars_between=4,
    scoring_config=ScoringConfig(),
)

top = max(
    result.report.scenarios,
    key=lambda s: s.score_components.get("total", s.score),
)
print(top.family, top.pattern_kind, top.score_components)
for rule in top.rules_log:
    print(rule.id, rule.passed, rule.measured, rule.detail)
```

Or open any of the URLs above against a [running instance](development.md) — the chart
configuration lives entirely in the query string, so each link reconstructs the exact view.

> Live prices move. Re-running after 2026-07-06 will fetch newer bars and the numbers will shift;
> the *behaviors* — nesting, the weakest link capping the score, the near-zero on NVDA, the empty
> result on 45 years of AAPL — are properties of the design, not of a particular week.
