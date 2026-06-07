import json
from pathlib import Path

import numpy as np

from analyst.theory.make_embeddings import META_NAME, build_embeddings


def test_build_embeddings_writes_jsonl_and_npy(tmp_path: Path):
    theory = tmp_path / "th.md"
    theory.write_text(
        "## Page 6\n\nfoo\n\n## Page 7\n\nbar\n", encoding="utf-8",
    )

    class FakeEmbedder:
        model_name = "fake"
        def encode(self, texts):
            return np.zeros((len(texts), 4), dtype=np.float32)

    out_dir = tmp_path / "data"
    out_dir.mkdir()
    build_embeddings(
        theory_path=theory,
        out_dir=out_dir,
        embedder=FakeEmbedder(),
    )
    assert (out_dir / "chunks.jsonl").exists()
    assert (out_dir / "embeddings.npy").exists()
    arr = np.load(out_dir / "embeddings.npy")
    assert arr.shape == (2, 4)

    # The meta sidecar is load-bearing — the corpus alignment guard reads it.
    meta_path = out_dir / META_NAME
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["count"] == 2
    assert meta["embed_dim"] == 4
    assert meta["model_name"] == "fake"
    assert meta["text_sha256"]  # fingerprint present for stale-regen detection
