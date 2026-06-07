from analyst.client.gate import _MIN_NARRATION_CHARS, gate_narration_draft
from analyst.schemas.narration import Claim, NarrationDraft


def _draft(*claims: Claim) -> NarrationDraft:
    return NarrationDraft(paragraphs=[list(claims)])


def _long(text: str) -> str:
    return (text + " ") * 8


def test_gate_passes_when_every_theory_claim_cites_allowed_pages():
    draft = _draft(
        Claim(text=_long("The score sits at 0.5."), type="data_observation"),
        Claim(text=_long("Wave 3 must exceed wave 2."), type="theory_claim",
              pages=[33, 34]),
    )
    rendered, report, fell_back = gate_narration_draft(
        draft, allowed_pages={33, 34}, layer1_fallback="FALLBACK",
    )
    assert fell_back is False
    assert report.ok
    assert rendered != "FALLBACK"
    assert "(p.33-34)" in rendered


def test_gate_fails_when_theory_claim_cites_disallowed_page():
    draft = _draft(
        Claim(text=_long("Rule R1 holds."), type="theory_claim", pages=[999]),
    )
    rendered, report, fell_back = gate_narration_draft(
        draft, allowed_pages={33, 34}, layer1_fallback="FALLBACK",
    )
    assert fell_back is True
    assert rendered == "FALLBACK"
    assert 999 in report.disallowed_pages
    assert not report.ok


def test_gate_fails_on_theory_claim_with_no_pages():
    draft = _draft(
        Claim(text="Theory requires five legs.", type="theory_claim",
              pages=[]),
    )
    _, report, fell_back = gate_narration_draft(
        draft, allowed_pages={33}, layer1_fallback="FALLBACK",
    )
    assert fell_back is True
    assert report.unsourced_claims == ("Theory requires five legs.",)


def test_gate_does_not_flag_data_observations_or_disclosures():
    draft = _draft(
        Claim(text=_long("The retracement reached 100% at bar 220."),
              type="data_observation"),
        Claim(text=_long("No Fibonacci Flow targets are defined to cite."),
              type="disclosure"),
    )
    _, report, fell_back = gate_narration_draft(
        draft, allowed_pages=set(), layer1_fallback="FALLBACK",
    )
    assert fell_back is False
    assert report.unsourced_claims == ()
    assert report.ok


def test_gate_flags_raw_code_identifier_in_claim_text():
    draft = _draft(
        Claim(text=_long("The pull_depth_discipline slot is weak."),
              type="data_observation"),
    )
    _, report, fell_back = gate_narration_draft(
        draft, allowed_pages=set(), layer1_fallback="FALLBACK",
    )
    assert fell_back is True
    assert report.raw_identifier_claims == (
        "The pull_depth_discipline slot is weak. " * 8,
    )
    assert not report.ok


def test_gate_passes_plain_language_without_raw_identifiers():
    draft = _draft(
        Claim(text=_long("The pullback-depth check is the weak point."),
              type="data_observation"),
    )
    _, report, fell_back = gate_narration_draft(
        draft, allowed_pages=set(), layer1_fallback="FALLBACK",
    )
    assert fell_back is False
    assert report.raw_identifier_claims == ()
    assert report.ok


def test_gate_flags_uppercase_pattern_code():
    draft = _draft(
        Claim(text=_long("The 5W_SIDEWAY pattern is still open."),
              type="data_observation"),
    )
    _, report, fell_back = gate_narration_draft(
        draft, allowed_pages=set(), layer1_fallback="FALLBACK",
    )
    assert fell_back is True
    assert report.raw_identifier_claims == (
        "The 5W_SIDEWAY pattern is still open. " * 8,
    )
    assert not report.ok


def test_gate_allows_plain_uppercase_words():
    draft = _draft(
        Claim(text=_long("The pattern points DOWN within a 5-wave move."),
              type="data_observation"),
    )
    _, report, fell_back = gate_narration_draft(
        draft, allowed_pages=set(), layer1_fallback="FALLBACK",
    )
    assert report.raw_identifier_claims == ()
    assert fell_back is False


def test_gate_fails_on_none_draft():
    rendered, report, fell_back = gate_narration_draft(
        None, allowed_pages={33}, layer1_fallback="FALLBACK",
    )
    assert fell_back is True
    assert rendered == "FALLBACK"
    assert report.malformed_json is True
    assert report.too_short is False
    assert not report.ok


def test_gate_fails_when_rendered_text_below_length_floor():
    draft = _draft(Claim(text="Tiny.", type="data_observation"))
    _, report, fell_back = gate_narration_draft(
        draft, allowed_pages=set(), layer1_fallback="FALLBACK",
    )
    assert fell_back is True
    assert report.too_short is True


