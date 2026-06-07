import type { CitationRef } from "./types";

// Collapse repeats of one page; sentences in order, pages sorted ascending.
export function groupCitationsByPage(citations: CitationRef[]): [number, string[]][] {
  const byPage = new Map<number, string[]>();
  for (const c of citations) {
    byPage.set(c.page, [...(byPage.get(c.page) ?? []), c.claim_sentence]);
  }
  return [...byPage.entries()].sort((a, b) => a[0] - b[0]);
}
