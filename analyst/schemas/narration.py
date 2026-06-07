from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal

from analyst.schemas.citation import CitationRef

# data_observation = Layer-1 number; theory_claim = EW rule (pages non-empty); disclosure = absence.
ClaimType = Literal["data_observation", "theory_claim", "disclosure"]
_CLAIM_TYPES: frozenset[str] = frozenset(
    {"data_observation", "theory_claim", "disclosure"}
)


@dataclass(frozen=True)
class Claim:
    text: str
    type: ClaimType
    pages: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class NarrationDraft:
    paragraphs: list[list[Claim]] = field(default_factory=list)

    @property
    def all_claims(self) -> list[Claim]:
        return [c for para in self.paragraphs for c in para]


def narration_json_schema(allowed_pages: Iterable[int]) -> dict:
    # `pages` constrained to allowed set → disallowed-page failures are impossible.
    page_enum = sorted(set(allowed_pages))
    if page_enum:
        pages_schema: dict = {"type": "array", "items": {"enum": page_enum}}
    else:
        pages_schema = {"type": "array", "maxItems": 0}
    return {
        "type": "object",
        "required": ["paragraphs"],
        "properties": {
            "paragraphs": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["text", "type"],
                        "properties": {
                            "text": {"type": "string"},
                            "type": {
                                "type": "string",
                                "enum": sorted(_CLAIM_TYPES),
                            },
                            "pages": pages_schema,
                        },
                    },
                },
            }
        },
    }


def parse_narration_draft(raw: str | None) -> NarrationDraft | None:
    # None on any malformation. Tolerates ```json fence (cloud models ignore `format`).
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    if text.startswith("```"):
        # Strip the ```lang opener without assuming a newline (single-line payloads).
        text = re.sub(r"^```[a-zA-Z0-9]*\s*", "", text)
        text = text.removesuffix("```").strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict) or not isinstance(obj.get("paragraphs"), list):
        return None

    paragraphs: list[list[Claim]] = []
    for para in obj["paragraphs"]:
        if not isinstance(para, list):
            return None
        claims: list[Claim] = []
        for c in para:
            if not isinstance(c, dict):
                return None
            ctype, body = c.get("type"), c.get("text")
            if ctype not in _CLAIM_TYPES or not isinstance(body, str):
                return None
            pages_raw = c.get("pages", [])
            if not isinstance(pages_raw, list):
                return None
            pages: list[int] = []
            for p in pages_raw:
                # bool is int subclass — reject so true/false don't coerce.
                if isinstance(p, bool) or not isinstance(p, int):
                    return None
                pages.append(p)
            claims.append(Claim(text=body.strip(), type=ctype, pages=pages))
        if claims:
            paragraphs.append(claims)
    return NarrationDraft(paragraphs=paragraphs) if paragraphs else None


def format_pages(pages: list[int]) -> str:
    # Contiguous → (p.99-100), else (p.99, p.103).
    ps = sorted(set(pages))
    if not ps:
        return ""
    if len(ps) >= 2 and ps == list(range(ps[0], ps[-1] + 1)):
        return f"(p.{ps[0]}-{ps[-1]})"
    return "(" + ", ".join(f"p.{p}" for p in ps) + ")"


def render_narration(draft: NarrationDraft) -> str:
    # Citation suffix appended deterministically; terminator goes AFTER the (p.N).
    out: list[str] = []
    for para in draft.paragraphs:
        sentences = []
        for c in para:
            s = c.text.strip()
            if c.type == "theory_claim" and c.pages:
                s = f"{s.rstrip('.!?').rstrip()} {format_pages(c.pages)}"
            if s and s[-1] not in ".!?":
                s += "."
            if s:
                s = s[0].upper() + s[1:]
            sentences.append(s)
        out.append(" ".join(sentences))
    return "\n\n".join(out)


def citations_from_draft(draft: NarrationDraft) -> tuple[CitationRef, ...]:
    return tuple(
        CitationRef(page=p, claim_sentence=c.text)
        for c in draft.all_claims
        if c.type == "theory_claim"
        for p in c.pages
    )
