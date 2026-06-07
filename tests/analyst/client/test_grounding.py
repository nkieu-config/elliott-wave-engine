import json
from pathlib import Path

import numpy as np
import pytest

import analyst.theory
from analyst.client.grounding import (
    find_fabricated_numbers,
    find_ungrounded_claims,
)
from analyst.schemas.narration import Claim, NarrationDraft
from tests.analyst._helpers import FakeEmbedder


def _draft(*claims: Claim) -> NarrationDraft:
    return NarrationDraft(paragraphs=[list(claims)])


_CORPUS = np.eye(20, dtype=np.float32)
_PAGE_TO_ROW = {100 + i: i for i in range(20)}


def test_grounded_claim_is_not_flagged():
    vec = np.full(20, 0.1, dtype=np.float32)
    vec[0] = 0.9
    emb = FakeEmbedder({"claim": vec})
    draft = _draft(Claim(text="claim", type="theory_claim", pages=[100]))
    assert find_ungrounded_claims(
        draft, embedder=emb, corpus_embeddings=_CORPUS, page_to_row=_PAGE_TO_ROW,
    ) == ()


def test_fabricated_claim_far_from_its_page_is_flagged():
    vec = np.full(20, 0.1, dtype=np.float32)
    vec[:15] = np.linspace(0.9, 0.2, 15)
    emb = FakeEmbedder({"fabricated": vec})
    draft = _draft(Claim(text="fabricated", type="theory_claim", pages=[118]))
    assert find_ungrounded_claims(
        draft, embedder=emb, corpus_embeddings=_CORPUS, page_to_row=_PAGE_TO_ROW,
    ) == ("fabricated",)


def test_low_similarity_but_top_ranked_is_not_flagged():
    vec = np.full(20, 0.05, dtype=np.float32)
    vec[0] = 0.5
    emb = FakeEmbedder({"claim": vec})
    draft = _draft(Claim(text="claim", type="theory_claim", pages=[100]))
    assert find_ungrounded_claims(
        draft, embedder=emb, corpus_embeddings=_CORPUS, page_to_row=_PAGE_TO_ROW,
    ) == ()


def test_multi_page_claim_passes_if_any_cited_page_supports_it():
    vec = np.full(20, 0.1, dtype=np.float32)
    vec[:15] = np.linspace(0.9, 0.2, 15)
    vec[0] = 0.9
    emb = FakeEmbedder({"claim": vec})
    draft = _draft(Claim(text="claim", type="theory_claim", pages=[118, 100]))
    assert find_ungrounded_claims(
        draft, embedder=emb, corpus_embeddings=_CORPUS, page_to_row=_PAGE_TO_ROW,
    ) == ()


def test_non_theory_claims_and_pageless_claims_are_skipped():
    vec = np.full(20, 0.05, dtype=np.float32)
    emb = FakeEmbedder({"obs": vec, "disc": vec})
    draft = _draft(
        Claim(text="obs", type="data_observation", pages=[]),
        Claim(text="disc", type="disclosure", pages=[]),
    )
    assert find_ungrounded_claims(
        draft, embedder=emb, corpus_embeddings=_CORPUS, page_to_row=_PAGE_TO_ROW,
    ) == ()


def test_claim_citing_a_page_outside_the_corpus_is_skipped():
    emb = FakeEmbedder({"claim": np.full(20, 0.05, dtype=np.float32)})
    draft = _draft(Claim(text="claim", type="theory_claim", pages=[999]))
    assert find_ungrounded_claims(
        draft, embedder=emb, corpus_embeddings=_CORPUS, page_to_row=_PAGE_TO_ROW,
    ) == ()


def test_degrades_gracefully_without_a_draft_or_embedder():
    assert find_ungrounded_claims(
        None, embedder=FakeEmbedder({}), corpus_embeddings=_CORPUS,
        page_to_row=_PAGE_TO_ROW,
    ) == ()
    draft = _draft(Claim(text="x", type="theory_claim", pages=[100]))
    assert find_ungrounded_claims(
        draft, embedder=None, corpus_embeddings=_CORPUS, page_to_row=_PAGE_TO_ROW,
    ) == ()


