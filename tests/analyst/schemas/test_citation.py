import dataclasses

import pytest

from analyst.schemas.citation import CitationRef, CitationReport, TheoryRef


def test_theory_ref_concept_operationalization():
    ref = TheoryRef(
        pages=(91, 96),
        concept="Same-degree principle",
        binding="concept_operationalization",
        note="log-CV proxy",
    )
    assert ref.binding == "concept_operationalization"
    assert 91 in ref.pages
    with pytest.raises(dataclasses.FrozenInstanceError):
        ref.pages = (1,)


def test_theory_ref_heuristic_has_no_pages():
    ref = TheoryRef(
        pages=(),
        concept="Chart appearance",
        binding="heuristic",
        note="no theory binding",
    )
    assert ref.pages == ()


def test_citation_report_ok_when_all_cited_pages_allowed():
    rep = CitationReport(
        cited_pages={34, 110},
        allowed_pages={21, 22, 34, 110},
        unsourced_claims=[],
    )
    assert rep.ok is True


def test_citation_report_fail_when_page_outside_allowed():
    rep = CitationReport(
        cited_pages={34, 200},
        allowed_pages={34, 110},
        unsourced_claims=[],
    )
    assert rep.ok is False
    assert 200 in rep.disallowed_pages


def test_citation_ref_construction_and_frozen():
    cr = CitationRef(page=34, claim_sentence="The trendline broke.")
    assert cr.page == 34
    assert cr.claim_sentence == "The trendline broke."
    with pytest.raises(dataclasses.FrozenInstanceError):
        cr.page = 35


def test_citation_report_fail_when_unsourced_claims_present():
    rep = CitationReport(
        cited_pages={34}, allowed_pages={34},
        unsourced_claims=["A sentence with no citation."],
    )
    assert rep.ok is False
    assert isinstance(rep.unsourced_claims, tuple)


def test_ungrounded_citation_claims_is_a_soft_flag():
    rep = CitationReport(
        cited_pages={34}, allowed_pages={34},
        ungrounded_citation_claims=["A claim its cited page does not support."],
    )
    assert rep.ok is True
    assert isinstance(rep.ungrounded_citation_claims, tuple)


def test_prose_page_claims_is_a_soft_flag():
    rep = CitationReport(
        prose_page_claims=["Leg-by-leg retracement, see pages 103 and 111."],
    )
    assert rep.ok is True
    assert isinstance(rep.prose_page_claims, tuple)
