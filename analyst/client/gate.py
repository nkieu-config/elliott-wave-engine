from __future__ import annotations

import re
from collections.abc import Iterable

from analyst.schemas.citation import CitationReport
from analyst.schemas.narration import NarrationDraft, render_narration

# Floor below which rendered narration is degenerate (prompts ask for 2-3 paragraphs).
_MIN_NARRATION_CHARS = 120

# Rule 5 leaked identifiers: snake_case, UPPER_CASE w/ underscore (≥1 letter),
# leg codes S2/T1 (lowercase s4 allowed for chart annotations), link codes +S/+T/+SE.
_RAW_IDENTIFIER_RE = re.compile(
    r"\b(?:[a-z]+_[a-z][a-z_]*"
    r"|(?=[A-Z0-9_]*[A-Z])[A-Z0-9]+_[A-Z0-9_]+"
    r"|[ST]\d+)\b"
    r"|(?<![A-Za-z0-9_])\+[ST]E?(?![A-Za-z0-9_])"
)

# Arithmetic chain (operator + ≥2 numbers). SOFT — two-number floor avoids
# tripping on bare metric definitions ("drawdown ratio = max drawdown divided by leg length").
_ARITH_OP_RE = re.compile(
    r"[×*÷]|\b(?:times|multipl(?:y|ies|ied|ying)|divided\s+by|product\s+of)\b",
    re.IGNORECASE,
)
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def _is_arithmetic_chain(text: str) -> bool:
    return bool(_ARITH_OP_RE.search(text)) and len(_NUMBER_RE.findall(text)) >= 2


# Prose page ref — citation belongs in `pages` field (rule 3). SOFT.
_PROSE_PAGE_RE = re.compile(r"\b(?:pages?\s+\d|p\.\s*\d)", re.IGNORECASE)


# Internal-implementation names forbidden by rule 7. SOFT.
_META_SYSTEM_RE = re.compile(
    r"\b(?:"
    r"verifier"
    r"|layer[\s\-]?1"
    r"|the\s+gate"
    r"|citation\s+gate"
    r"|bottleneck\s+diagnos"
    r"|score[\s\-]?components?\s+block"
    r"|targets?\s+block"
    r"|confirmation\s+block"
    r"|scenario[\s\-]?comparison\s+block"
    r")\b",
    re.IGNORECASE,
)


# Procedural recitation — model paraphrases a check's definition instead of
# reading chart values. Also catches hedged generalities. SOFT.
_PROCEDURAL_RECITATION_RE = re.compile(
    r"\b(?:"
    r"the\s+measurement\s+requires"
    r"|is\s+calculated\s+by"
    r"|is\s+computed\s+by"
    r"|involves?\s+(?:marking|measuring|comparing|computing)"
    r"|evaluates?\s+how\s+(?:much\s+|many\s+|deeply\s+)?"
    r"|assesses?\s+how\s+(?:much\s+|many\s+|smooth\s+|the\s+)?"
    r"|works\s+by\s+(?:marking|measuring|comparing|computing|taking)"
    r"|is\s+defined\s+as\s+(?:the\s+ratio|the\s+result)"
    r"|as\s+per\s+the\s+measurement\s+rules"
    # Hedged generalities — the model standing in for missing data
    r"|some\s+(?:retracements?\s+)?(?:may|might)\s+be\s+(?:too\s+)?(?:shallow|deep|small|large|fast|slow)"
    r"|may\s+be\s+too\s+(?:shallow|deep|small|large|fast|slow)"
    r"|may\s+not\s+(?:align|match|fit|conform|reach|hold)"
    r"|may\s+(?:differ|vary|diverge)"
    r"|might\s+(?:not\s+)?(?:align|match|fit|conform|reach|hold|differ|vary)"
    r"|do(?:es)?\s+not\s+always\s+(?:align|match|fit|reach)"
    r"|typically\s+(?:lands?|sits?|reaches?|spans?|takes?|runs?)"
    r"|generally\s+(?:one\s+(?:would|might)\s+expect|expect)"
    r"|tend\s+to\s+(?:deviate|exceed|land|fall|sit|align|differ|vary)"
    r"|deviate\s+from\s+typical"
    r"|expected\s+patterns?\b"
    # Abstract "% of pattern range" — succession block already gives dollar band.
    r"|\d+(?:\.\d+)?\s*%\s+of\s+(?:the\s+|this\s+)?(?:pattern'?s?|entire|full)\s+(?:full\s+)?(?:price\s+)?range"
    r")\b",
    re.IGNORECASE,
)


def _has_procedural_recitation(text: str) -> bool:
    return bool(_PROCEDURAL_RECITATION_RE.search(text))


# Conjunction/adverb openers signalling a fragment. False positives acceptable — SOFT.
_FRAGMENT_OPENERS_RE = re.compile(
    r"^\s*(?:"
    r"And|But|Or|With|Meaning|Which|That"
    r"|Approximately|Roughly|About|Around"
    r")\s+(?:[a-z]|\d)",
    re.IGNORECASE,
)


def _is_sentence_fragment(text: str) -> bool:
    return bool(_FRAGMENT_OPENERS_RE.match(text))


def _has_meta_system(text: str) -> bool:
    return bool(_META_SYSTEM_RE.search(text))


def gate_narration_draft(
    draft: NarrationDraft | None,
    *,
    allowed_pages: Iterable[int],
    layer1_fallback: str,
    min_chars: int = _MIN_NARRATION_CHARS,
) -> tuple[str, CitationReport, bool]:
    # min_chars override: Q&A answers a single question, so its floor is lower
    # than the 2-3 paragraph narration modes default to.
    allowed_set = frozenset(allowed_pages)

    # malformed_json ≠ too_short — long answer can fail structured-output parsing.
    if draft is None:
        return (
            layer1_fallback,
            CitationReport(allowed_pages=allowed_set, malformed_json=True),
            True,
        )

    cited: set[int] = set()
    unsourced: list[str] = []
    raw_identifier: list[str] = []
    arithmetic: list[str] = []
    prose_page: list[str] = []
    meta_system: list[str] = []
    procedural: list[str] = []
    fragments: list[str] = []
    for c in draft.all_claims:
        if _RAW_IDENTIFIER_RE.search(c.text):
            raw_identifier.append(c.text)
        if _is_arithmetic_chain(c.text):
            arithmetic.append(c.text)
        if _PROSE_PAGE_RE.search(c.text):
            prose_page.append(c.text)
        if _has_meta_system(c.text):
            meta_system.append(c.text)
        if _has_procedural_recitation(c.text):
            procedural.append(c.text)
        if _is_sentence_fragment(c.text):
            fragments.append(c.text)
        if c.type != "theory_claim":
            continue
        if not c.pages:
            unsourced.append(c.text)
        else:
            cited.update(c.pages)

    rendered = render_narration(draft)
    report = CitationReport(
        cited_pages=cited,
        allowed_pages=allowed_set,
        unsourced_claims=tuple(unsourced),
        raw_identifier_claims=tuple(raw_identifier),
        arithmetic_chain_claims=tuple(arithmetic),
        prose_page_claims=tuple(prose_page),
        meta_system_claims=tuple(meta_system),
        procedural_recitation_claims=tuple(procedural),
        fragment_claims=tuple(fragments),
        too_short=len(rendered.strip()) < min_chars,
    )
    if report.ok:
        return rendered, report, False
    return layer1_fallback, report, True
