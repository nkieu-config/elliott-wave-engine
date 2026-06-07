from __future__ import annotations

from analyst.schemas.analysis import AnalysisResult
from analyst.serialization.analysis_blocks import (
    format_alternative_brief,
    format_bottleneck,
    format_confirmation,
    format_decision_summary,
    format_scenario_diff,
    format_succession,
    format_targets,
    format_weakness_detail,
)
from analyst.serialization.slots import format_slot_grid
from analyst.serialization.tree import format_tree
from analyst.taxonomy import humanize_family_codes
from engine import Scenario
from engine.display import pattern_label

# Sections absent here are absent from mode's data block — model can't bleed unseen numbers.
_MODE_SECTIONS: dict[str, frozenset[str]] = {
    "explanation": frozenset(
        {"identity", "structure", "verifier", "slots", "bottleneck", "decision"}
    ),
    "slot_focus": frozenset(
        {"identity", "structure", "slots", "bottleneck", "weakness_detail",
         "targets", "decision"}
    ),
    "differentiator": frozenset(
        {"identity", "structure", "slots", "bottleneck", "diff",
         "decision", "alternative"}
    ),
    "scenario_outlook": frozenset(
        {"identity", "structure", "confirmation", "targets", "succession",
         "decision"}
    ),
}

# Fallback for unknown/None mode — render everything.
_ALL_SECTIONS: frozenset[str] = frozenset(
    {
        "identity", "structure", "verifier", "slots", "bottleneck",
        "weakness_detail", "diff", "confirmation", "targets",
        "succession", "decision", "alternative",
    }
)


def format_verifier(sc: Scenario) -> str:
    # Verifier classifies only on completion; explicit no-pass/fail line prevents conflation.
    if sc.is_complete:
        passed = [r for r in sc.rules_log if r.passed]
        failed = [r for r in sc.rules_log if not r.passed]
        lines = [
            "## Verifier\n",
            f"- **Verdict:** PASSED — the verifier classified this pattern "
            f"as {pattern_label(sc.pattern_kind, friendly=True)}.",
        ]
        if sc.rules_log:
            summary = f"{len(passed)} rule(s) satisfied"
            if failed:
                summary += (
                    f"; {len(failed)} not satisfied: "
                    + ", ".join(r.id for r in failed)
                )
            lines.append(f"- **Rules:** {summary}.")
        return "\n".join(lines) + "\n"

    n_legs = len(sc.legs)
    return (
        "## Verifier\n\n"
        f"- **Verdict:** NOT RUN — the pattern is still open "
        f"({n_legs} leg(s) parsed); the verifier classifies a pattern only "
        f"once it is complete.\n"
        "- The verifier rules have NOT been evaluated for this scenario. Do "
        "not describe them as passed, failed, or 'not passed cleanly' — "
        "pattern incompleteness is a separate fact from a verifier verdict.\n"
    )


def serialize_scenario(
    sc: Scenario, layer1: AnalysisResult, mode: str | None = None,
) -> str:
    wanted = _MODE_SECTIONS.get(mode, _ALL_SECTIONS) if mode else _ALL_SECTIONS
    sections: list[str] = []

    if "identity" in wanted:
        pk = pattern_label(sc.pattern_kind, friendly=True) or "?"
        status = "CLOSED" if sc.is_complete else "OPEN"
        sections.append(
            f"# Scenario Analysis\n\n"
            f"- **Family:** {humanize_family_codes(sc.family)}\n"
            f"- **Pattern:** {pk}\n"
            f"- **Status:** {status}\n"
            f"- **Score:** {sc.score:.3f}\n"
        )

    if "structure" in wanted:
        sections.append(
            "## Structure\n\n```\n" + format_tree(sc.root, sc.family) + "\n```\n"
        )

    if "verifier" in wanted:
        sections.append(format_verifier(sc))

    if "slots" in wanted:
        bottleneck_name = layer1.bottleneck.slot_name if layer1.bottleneck else None
        sections.append(
            "## Score Components\n\n"
            + format_slot_grid(sc.score_components or {}, bottleneck=bottleneck_name)
        )

    if "bottleneck" in wanted and layer1.bottleneck:
        sections.append(format_bottleneck(layer1.bottleneck))
    if "weakness_detail" in wanted and layer1.bottleneck:
        # Pass score_intermediates — sc.score_components lacks per-slot data.
        detail = format_weakness_detail(
            layer1.bottleneck, sc.score_components,
            intermediates_map=layer1.score_intermediates,
        )
        if detail:
            sections.append(detail)
    if "decision" in wanted and layer1.decision:
        sections.append(format_decision_summary(layer1.decision))
    if "alternative" in wanted and layer1.alternative:
        sections.append(format_alternative_brief(layer1.alternative))
    if "diff" in wanted:
        # Always rendered — block states "no competitor" explicitly.
        sections.append(format_scenario_diff(layer1.scenario_diffs))
    if "confirmation" in wanted and layer1.confirmation:
        sections.append(format_confirmation(layer1.confirmation))
    if "targets" in wanted and layer1.targets:
        sections.append(format_targets(layer1.targets))
    if "succession" in wanted and layer1.succession:
        # current_price → link bands get %-from-current (else LLM loses dollar handle).
        current_px = (
            layer1.decision.current.price
            if layer1.decision is not None else None
        )
        sections.append(format_succession(layer1.succession, current_px))

    return "\n\n".join(sections)
