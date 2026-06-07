from __future__ import annotations

import re

import numpy as np

from analyst.schemas.narration import NarrationDraft

# Empirically tuned (bge-base-en-v1.5, 98-page corpus): grounded sim ~0.71-0.84
# rank 1-2; mis-cited sim ~0.44-0.58 rank 26-72. Flag only when BOTH bars fail.
_MIN_SIMILARITY = 0.62
_MAX_RANK = 12


def find_ungrounded_claims(
    draft: NarrationDraft | None,
    *,
    embedder,
    corpus_embeddings: np.ndarray,
    page_to_row: dict[int, int],
) -> tuple[str, ...]:
    if draft is None or embedder is None or corpus_embeddings.size == 0:
        return ()

    scorable = [
        c for c in draft.all_claims
        if c.type == "theory_claim"
        and c.pages
        and any(p in page_to_row for p in c.pages)
    ]
    if not scorable:
        return ()

    claim_vecs = embedder.encode([c.text for c in scorable], is_query=True)

    ungrounded: list[str] = []
    for claim, qv in zip(scorable, claim_vecs, strict=True):
        # L2-normalised → dot product = cosine. Pass if grounded in ANY cited page.
        sims = corpus_embeddings @ qv
        cited_rows = [page_to_row[p] for p in claim.pages if p in page_to_row]
        best_sim = max(float(sims[r]) for r in cited_rows)
        best_rank = min(int((sims > sims[r]).sum()) + 1 for r in cited_rows)
        if best_sim < _MIN_SIMILARITY and best_rank > _MAX_RANK:
            ungrounded.append(claim.text)
    return tuple(ungrounded)


# Leading anchor avoids matching fractional tails (`.5` inside `12.5`).
_NUMBER_TOKEN_RE = re.compile(r"(?<![\d.])-?\d+(?:\.\d+)?%?")

# Standard Fib constants — quoting these isn't invention.
_FIB_CONSTANTS: frozenset[str] = frozenset({
    "0.146", "0.236", "0.382", "0.5", "0.618", "0.786",
    "1", "1.272", "1.382", "1.618", "2", "2.618",
    "14.6", "23.6", "38.2", "50", "61.8", "78.6",
    "100", "101", "127.2", "138.2", "161.8", "261.8",
})

# Counting ints used in English idioms — never the figures rule 4 protects.
_TRIVIAL_INTS: frozenset[str] = frozenset(
    {str(n) for n in range(0, 11)}
)


def _normalize_token(tok: str) -> str:
    return tok.lstrip("+-").rstrip("%")


def _is_groundable_number(tok: str) -> bool:
    bare = _normalize_token(tok)
    return bool(bare) and bare not in _FIB_CONSTANTS and bare not in _TRIVIAL_INTS


def _token_in_corpus(tok: str, corpus: str) -> bool:
    # Signed/percent need verbatim — bare "54%" would match "p.54" or "2054".
    bare = _normalize_token(tok)
    if not bare:
        return False
    if tok.endswith("%") or tok.startswith(("-", "+")):
        forms = {tok, tok.lstrip("+"), bare + "%"}
        return any(f in corpus for f in forms)
    # Number-boundary match so a fabricated "450" isn't masked by "3450"/"45000".
    return re.search(rf"(?<![\d.]){re.escape(bare)}(?![\d.])", corpus) is not None


def find_fabricated_numbers(
    draft: NarrationDraft | None,
    *,
    layer1_md: str,
) -> tuple[str, ...]:
    # data_observation only — theory_claims quote Fib constants, disclosures are meta.
    if draft is None or not layer1_md:
        return ()
    flagged: list[str] = []
    for c in draft.all_claims:
        if c.type != "data_observation":
            continue
        tokens = _NUMBER_TOKEN_RE.findall(c.text)
        groundable = [t for t in tokens if _is_groundable_number(t)]
        if not groundable:
            continue
        missing = [t for t in groundable if not _token_in_corpus(t, layer1_md)]
        if missing:
            flagged.append(c.text)
    return tuple(flagged)
