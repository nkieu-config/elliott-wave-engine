export type DeltaDir = "up" | "down" | "flat";

// Intl owns the sign (signDisplay) — never hand-concatenate. Locale from the
// caller (useLocale); currency stays USD. Cached per locale; en-US fallback.
interface DeltaFormatters {
  signed: Intl.NumberFormat;
  signedUsd: Intl.NumberFormat;
  absUsd: Intl.NumberFormat;
}
const FORMATTER_CACHE = new Map<string, DeltaFormatters>();

function formattersFor(locale: string): DeltaFormatters {
  let f = FORMATTER_CACHE.get(locale);
  if (!f) {
    f = {
      signed: new Intl.NumberFormat(locale, {
        signDisplay: "exceptZero",
        maximumFractionDigits: 0,
      }),
      signedUsd: new Intl.NumberFormat(locale, {
        style: "currency",
        currency: "USD",
        signDisplay: "exceptZero",
        maximumFractionDigits: 0,
      }),
      absUsd: new Intl.NumberFormat(locale, {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0,
      }),
    };
    FORMATTER_CACHE.set(locale, f);
  }
  return f;
}

export interface DeltaMeta {
  dir: DeltaDir;
  /** chip text — always carries an Intl sign, never color-only. */
  text: string;
  /** empty when nothing to announce. */
  announce: string;
  /** number token — must not be auto-translated. */
  noTranslate: boolean;
}

export const FLAT: DeltaMeta = { dir: "flat", text: "—", announce: "", noTranslate: false };

// No baseline or unchanged value → flat resting state, no announce, so a
// refetch that changes nothing stays silent.
export function numDelta(
  label: string,
  cur: number,
  prev: number | null | undefined,
  opts: { currency?: boolean; unit?: string; locale?: string } = {},
): DeltaMeta {
  if (prev == null) return FLAT;
  const d = cur - prev;
  if (d === 0) return { dir: "flat", text: "0", announce: "", noTranslate: true };
  const dir: DeltaDir = d > 0 ? "up" : "down";
  const fmt = formattersFor(opts.locale ?? "en-US");
  const text = (opts.currency ? fmt.signedUsd : fmt.signed).format(d);
  const mag = opts.currency ? fmt.absUsd.format(Math.abs(d)) : String(Math.abs(d));
  const unit = opts.unit ? ` ${opts.unit}` : "";
  return { dir, text, announce: `${label} ${dir} ${mag}${unit}`, noTranslate: true };
}
