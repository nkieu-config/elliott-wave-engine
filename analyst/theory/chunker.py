from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

PAGE_HEADER_RE = re.compile(r"^##\s+Page\s+(\d+)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Chunk:
    page: int
    body: str


def chunk_theory_file(path: Path | str) -> list[Chunk]:
    text = Path(path).read_text(encoding="utf-8")
    matches = list(PAGE_HEADER_RE.finditer(text))
    chunks: list[Chunk] = []
    for i, m in enumerate(matches):
        page = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        # Strip trailing "---" page separator.
        if body.endswith("---"):
            body = body[: -len("---")].rstrip()
        chunks.append(Chunk(page=page, body=body))
    return chunks


# bge can't bridge EWL's coined Link-Wave codes to their English names, so a
# natural-language query ("Trend linkage") misses a code-only page (p64 jumped
# rank 16→2 once enriched). Leg codes (s1-s5) need no alias — the corpus already
# writes them beside "wave". Match the gate's boundary rule; +SE before +S.
_LINKWAVE_RE = re.compile(r"(?<![A-Za-z0-9_])\+(SE|S|T)(?![A-Za-z0-9_])")
_LINKWAVE_ALIAS: dict[str, str] = {
    "+SE": "Sideway-Expand linkage (also called Extend)",
    "+S": "Sideway linkage (Sideway Link-Wave)",
    "+T": "Trend linkage (Trend Link-Wave)",
}


def _alias_footer(body: str) -> str:
    found = {"+" + m.group(1) for m in _LINKWAVE_RE.finditer(body)}
    parts = [_LINKWAVE_ALIAS[c] for c in ("+SE", "+S", "+T") if c in found]
    return "Terminology: " + "; ".join(parts) + "." if parts else ""


def enrich_aliases(chunks: list[Chunk]) -> list[Chunk]:
    # Append Link-Wave code→name aliases so both forms embed together. Applied
    # at build time — keep it in sync between make_embeddings and the corpus test.
    out: list[Chunk] = []
    for c in chunks:
        footer = _alias_footer(c.body)
        out.append(Chunk(page=c.page, body=f"{c.body}\n\n{footer}") if footer else c)
    return out
