import numpy as np
import pytest

from analyst.theory.chunker import Chunk
from analyst.theory.retriever import Retriever


@pytest.fixture
def toy_chunks():
    return [
        Chunk(page=34, body="Confirmation Concept — 4 levels for 5W_TREND"),
        Chunk(page=55, body="3W Confirmation — 2 conditions"),
        Chunk(page=110, body="5W_TREND Fibonacci Flow"),
    ]


@pytest.fixture
def toy_embeddings(toy_chunks):
    rng = np.random.default_rng(0)
    return rng.standard_normal((len(toy_chunks), 4), dtype=np.float32)


def test_retrieve_by_page_returns_exact_chunk(toy_chunks, toy_embeddings):
    r = Retriever(chunks=toy_chunks, embeddings=toy_embeddings, embedder=None)
    out = r.by_pages([34, 110])
    assert [c.page for c in out] == [34, 110]


def test_retrieve_by_page_skips_missing(toy_chunks, toy_embeddings):
    r = Retriever(chunks=toy_chunks, embeddings=toy_embeddings, embedder=None)
    out = r.by_pages([34, 999])
    assert [c.page for c in out] == [34]


def test_retrieve_by_similarity_returns_top_k(toy_chunks, toy_embeddings):
    class FakeEmbedder:
        def __init__(self):
            self.last_is_query = None

        def encode(self, texts, *, is_query=False):
            self.last_is_query = is_query
            v = toy_embeddings[0:1].copy()
            return v / np.linalg.norm(v, axis=1, keepdims=True)

    norm = toy_embeddings / np.linalg.norm(toy_embeddings, axis=1, keepdims=True)
    fake = FakeEmbedder()
    r = Retriever(chunks=toy_chunks, embeddings=norm, embedder=fake)
    out = r.by_similarity("anything", k=2)
    assert len(out) == 2
    assert out[0].page == 34
    assert fake.last_is_query is True
