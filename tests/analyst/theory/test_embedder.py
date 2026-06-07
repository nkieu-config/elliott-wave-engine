import numpy as np
import pytest

from analyst.theory.embedder import (
    EMBED_DIM,
    QUERY_INSTRUCTION,
    Embedder,
    _prepare_texts,
)


def test_query_instruction_applied_to_queries_only():
    assert _prepare_texts(["wave 3 rule"], is_query=False) == ["wave 3 rule"]
    assert _prepare_texts(["wave 3 rule"], is_query=True) == [
        QUERY_INSTRUCTION + "wave 3 rule"
    ]


@pytest.mark.slow
def test_embedder_returns_correct_shape():
    pytest.importorskip("sentence_transformers")  # optional `grounding` extra
    e = Embedder()
    vecs = e.encode(["hello world", "elliott wave theory"])
    assert vecs.shape == (2, EMBED_DIM)
    assert vecs.dtype == np.float32


@pytest.mark.slow
def test_embedder_is_deterministic_per_input():
    pytest.importorskip("sentence_transformers")  # optional `grounding` extra
    e = Embedder()
    a = e.encode(["confirmation concept"])
    b = e.encode(["confirmation concept"])
    np.testing.assert_allclose(a, b, atol=1e-5)