def test_gate_length_floor_counts_rendered_text():
    body = "x" * (_MIN_NARRATION_CHARS + 10)
    draft = _draft(Claim(text=body, type="data_observation"))
    _, report, fell_back = gate_narration_draft(
        draft, allowed_pages=set(), layer1_fallback="FALLBACK",
    )
    assert fell_back is False
    assert report.too_short is False


def test_gate_collects_all_cited_pages_across_paragraphs():
    draft = NarrationDraft(paragraphs=[
        [Claim(text=_long("Wave rule A."), type="theory_claim", pages=[33])],
        [Claim(text=_long("Wave rule B."), type="theory_claim", pages=[34])],
    ])
    _, report, fell_back = gate_narration_draft(
        draft, allowed_pages={33, 34}, layer1_fallback="FALLBACK",
    )
    assert fell_back is False
    assert report.cited_pages == frozenset({33, 34})


def test_gate_flags_arithmetic_chain_as_a_soft_signal():
    draft = _draft(
        Claim(text=_long("The score 0.374 is quality 0.467 times 0.800."),
              type="data_observation"),
    )
    rendered, report, fell_back = gate_narration_draft(
        draft, allowed_pages=set(), layer1_fallback="FALLBACK",
    )
    assert report.arithmetic_chain_claims
    assert report.ok
    assert fell_back is False
    assert rendered != "FALLBACK"


def test_gate_flags_arithmetic_with_multiplication_symbol():
    draft = _draft(
        Claim(text=_long("Overall 0.374 = 0.467 × 0.800 in this count."),
              type="data_observation"),
    )
    _, report, _ = gate_narration_draft(
        draft, allowed_pages=set(), layer1_fallback="FALLBACK",
    )
    assert report.arithmetic_chain_claims


def test_gate_flags_prose_page_reference_as_a_soft_signal():
    draft = _draft(
        Claim(text=_long("Leg-by-leg retracement applies, as set out on "
                         "pages 103 and 111 of the theory."),
              type="theory_claim", pages=[103, 111]),
    )
    rendered, report, fell_back = gate_narration_draft(
        draft, allowed_pages={103, 111}, layer1_fallback="FALLBACK",
    )
    assert report.prose_page_claims
    assert report.ok
    assert fell_back is False
    assert rendered != "FALLBACK"


def test_gate_prose_page_catches_abbreviated_form_but_not_plain_prose():
    d1 = _draft(Claim(text=_long("This reflects the same-degree rule p.91 here."),
                      type="data_observation"))
    _, r1, _ = gate_narration_draft(d1, allowed_pages=set(), layer1_fallback="F")
    assert r1.prose_page_claims
    d2 = _draft(Claim(text=_long("Pivot 3 is the dullest turn and leg s4 is choppy."),
                      type="data_observation"))
    _, r2, _ = gate_narration_draft(d2, allowed_pages=set(), layer1_fallback="F")
    assert r2.prose_page_claims == ()


def test_gate_arithmetic_needs_both_an_operator_and_two_numbers():
    d1 = _draft(Claim(text=_long("The ratio is max drawdown divided by leg span."),
                      type="data_observation"))
    _, r1, _ = gate_narration_draft(d1, allowed_pages=set(), layer1_fallback="F")
    assert r1.arithmetic_chain_claims == ()
    d2 = _draft(Claim(text=_long("Leg one runs from 27.55 to 199.68 on the chart."),
                      type="data_observation"))
    _, r2, _ = gate_narration_draft(d2, allowed_pages=set(), layer1_fallback="F")
    assert r2.arithmetic_chain_claims == ()


def test_gate_flags_upper_case_leg_codes():
    d = _draft(Claim(text=_long("Comparisons between S2 and S4 set the pace."),
                     type="data_observation"))
    _, r, _ = gate_narration_draft(d, allowed_pages=set(), layer1_fallback="F")
    assert r.raw_identifier_claims
    d2 = _draft(Claim(text=_long("Leg s4 sets the pace in this read."),
                      type="data_observation"))
    _, r2, _ = gate_narration_draft(d2, allowed_pages=set(), layer1_fallback="F")
    assert r2.raw_identifier_claims == ()


def test_gate_flags_link_wave_codes():
    for code in ("+T", "+S", "+SE"):
        d = _draft(Claim(text=_long(f"The structure may link via {code} next."),
                         type="data_observation"))
        _, r, _ = gate_narration_draft(d, allowed_pages=set(), layer1_fallback="F")
        assert r.raw_identifier_claims, f"{code} should have been flagged"


