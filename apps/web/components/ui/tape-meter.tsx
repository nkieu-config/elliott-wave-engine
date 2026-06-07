import { type CSSVars } from "@/lib/ui";
import { type Tier } from "@/lib/score-components";

export type Tone = "primary" | "up" | "warn" | "down" | "muted";

// Score tiers reuse the tape's up/warn/down LED hues.
export const TIER_TONE: Record<Tier, Tone> = { low: "down", mid: "warn", high: "up" };

// `bare` drops the KPI tearsheet's top margin; `animate=false` skips the print
// reveal for long lists.
export function TapeMeter({
  tone = "primary",
  fill = 100,
  openFill,
  empty = false,
  bare = false,
  animate = true,
  ariaLabel,
}: {
  tone?: Tone;
  /** primary fill, 0–100. */
  fill?: number;
  /** second stacked segment starting where `fill` ends. */
  openFill?: number;
  empty?: boolean;
  bare?: boolean;
  animate?: boolean;
  /** when set the meter is meaningful (role="img"); else decorative. */
  ariaLabel?: string;
}) {
  if (empty) {
    return (
      <div className="ewl-tape" data-empty="true" data-bare={bare || undefined} aria-hidden="true" />
    );
  }
  const semantics = ariaLabel
    ? ({ role: "img", "aria-label": ariaLabel } as const)
    : ({ "aria-hidden": true } as const);
  return (
    <div
      className="ewl-tape"
      data-tone={tone === "muted" ? undefined : tone}
      data-bare={bare || undefined}
      data-animate={animate ? undefined : "false"}
      {...semantics}
    >
      <span className="ewl-tape-fill" style={{ "--fill": `${fill}%` } as CSSVars} />
      {openFill != null && (
        <span
          className="ewl-tape-fill2"
          style={{ "--start": `${fill}%`, "--fill2": `${openFill}%` } as CSSVars}
        />
      )}
    </div>
  );
}
