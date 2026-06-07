"""Q&A core — torch-free via a fake embedder (deterministic vectors) and a fake
LLM (canned JSON), so CI runs it without the grounding extra."""

from __future__ import annotations

import numpy as np
import pytest

from analyst.client.gate import gate_narration_draft
from analyst.orchestrator import _QA_OUT_OF_SCOPE_MSG, build_analyst
from analyst.prompts.qa import build_qa_prompt
from analyst.schemas.narration import parse_narration_draft
from analyst.theory.chunker import Chunk
from analyst.theory.retriever import Retriever
from tests.analyst._helpers import FakeEmbedder, make_scenario
from tests.analyst._helpers import make_uptrend_then_drop_bars as _bars


class _FakeLLM:
    model_id = "fake"

    def __init__(self, response="", raises=False):
        self.response = response
        self.raises = raises
        self.calls = 0

    def complete(self, messages, *, format=None):
        self.calls += 1
        if self.raises:
            raise AssertionError("LLM must not be called")
        return self.response


_CHUNKS = [Chunk(page=1, body="alpha"), Chunk(page=2, body="beta"), Chunk(page=3, body="gamma")]
_EMB = np.eye(3, dtype=np.float32)  # L2-normalized rows, row i == chunks[i]


def _analyst(llm, embedder, tmp_path):
    return build_analyst(
        chunks=list(_CHUNKS), embeddings=_EMB.copy(),
        llm_client=llm, embedder=embedder, cache_dir=tmp_path,
    )


def test_by_similarity_scored_orders_and_scores() -> None:
    r = Retriever(chunks=list(_CHUNKS), embeddings=_EMB.copy(), embedder=FakeEmbedder())
    out = r.by_similarity_scored("q", k=2)
    assert [c.page for c, _ in out] == [1, 2]  # query [1,0,0] → page 1 top
    assert out[0][1] == pytest.approx(1.0)
    assert out[1][1] == pytest.approx(0.0)


def test_build_qa_prompt_chart_block_optional() -> None:
    bare = build_qa_prompt("Q?", "REFS")
    assert "[CHART DATA]" not in bare
    assert "[THEORY REFS]" in bare and "[QUESTION]" in bare
    withchart = build_qa_prompt("Q?", "REFS", chart_md="DATA")
    assert "[CHART DATA]" in withchart


def test_answer_question_happy_path(tmp_path) -> None:
    resp = (
        '{"paragraphs": [[{"text": "A five-wave trend advances in five '
        'distinct legs that share one direction.", "type": "theory_claim", '
        '"pages": [1]}]]}'
    )
    llm = _FakeLLM(response=resp)
    out = _analyst(llm, FakeEmbedder(), tmp_path).answer_question("what is a five-wave trend?")
    assert not out.out_of_scope and not out.fell_back
    # Query [1,0,0] → only page 1 clears the per-chunk floor (others score 0).
    assert out.retrieved_pages == (1,)
    assert "(p.1)" in out.answer
    assert [c.page for c in out.citations] == [1]
    assert llm.calls == 1


def test_answer_question_out_of_scope_skips_llm(tmp_path) -> None:
    # Weak top similarity + no chart → refuse before any LLM call.
    embedder = FakeEmbedder(vectors={"price of bitcoin today?": [0.1, 0.1, 0.1]})
    llm = _FakeLLM(raises=True)
    out = _analyst(llm, embedder, tmp_path).answer_question("price of bitcoin today?")
    assert out.out_of_scope
    assert out.answer == _QA_OUT_OF_SCOPE_MSG
    assert out.citations == ()
    assert llm.calls == 0


def test_force_refresh_bypasses_cache(tmp_path) -> None:
    resp = (
        '{"paragraphs": [[{"text": "A five-wave trend advances in five '
        'distinct legs that share one direction.", "type": "theory_claim", '
        '"pages": [1]}]]}'
    )
    llm = _FakeLLM(response=resp)
    a = _analyst(llm, FakeEmbedder(), tmp_path)
    a.answer_question("what is a five-wave trend?")
    assert llm.calls == 1
    out = a.answer_question("what is a five-wave trend?", force_refresh=True)
    assert llm.calls == 2 and not out.cached


