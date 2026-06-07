from __future__ import annotations

import threading
from collections.abc import Sequence

import numpy as np

MODEL_NAME = "BAAI/bge-base-en-v1.5"
# Pinned SHA — HF force-push could silently shift embedding space. Bump with corpus.
MODEL_REVISION = "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"
EMBED_DIM = 768

# bge-*-en-v1.5 is asymmetric — queries need this prefix.
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


def _prepare_texts(texts: Sequence[str], is_query: bool) -> list[str]:
    if is_query:
        return [QUERY_INSTRUCTION + t for t in texts]
    return list(texts)


class Embedder:
    def __init__(
        self,
        model_name: str = MODEL_NAME,
        revision: str | None = MODEL_REVISION,
    ) -> None:
        self.model_name = model_name
        self.revision = revision
        self._model = None
        # Double-checked locking: 4 parallel mode threads can race the first grounding check.
        self._load_lock = threading.Lock()

    def _load(self):
        if self._model is None:
            with self._load_lock:
                if self._model is None:
                    from sentence_transformers import SentenceTransformer  # heavy

                    self._model = SentenceTransformer(
                        self.model_name, revision=self.revision,
                    )
        return self._model

    def prewarm(self) -> None:
        # Absorb 10-30s load off the request path (call at startup).
        self._load()

    def encode(self, texts: Sequence[str], *, is_query: bool = False) -> np.ndarray:
        model = self._load()
        vecs = model.encode(
            _prepare_texts(texts, is_query),
            convert_to_numpy=True,
            normalize_embeddings=True,  # cosine = dot product
            show_progress_bar=False,
        )
        return vecs.astype(np.float32, copy=False)
