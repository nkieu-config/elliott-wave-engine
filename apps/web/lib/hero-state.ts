import type { SampleData } from "./types";

export type HeroTone = "danger" | "warn" | "info";

export interface HeroState {
  /** Stable key — sessionStorage dismiss + React key + icon lookup. */
  key: string;
  tone: HeroTone;
  title: string;
  body: string;
  retry: boolean;
}

// Precedence: fetch error → load error → no bars → no anchor → no scenarios.
// Null when nothing to flag. Icon-free so it stays node-testable.
export function resolveHero(
  data: SampleData | undefined,
  error: Error | null,
): HeroState | null {
  if (error) {
    return {
      key: "fetch-error",
      tone: "danger",
      title: "Couldn't fetch pipeline",
      body: error.message || "The server returned an error while preparing the analysis.",
      retry: true,
    };
  }
  if (!data) return null;
  if (data.load_error) {
    return {
      key: "load-error",
      tone: "danger",
      title: "Data load failed",
      body: data.load_error,
      retry: true,
    };
  }
  if (data.bars.length === 0) {
    return {
      key: "no-data",
      tone: "info",
      title: "No data loaded",
      body: "Pick a symbol the data provider can serve, or widen the lookback period.",
      retry: false,
    };
  }
  if (!data.selected_anchor) {
    return {
      key: "no-anchor",
      tone: "warn",
      title: "No anchor pivot found",
      body: "Lower the ATR multiplier or the min-bars filter in the sidebar to surface more pivots.",
      retry: false,
    };
  }
  if (!data.report?.scenarios?.length) {
    // Prefer the human `suggested_action` (death_reason is a machine code).
    const hint = data.report?.diagnostic?.suggested_action?.trim();
    return {
      key: "no-scenarios",
      tone: "warn",
      title: "Could not build a wave count",
      body:
        hint ||
        "The pivot sequence didn't satisfy any Elliott rule set. Adjust pivot detection or pull-depth window in the sidebar.",
      retry: false,
    };
  }
  return null;
}
