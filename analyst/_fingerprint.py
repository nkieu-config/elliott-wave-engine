from __future__ import annotations

import hashlib
from pathlib import Path

_ANALYST_ROOT = Path(__file__).resolve().parent

# Keep MINIMAL — each excluded name is a category that won't invalidate the cache.
_EXCLUDED_PARTS = frozenset({"eval", "__pycache__", ".cache"})

# Source globs whose CONTENT must invalidate the narration cache when it changes:
# - *.py  : pipeline logic (prompts, gate, serializers, embedder model/revision)
# - data/*.jsonl, data/*.npy : the theory corpus + its embeddings. A corpus
#   rebuilt with a new model/source touches NO .py, so without hashing the data
#   files a cached narration would keep citing a corpus it was never grounded in.
_FINGERPRINTED_GLOBS = ("*.py", "theory/data/*.jsonl", "theory/data/*.npy")


def _compute_fingerprint() -> str:
    h = hashlib.sha256()
    files = sorted(
        {
            p
            for glob in _FINGERPRINTED_GLOBS
            for p in _ANALYST_ROOT.glob(f"**/{glob}")
            if _EXCLUDED_PARTS.isdisjoint(p.relative_to(_ANALYST_ROOT).parts)
        },
        key=lambda p: p.relative_to(_ANALYST_ROOT).as_posix(),
    )
    for p in files:
        h.update(p.relative_to(_ANALYST_ROOT).as_posix().encode("utf-8"))
        try:
            h.update(p.read_bytes())
        except OSError:
            h.update(b"<unreadable>")  # vanished mid-rebuild — degrade, don't crash import
    return h.hexdigest()[:16]


PIPELINE_FINGERPRINT: str = _compute_fingerprint()
