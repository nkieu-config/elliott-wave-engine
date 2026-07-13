from __future__ import annotations

from typing import Any, Literal

from analyst.schemas.bottleneck import BottleneckDiagnosis
from analyst.taxonomy import SLOT_PROSE, STRUCTURAL_SLOTS, VISUAL_SLOTS
from analyst.theory.citation_map import slot_theory_ref

_STRUCTURAL = frozenset(STRUCTURAL_SLOTS)
_VISUAL = frozenset(VISUAL_SLOTS)


def diagnose_bottleneck(
    score_components: dict[str, Any], family: str,
) -> BottleneckDiagnosis:
    # family resolves theory pages for fib_push_pairs.
    active = {
        k: v for k, v in score_components.items()
        if k in _STRUCTURAL | _VISUAL and isinstance(v, (int, float))
    }
    if not active:
        raise ValueError("No active slots in score_components")
    sorted_slots = sorted(active.items(), key=lambda kv: kv[1])
    bottleneck_name, bottleneck_value = sorted_slots[0]
    gap = (sorted_slots[1][1] - bottleneck_value) if len(sorted_slots) > 1 else 0.0

    dim: Literal["structural", "visual"] = (
        "structural" if bottleneck_name in _STRUCTURAL else "visual"
    )
    dim_total = score_components.get(f"{dim}_total", bottleneck_value)
    # quality = MIN(structural_total, visual_total). `total` = quality × commitment.
    overall_quality = score_components.get("quality", min(
        score_components.get("structural_total", float("inf")),
        score_components.get("visual_total", float("inf")),
    ))

    intermediates = (
        score_components.get("intermediates", {}).get(bottleneck_name, {})
    )
    ref = slot_theory_ref(bottleneck_name, family)
    if ref is None:
        raise ValueError(f"no theory reference for slot {bottleneck_name!r} (family {family!r})")
    explanation = _build_explanation(bottleneck_name, intermediates)

    return BottleneckDiagnosis(
        slot_name=bottleneck_name,
        slot_value=float(bottleneck_value),
        dimension=dim,
        is_dim_minimum=abs(bottleneck_value - dim_total) < 1e-9,
        is_overall_minimum=abs(bottleneck_value - overall_quality) < 1e-9,
        gap_to_next=float(gap),
        intermediates=intermediates,
        plain_explanation=explanation,
        theory_ref=ref,
    )


def _build_explanation(slot: str, inter: dict) -> str:
    plain = SLOT_PROSE.get(slot, slot)
    if slot == "speed_cluster":
        speeds = inter.get("leg_speeds", [])
        if speeds:
            lo, hi = min(speeds), max(speeds)
            spread = f"~{hi/lo:.2f}×" if lo > 0 else "extreme (slowest leg ≈ 0)"
            return (
                f"The {plain} check is the weakest. Leg pace ranges from "
                f"{lo:.2f} to {hi:.2f} (price per bar), a {spread} spread — "
                f"the check operationalizes the same-degree principle "
                f"(p.91) (p.96) and penalises wide pace spreads."
            )
    if slot == "fib_push_pairs":
        pairs = inter.get("pairs", [])
        if pairs:
            worst = max(pairs, key=lambda p: p["distance"])
            return (
                f"The {plain} check is the weakest. The worst push pair "
                f"{worst['pair']} sits a distance of {worst['distance']:.3f} "
                f"from the nearest Fibonacci level."
            )
    if slot == "pull_depth_discipline":
        pairs = inter.get("pairs", [])
        out_of_window = [p for p in pairs if not p.get("in_window")]
        if out_of_window:
            depths = ", ".join(f"{p['depth']:.3f}" for p in out_of_window)
            return (
                f"The {plain} check is the weakest. {len(out_of_window)} "
                f"pullback(s) fall outside the healthy 0.382-0.618 "
                f"retracement window (depths: {depths})."
            )
    if slot == "leg_smoothness":
        per_leg = inter.get("per_leg", [])
        if per_leg:
            worst = max(per_leg, key=lambda leg: leg.get("ratio", 0.0))
            direction = worst.get("direction")
            kind = (
                " (a down leg)" if direction == "down"
                else " (an up leg)" if direction == "up" else ""
            )
            return (
                f"The {plain} check is the weakest. Leg s{worst['leg_idx']+1}"
                f"{kind}'s deepest counter-swing — its largest move AGAINST the "
                f"leg's own direction — ran {worst['ratio']:.3f}× the leg's net "
                f"travel (its drawdown ratio), measured within this leg only; a "
                f"clean impulse stays under 1.0. This is a chart-appearance "
                f"heuristic with no theory binding."
            )
    if slot == "pivot_sharpness":
        per_pivot = inter.get("per_pivot", [])
        if per_pivot:
            worst = min(per_pivot, key=lambda p: p.get("sharpness_score", 1.0))
            return (
                f"The {plain} check is the weakest. Pivot "
                f"{worst['pivot_idx']} is the dullest turning point on the "
                f"chart; this is a chart-appearance heuristic with no theory "
                f"binding."
            )
    return f"The {plain} check is the weakest; no detailed measurements are available."