@pytest.mark.slow
def test_real_embedder_flags_the_p110_cycle_fabrication():
    # Needs the optional `grounding` extra (sentence-transformers/torch); skip
    # cleanly on a lean install. Restore with `uv sync --extra grounding`.
    pytest.importorskip("sentence_transformers")
    from analyst.theory.embedder import Embedder

    data = Path(analyst.theory.__file__).parent / "data"
    corpus = np.load(data / "embeddings.npy")
    order = [
        json.loads(line)["page"]
        for line in (data / "chunks.jsonl").read_text().splitlines()
        if line.strip()
    ]
    page_to_row = {p: i for i, p in enumerate(order)}
    emb = Embedder()

    fabricated = _draft(Claim(
        text="A completed five-wave sequence marks the end of a cycle and "
             "the prior trend is expected to resume after the pattern "
             "finishes.",
        type="theory_claim", pages=[110],
    ))
    faithful = _draft(Claim(
        text="In a five-wave trend pattern the structure can complete at "
             "several Fibonacci measurement targets.",
        type="theory_claim", pages=[110],
    ))

    assert find_ungrounded_claims(
        fabricated, embedder=emb, corpus_embeddings=corpus,
        page_to_row=page_to_row,
    ), "the p.110 cycle fabrication should be flagged ungrounded"
    assert not find_ungrounded_claims(
        faithful, embedder=emb, corpus_embeddings=corpus,
        page_to_row=page_to_row,
    ), "a faithful claim about p.110 must not be flagged"


def test_fabricated_numbers_flags_a_claim_with_unknown_price():
    layer1_md = "## Targets\n- Wave 5 projection: $125.54 (38.2% retracement)"
    flagged = _draft(Claim(
        text="The pattern is invalidated below $98.01.",
        type="data_observation",
    ))
    out = find_fabricated_numbers(flagged, layer1_md=layer1_md)
    assert out, "$98.01 is not in Layer-1 → claim must be flagged"


def test_fabricated_numbers_accepts_a_claim_with_grounded_numbers():
    layer1_md = "- Wave 5 projection: $125.54\n- Invalidation: $98.01"
    grounded = _draft(Claim(
        text="The pattern is invalidated below $98.01 and tops near $125.54.",
        type="data_observation",
    ))
    assert find_fabricated_numbers(grounded, layer1_md=layer1_md) == ()


def test_fabricated_numbers_skips_standard_fibonacci_constants():
    layer1_md = "## Targets\n- Wave 5: $125.54"
    claim = _draft(Claim(
        text="The 38.2% retracement marks the lower band of the projection.",
        type="data_observation",
    ))
    assert find_fabricated_numbers(claim, layer1_md=layer1_md) == ()


def test_fabricated_numbers_skips_trivial_counting_integers():
    layer1_md = "(empty)"
    claim = _draft(Claim(
        text="Wave 5 is the open leg and is the 1 remaining wave to form.",
        type="data_observation",
    ))
    assert find_fabricated_numbers(claim, layer1_md=layer1_md) == ()


def test_fabricated_numbers_strict_for_rounded_signed_percentages():
    # regression: v2.14
    layer1_md = (
        "## Decision Summary\n"
        "- Invalidation: $98.01 (-53.9% from current)\n"
        "## What Can Follow\n"
        "- Cite p.54 for the connector rule\n"
    )
    flagged = _draft(Claim(
        text="The primary's invalidation is only -54% below current price.",
        type="data_observation",
    ))
    out = find_fabricated_numbers(flagged, layer1_md=layer1_md)
    assert out, (
        '"-54%" should be flagged as fabricated/rounded — the layer-1 '
        'data has "-53.9%", not "-54%". The bare "54" in "p.54" must '
        'NOT count as a valid match for a percentage token.'
    )


def test_fabricated_numbers_accepts_verbatim_signed_percentage():
    # regression: v2.14
    layer1_md = "- Invalidation: $98.01 (-53.9% from current)"
    accepted = _draft(Claim(
        text="The primary's invalidation is -53.9% below current.",
        type="data_observation",
    ))
    assert find_fabricated_numbers(accepted, layer1_md=layer1_md) == ()


def test_fabricated_numbers_only_scores_data_observation_claims():
    layer1_md = "(empty)"
    claim = _draft(Claim(
        text="The 78.6% threshold defines a Sideway link wave.",
        type="theory_claim", pages=[73],
    ))
    assert find_fabricated_numbers(claim, layer1_md=layer1_md) == ()


def test_fabricated_number_not_masked_by_a_substring_match():
    # "450" must be flagged even though it appears INSIDE "3450"/"45000" — the old
    # bare `in` substring check let fabricated numbers through.
    draft = _draft(Claim(text="target near 450", type="data_observation", pages=[]))
    assert find_fabricated_numbers(
        draft, layer1_md="confirmation at 3450 and 45000",
    ) == ("target near 450",)


def test_number_with_clean_boundaries_is_grounded():
    draft = _draft(Claim(text="target near 450", type="data_observation", pages=[]))
    assert find_fabricated_numbers(draft, layer1_md="target sits at 450 exactly") == ()
