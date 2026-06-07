"""Integrity checks on the SHIPPED theory corpus (chunks.jsonl + embeddings.npy).

These guard the data files themselves, not the chunker/embedder logic — a
partial or stale regeneration (one file rewritten, the other not) is exactly
the silent-misalignment failure the Retriever alignment guard defends against.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from analyst.theory.chunker import Chunk, chunk_theory_file, enrich_aliases
from analyst.theory.embedder import EMBED_DIM, MODEL_NAME, MODEL_REVISION
from analyst.theory.make_embeddings import (
    DEFAULT_THEORY,
    META_NAME,
    corpus_fingerprint,
)
from analyst.theory.retriever import Retriever

_DATA_DIR = Path(__file__).resolve().parents[3] / "analyst" / "theory" / "data"
_CHUNKS = _DATA_DIR / "chunks.jsonl"
_EMBEDDINGS = _DATA_DIR / "embeddings.npy"
_META = _DATA_DIR / META_NAME


@pytest.fixture(scope="module")
def chunks() -> list[Chunk]:
    rows = [
        json.loads(line)
        for line in _CHUNKS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return [Chunk(**r) for r in rows]


@pytest.fixture(scope="module")
def embeddings() -> np.ndarray:
    return np.load(_EMBEDDINGS)


def test_data_files_exist() -> None:
    assert _CHUNKS.is_file(), f"missing {_CHUNKS}"
    assert _EMBEDDINGS.is_file(), f"missing {_EMBEDDINGS}"


def test_chunk_count_matches_embedding_rows(chunks, embeddings) -> None:
    # The load-bearing invariant: row i of embeddings is chunks[i]'s vector.
    assert embeddings.shape[0] == len(chunks), (
        f"{len(chunks)} chunks but {embeddings.shape[0]} embedding rows — "
        f"regenerate via analyst/theory/make_embeddings.py"
    )


def test_embedding_shape_and_dtype(embeddings) -> None:
    assert embeddings.ndim == 2
    assert embeddings.shape[1] == EMBED_DIM
    assert embeddings.dtype == np.float32


def test_embeddings_are_l2_normalized(embeddings) -> None:
    # grounding treats dot product as cosine, which requires unit-norm rows.
    norms = np.linalg.norm(embeddings, axis=1)
    np.testing.assert_allclose(norms, 1.0, atol=1e-5)


def test_pages_are_unique(chunks) -> None:
    # by_pages builds a {page: chunk} dict; duplicate pages would silently drop.
    pages = [c.page for c in chunks]
    assert len(pages) == len(set(pages)), "duplicate page numbers in corpus"


def test_retriever_accepts_real_corpus(chunks, embeddings) -> None:
    # The alignment guard must pass for the data we actually ship.
    Retriever(chunks=chunks, embeddings=embeddings, embedder=None)


def test_retriever_rejects_truncated_embeddings(chunks, embeddings) -> None:
    # Regression: a stale/partial regen (fewer vectors than chunks) must fail
    # loudly at construction, not mis-score or IndexError mid-request.
    truncated = embeddings[:-1]
    with pytest.raises(ValueError, match="misaligned"):
        Retriever(chunks=chunks, embeddings=truncated, embedder=None)


def test_chunks_match_source(chunks) -> None:
    # The drift guard: chunks.jsonl is derived from the theory markdown, but
    # make_embeddings runs by hand — editing the source without rebuilding ships
    # stale theory text into prompts. Re-chunk (+ alias enrich, as the build
    # does) and demand they match.
    fresh = enrich_aliases(chunk_theory_file(DEFAULT_THEORY))
    assert fresh == chunks, (
        "chunks.jsonl is out of sync with the theory source — "
        "rebuild via analyst/theory/make_embeddings.py"
    )


def test_corpus_meta_matches_corpus(chunks, embeddings) -> None:
    # corpus_meta.json ties the embeddings back to the exact chunk text they
    # were built from, so a chunks-only resync (text rebuilt, .npy not) fails
    # here instead of silently mis-scoring the grounding check.
    assert _META.is_file(), f"missing {_META} — rebuild via make_embeddings.py"
    meta = json.loads(_META.read_text(encoding="utf-8"))
    assert meta["text_sha256"] == corpus_fingerprint(chunks), (
        "corpus_meta hash != chunks.jsonl — corpus was regenerated partially; "
        "rebuild via analyst/theory/make_embeddings.py"
    )
    assert meta["count"] == len(chunks)
    assert meta["embed_dim"] == embeddings.shape[1] == EMBED_DIM
    assert meta["model_name"] == MODEL_NAME
    assert meta["revision"] == MODEL_REVISION
