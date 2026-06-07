// Scores are 0..1 but sit low because final = min(structural, visual) *
// commitment, so the tier bands below are deliberately not even thirds.

import type { ConfidenceTier, ConfidenceTierInfo } from "./types";

export function confidenceTier(score: number): ConfidenceTierInfo {
  if (score >= 0.5) return { key: "high", word: "Strong" };
  if (score >= 0.25) return { key: "mid", word: "Moderate" };
  return { key: "low", word: "Low" };
}

export const TIER_FG: Record<ConfidenceTier, string> = {
  low: "var(--color-down)",
  mid: "var(--color-warn)",
  high: "var(--color-up)",
};