def test_gate_flags_meta_system_components_as_soft_signal():
    d = _draft(Claim(text=_long("The verifier has not yet evaluated this scenario."),
                     type="data_observation"))
    _, r, fell_back = gate_narration_draft(
        d, allowed_pages=set(), layer1_fallback="F",
    )
    assert r.meta_system_claims
    assert r.ok
    assert fell_back is False
    for phrase in ("Layer-1 shows", "the gate rejected", "the citation gate"):
        d2 = _draft(Claim(text=_long(f"As {phrase} this scenario, the pattern is open."),
                          type="data_observation"))
        _, r2, _ = gate_narration_draft(d2, allowed_pages=set(), layer1_fallback="F")
        assert r2.meta_system_claims, f"`{phrase}` should have been flagged"


def test_gate_flags_procedural_recitation_as_soft_signal():
    d = _draft(Claim(
        text=_long(
            "The pullback-depth check evaluates how deeply corrective "
            "waves retrace prior impulse waves."
        ),
        type="data_observation",
    ))
    _, r, fell_back = gate_narration_draft(
        d, allowed_pages=set(), layer1_fallback="F",
    )
    assert r.procedural_recitation_claims
    assert r.ok
    assert fell_back is False


def test_gate_procedural_recitation_does_not_trip_plain_interpretation():
    d = _draft(Claim(
        text=_long("The pullback-depth check ranks second-weakest here."),
        type="data_observation",
    ))
    _, r, _ = gate_narration_draft(d, allowed_pages=set(), layer1_fallback="F")
    assert r.procedural_recitation_claims == ()


def test_gate_catches_sentence_fragments():
    # regression: v2.10
    fragment_phrases = [
        "And has moved beyond the upper end of the projection band.",
        "With four waves completed and the fifth in progress.",
        "Meaning price has overshot the theoretical target.",
        "Which suggests the count is nearing completion.",
    ]
    for phrase in fragment_phrases:
        d = _draft(Claim(text=_long(phrase), type="data_observation"))
        _, r, fell_back = gate_narration_draft(
            d, allowed_pages=set(), layer1_fallback="F",
        )
        assert r.fragment_claims, f"fragment should be flagged: {phrase!r}"
        assert r.ok
        assert fell_back is False


def test_gate_catches_adverbial_np_fragments():
    # regression: v2.14
    fragments = [
        "Approximately 1.6 years on this weekly chart, though a rule of thumb.",
        "Roughly 82 bars to completion, depending on leg durations.",
        "About 159% of the theory band, based on the open wave.",
        "Around 0.382 of the prior leg, give or take.",
    ]
    for phrase in fragments:
        d = _draft(Claim(text=_long(phrase), type="data_observation"))
        _, r, _ = gate_narration_draft(
            d, allowed_pages=set(), layer1_fallback="F",
        )
        assert r.fragment_claims, f"v2.14 fragment should be flagged: {phrase!r}"


def test_gate_complete_sentences_pass():
    d = _draft(Claim(
        text=_long("Price has moved beyond the projection band's upper edge."),
        type="data_observation",
    ))
    _, r, _ = gate_narration_draft(d, allowed_pages=set(), layer1_fallback="F")
    assert r.fragment_claims == ()


def test_gate_catches_hedged_generalities():
    # regression: v2.9
    hedge_phrases = [
        "Retracements may be too shallow or too deep here.",
        "The pullback typically lands at the 50% level.",
        "These checks tend to deviate from typical Fibonacci levels.",
        "Generally one would expect a sharper turn.",
    ]
    for phrase in hedge_phrases:
        d = _draft(Claim(text=_long(phrase), type="data_observation"))
        _, r, _ = gate_narration_draft(
            d, allowed_pages=set(), layer1_fallback="F",
        )
        assert r.procedural_recitation_claims, (
            f"hedged phrase should be flagged: {phrase!r}"
        )


def test_gate_catches_percent_of_pattern_range():
    # regression: v2.12
    phrases = [
        "the link wave must exceed 101% of the pattern's full range",
        "requiring 78.6% of the pattern range before forming",
        "approximately 101% of the entire price range",
        "needs to cross 101% of this pattern's range",
    ]
    for phrase in phrases:
        d = _draft(Claim(text=_long(phrase), type="data_observation"))
        _, r, _ = gate_narration_draft(
            d, allowed_pages=set(), layer1_fallback="F",
        )
        assert r.procedural_recitation_claims, (
            f"\"% of the pattern range\" should be flagged: {phrase!r}"
        )


def test_gate_catches_may_not_align_family():
    # regression: v2.10
    phrases = [
        "Wave 2 and Wave 4 may not align with expected patterns.",
        "The pullback may differ from typical Fibonacci levels.",
        "These checks tend to align with the prior leg.",
        "The durations may vary widely here.",
        "The retracement does not always reach the 50% level.",
    ]
    for phrase in phrases:
        d = _draft(Claim(text=_long(phrase), type="data_observation"))
        _, r, _ = gate_narration_draft(
            d, allowed_pages=set(), layer1_fallback="F",
        )
        assert r.procedural_recitation_claims, (
            f"v2.10 hedge phrase should be flagged: {phrase!r}"
        )
