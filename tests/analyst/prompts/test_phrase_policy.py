"""Lock prompt↔serializer terminology. Scans serialized markdown, not the prompt
body (which keeps intentional ✗ counter-examples), plus a light prompt term check."""

from __future__ import annotations

from analyst.diagnostics.scenario_diff import diff_top_scenarios
from analyst.prompts.differentiator import USER_PROMPT as DIFFERENTIATOR_PROMPT
from analyst.prompts.scenario_outlook import USER_PROMPT as OUTLOOK_PROMPT
from analyst.serialization.analysis_blocks import format_scenario_diff
from tests.analyst.fixtures.scenarios import sideway_vs_three_pair

# Required / forbidden substrings per serialized block — extend as new
# terminology contradictions surface.
SERIALIZED_BLOCK_POLICY = {
    "scenario_diff": {
        "required": ["score points"],
        "forbidden": ["percentage points"],
    },
}


def _scenario_diff_md() -> str:
    primary, competitor = sideway_vs_three_pair()
    return format_scenario_diff(tuple(diff_top_scenarios([primary, competitor])))


def test_scenario_diff_gap_block_uses_score_points_not_percentage_points():
    md = _scenario_diff_md()
    policy = SERIALIZED_BLOCK_POLICY["scenario_diff"]
    for required in policy["required"]:
        assert required in md, f"expected {required!r} in scenario-diff block"
    for forbidden in policy["forbidden"]:
        assert forbidden not in md, f"{forbidden!r} must not appear"


def test_scenario_diff_gap_rendered_as_bare_points_no_percent_sign():
    # Gap reads "+12", never "+12%" — a % invites a probability reading.
    md = _scenario_diff_md()
    gap_block = md[md.index("| Check | Gap (score points) |"):]
    assert "%" not in gap_block


def test_differentiator_prompt_prescribes_score_points_term():
    # Prompt side of the same invariant — keeps it from drifting back to conflict.
    assert "score points" in DIFFERENTIATOR_PROMPT


def test_outlook_why_fibonacci_guards_against_circular_answer():
    # The "why these ratios" beat must demand the golden-ratio mechanism and
    # flag the recurring circular "because it lacks a trend" answer.
    assert "golden ratio" in OUTLOOK_PROMPT
    assert "lacks a clear trend" in OUTLOOK_PROMPT


def test_outlook_requires_a_citation_on_the_fibonacci_why():
    # The Fibonacci "why" must be a cited theory_claim, not a page-less
    # data_observation (the citation kept dropping otherwise).
    assert "theory_claim" in OUTLOOK_PROMPT
    assert "MUST carry a (p.N) citation" in OUTLOOK_PROMPT


def test_outlook_guards_against_forced_linkage_phrasing():
    # The linkage is a TYPE constraint, not a forced event — guard the
    # "a Sideway linkage is required to follow" over-compression.
    assert "is required to follow this pattern" in OUTLOOK_PROMPT  # the ✗ example
    assert "if a linkage follows" in OUTLOOK_PROMPT                # the ✓ framing


def test_differentiator_defers_lead_call_to_lead_strength_line():
    # The clear-vs-close call must come from the computed Lead strength line,
    # not the model's own judgement (which overstated a sub-50% lead).
    assert "Lead strength" in DIFFERENTIATOR_PROMPT
    assert "clear leader" in DIFFERENTIATOR_PROMPT  # the thing it must not say
