// Resolve a BCP-47 locale from Accept-Language so server and client format
// dates/numbers identically (no hydration drift). en-US fallback.
export const FALLBACK_LOCALE = "en-US";

export function resolveLocale(acceptLanguage: string | null | undefined): string {
  if (!acceptLanguage) return FALLBACK_LOCALE;
  // "en-US,en;q=0.9,fr;q=0.8" → tags sorted by descending q-weight.
  const tags = acceptLanguage
    .split(",")
    .map((part) => {
      const [tag, ...params] = part.trim().split(";");
      const q = params.map((p) => p.trim()).find((p) => p.startsWith("q="));
      const weight = q ? Number(q.slice(2)) : 1;
      return { tag: tag.trim(), weight: Number.isFinite(weight) ? weight : 0 };
    })
    .filter((t) => t.tag && t.tag !== "*")
    .sort((a, b) => b.weight - a.weight);

  for (const { tag } of tags) {
    try {
      const canonical = Intl.getCanonicalLocales(tag)[0];
      if (canonical) return canonical;
    } catch {
      // Malformed tag — skip to the next candidate.
    }
  }
  return FALLBACK_LOCALE;
}

// Pin Gregorian on date surfaces: a th-TH viewer gets Thai month names but
// Gregorian years (2026, not BE 2569). Numbers are calendar-agnostic.
export function gregorianLocale(locale: string): string {
  try {
    // Merges into any existing -u- block; string concat would double it (invalid).
    return new Intl.Locale(locale, { calendar: "gregory" }).toString();
  } catch {
    return locale; // malformed tag
  }
}
