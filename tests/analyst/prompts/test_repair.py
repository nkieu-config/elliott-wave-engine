import pytest

from analyst.prompts.repair import build_repair_prompt
from analyst.schemas.citation import CitationReport


def test_repair_prompt_lists_disallowed_and_allowed_pages():
    report = CitationReport(
        cited_pages={42, 999}, allowed_pages={42, 91}, unsourced_claims=(),
    )
    out = build_repair_prompt("BASE PROMPT", "prior answer (p.999)", report)
    assert "BASE PROMPT" in out
    assert "prior answer (p.999)" in out
    assert "(p.999)" in out
    assert "(p.42)" in out and "(p.91)" in out


def test_repair_prompt_lists_unsourced_claims_with_escape_hatch():
    report = CitationReport(
        cited_pages=set(), allowed_pages={91},
        unsourced_claims=("The rule requires five legs.",),
    )
    out = build_repair_prompt("BASE", "prior", report)
    assert "The rule requires five legs." in out
    assert "disclosure" in out


def test_repair_too_short_message_is_mode_specific():
    report = CitationReport(cited_pages=set(), allowed_pages=set(), too_short=True)
    analysis = build_repair_prompt("BASE", "x", report)
    qa = build_repair_prompt("BASE", "x", report, mode="qa")
    assert "2-3 short paragraphs" in analysis      # narration wants paragraphs
    assert "2-3 short paragraphs" not in qa         # QA allows a single sentence
    assert "single" in qa.lower()


def test_repair_prompt_includes_revision_instruction():
    report = CitationReport(cited_pages={999}, allowed_pages=set())
    out = build_repair_prompt("BASE", "prior", report)
    assert "[REVISION REQUEST]" in out
    assert "json object only" in out.lower()


# field name → (claim text, marker substring expected in the prompt)
@pytest.mark.parametrize(
    ("field", "claim", "marker"),
    [
        ("arithmetic_chain_claims",
         "The score 0.374 is 0.467 times 0.800.", "arithmetic chain"),
        ("prose_page_claims",
         "Leg-by-leg retracement, see pages 103 and 111.",
         "page reference inside the prose"),
        ("raw_identifier_claims",
         "The pull_depth_discipline check fired.", "raw code identifier"),
        ("ungrounded_citation_claims",
         "Theory X says Y (p.91).", "does NOT actually state"),
        ("meta_system_claims",
         "The verifier has not evaluated this.", "internal system component"),
        ("procedural_recitation_claims",
         "The check evaluates how X by Y.", "GENERAL procedure"),
        ("fabricated_number_claims", "The score is 0.873.", "NOT present in"),
        ("fragment_claims", "And the pullback held.", "SENTENCE FRAGMENTS"),
    ],
    ids=[
        "arithmetic_chain", "prose_page", "raw_identifier", "ungrounded_citation",
        "meta_system", "procedural_recitation", "fabricated_number", "fragment",
    ],
)
def test_repair_prompt_lists_claim_field(field, claim, marker):
    report = CitationReport(**{field: (claim,)})
    out = build_repair_prompt("BASE", "prior", report)
    assert claim in out
    assert marker in out


def test_repair_prompt_handles_too_short_report():
    report = CitationReport(too_short=True)
    out = build_repair_prompt("BASE", "", report)
    assert "empty or far too short" in out
    assert "no specific issue recorded" not in out


def test_repair_prompt_flags_malformed_json():
    report = CitationReport(malformed_json=True)
    out = build_repair_prompt("BASE", "not json", report)
    assert "not valid JSON" in out
