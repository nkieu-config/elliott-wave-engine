# Single source of truth for slot vocabulary — at package top level because
# diagnostics, serialization, orchestrator and the API all depend on it.

from __future__ import annotations

from engine.display import FAMILY_DISPLAY

# Lowercase slot prose for inline narration. Explicit (not `.lower()`) so
# "Fibonacci" stays a proper noun mid-sentence.
SLOT_PROSE: dict[str, str] = {
    "speed_cluster": "wave pacing",
    "fib_push_pairs": "Fibonacci proportion",
    "pull_depth_discipline": "pullback depth",
    "pivot_sharpness": "pivot sharpness",
    "leg_smoothness": "swing smoothness",
}

GLOSSARY: dict[str, str] = {
    "Wave pacing": "Whether the waves move at a similar speed (price per bar).",
    "Fibonacci proportion": "Whether wave sizes land near classic Fibonacci ratios.",
    "Pullback depth": "Whether each pullback retraces a healthy amount — not too shallow, not too deep.",
    "Pivot sharpness": "How clean and sharp each turning point looks on the chart.",
    "Swing smoothness": "How smooth each price swing is, versus choppy back-and-forth.",
    "Match quality": "How well the wave's shape and proportions fit — before the completeness discount.",
    "Completeness": "How far the pattern has progressed; a partial pattern is discounted.",
    "Ranking score": "The final score used to rank scenarios: match quality × completeness.",
}

STRUCTURAL_SLOTS: tuple[str, ...] = (
    "speed_cluster", "fib_push_pairs", "pull_depth_discipline",
)
VISUAL_SLOTS: tuple[str, ...] = ("pivot_sharpness", "leg_smoothness")

# Canonical 5-slot ordering: structural first, then visual.
ALL_SLOTS: tuple[str, ...] = STRUCTURAL_SLOTS + VISUAL_SLOTS


def slot_dimension(slot: str) -> str:
    return "structural" if slot in STRUCTURAL_SLOTS else "visual"


def humanize_family_codes(text: str) -> str:
    # Longest-first so LINK_SE isn't partly rewritten by LINK_S.
    for code in sorted(FAMILY_DISPLAY, key=len, reverse=True):
        text = text.replace(code, FAMILY_DISPLAY[code])
    return text
