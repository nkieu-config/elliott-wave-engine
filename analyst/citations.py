from __future__ import annotations

import re

# Accepts (p.91), (p.91-96), p.91, pp.91-96, en-dash variant.
PAGE_CITATION_RE: re.Pattern[str] = re.compile(
    r"\bpp?\.\s?(\d+)(?:\s?[-–]\s?(\d+))?"
)

# Split on sentence-final punctuation OR line break (bullet lists lack `.`).
SENTENCE_SPLIT_RE: re.Pattern[str] = re.compile(r"(?<=[.!?])\s+|\n+")


def extract_pages(text: str) -> set[int]:
    pages: set[int] = set()
    for m in PAGE_CITATION_RE.finditer(text):
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else start
        for p in range(start, end + 1):
            pages.add(p)
    return pages
