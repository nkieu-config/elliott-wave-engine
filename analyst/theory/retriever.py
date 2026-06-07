from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from analyst.theory.chunker import Chunk


class _EmbedderProto(Protocol):
    def encode(
        self, texts: Sequence[str], *, is_query: bool = False,
    ) -> np.ndarray: ...


@dataclass
class Retriever:
    # Narration uses by_pages (deterministic slot→page map); Q&A uses similarity.
    chunks: list[Chunk]
    embeddings: np.ndarray            # (N, D), L2-normalized
    embedder: _EmbedderProto | None   # None = page-only mode

    def __post_init__(self) -> None:
        # Row i of `embeddings` MUST correspond to chunks[i] (grounding indexes
        # by chunk position). Empty = page-only mode; otherwise row count must
        # match exactly or a stale regen mis-scores claims silently / IndexErrors.
        n_rows = self.embeddings.shape[0] if self.embeddings.size else 0
        if n_rows and n_rows != len(self.chunks):
            raise ValueError(
                f"Corpus misaligned: {len(self.chunks)} chunks but "
                f"{n_rows} embedding rows — regenerate via "
                f"analyst/theory/make_embeddings.py so both files match."
            )

    def by_pages(self, pages: Iterable[int]) -> list[Chunk]:
        idx = {c.page: c for c in self.chunks}
        return [idx[p] for p in pages if p in idx]

    def by_similarity(self, query: str, k: int = 3) -> list[Chunk]:
        return [c for c, _ in self.by_similarity_scored(query, k)]

    def by_similarity_scored(
        self, query: str, k: int = 3,
    ) -> list[tuple[Chunk, float]]:
        # Scores exposed for Q&A's out-of-scope gate (cosine, since rows are L2-normed).
        if self.embedder is None:
            raise RuntimeError("Embedder not configured; cannot do similarity search")
        q = self.embedder.encode([query], is_query=True)
        scores = (self.embeddings @ q[0]).astype(np.float32)
        top = np.argsort(-scores)[:k]
        return [(self.chunks[i], float(scores[i])) for i in top]