def test_answer_question_caches_second_call(tmp_path) -> None:
    resp = (
        '{"paragraphs": [[{"text": "A five-wave trend advances in five '
        'distinct legs that share one direction.", "type": "theory_claim", '
        '"pages": [1]}]]}'
    )
    llm = _FakeLLM(response=resp)
    a = _analyst(llm, FakeEmbedder(), tmp_path)
    first = a.answer_question("what is a five-wave trend?")
    second = a.answer_question("what is a five-wave trend?")
    assert not first.cached and second.cached
    assert llm.calls == 1


def test_answer_question_requires_embedder(tmp_path) -> None:
    a = _analyst(_FakeLLM(response="{}"), None, tmp_path)
    with pytest.raises(RuntimeError, match="embedder"):
        a.answer_question("anything")


def test_gate_min_chars_lets_short_answer_pass() -> None:
    # A concise grounded answer (40-120 chars) passes the Q&A floor but would
    # trip the default narration floor.
    draft = parse_narration_draft(
        '{"paragraphs": [[{"text": "Wave 3 must never be the shortest.", '
        '"type": "theory_claim", "pages": [22]}]]}'
    )
    _, strict, strict_fb = gate_narration_draft(
        draft, allowed_pages={22}, layer1_fallback="fb",
    )
    assert strict.too_short and strict_fb
    _, lax, lax_fb = gate_narration_draft(
        draft, allowed_pages={22}, layer1_fallback="fb", min_chars=40,
    )
    assert not lax.too_short and not lax_fb


def test_scenario_without_bars_raises(tmp_path) -> None:
    a = _analyst(_FakeLLM(response="{}"), FakeEmbedder(), tmp_path)
    with pytest.raises(ValueError, match="bars"):
        a.answer_question("anything", scenario=make_scenario())


def test_relevance_floor_drops_marginal_pages(tmp_path) -> None:
    emb = FakeEmbedder(vectors={"q": [0.95, 0.7, 0.2]})
    resp = (
        '{"paragraphs": [[{"text": "A five-wave trend advances in five '
        'distinct legs that share one direction.", "type": "theory_claim", '
        '"pages": [1]}]]}'
    )
    out = _analyst(_FakeLLM(response=resp), emb, tmp_path).answer_question("q")
    # page 3 (0.2 < floor) dropped; page 2 (0.7) kept beside top page 1.
    assert out.retrieved_pages == (1, 2)


def test_theory_number_not_flagged_as_fabricated(tmp_path) -> None:
    chunks = [Chunk(page=1, body="A Trend linkage must exceed 200 percent of the prior leg.")]
    embeddings = np.array([[1.0]], dtype=np.float32)
    resp = (
        '{"paragraphs": [[{"text": "The linkage must run beyond 200 percent '
        'of the prior leg.", "type": "data_observation", "pages": []}]]}'
    )
    a = build_analyst(
        chunks=chunks, embeddings=embeddings, llm_client=_FakeLLM(response=resp),
        embedder=FakeEmbedder(default=[1.0]), cache_dir=tmp_path,
    )
    out = a.answer_question(
        "how big is a trend linkage?", scenario=make_scenario(), bars=_bars(),
    )
    # "200" lives in the theory ref, not the chart block — must NOT be flagged.
    assert out.citation_report.fabricated_number_claims == ()
    assert not out.fell_back


def test_fallback_not_cached(tmp_path) -> None:
    llm = _FakeLLM(response="{}")  # unparseable draft → gate falls back
    a = _analyst(llm, FakeEmbedder(), tmp_path)
    first = a.answer_question("what is a five-wave trend?")
    calls_after_first = llm.calls
    second = a.answer_question("what is a five-wave trend?")
    assert first.fell_back and second.fell_back
    assert not second.cached
    assert llm.calls > calls_after_first  # retry re-hit the LLM, not the cache
