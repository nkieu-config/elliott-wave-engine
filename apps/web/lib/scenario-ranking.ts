// Invariant: leaderboard render order and ↑/↓ keyboard-nav order both source
// from here so they never drift apart.

import { clamp } from "./math";
import type { Scenario } from "./types";

export function byScoreDesc(scenarios: Scenario[]): Scenario[] {
  return [...scenarios].sort((a, b) => b.score - a.score);
}

export function maxScore(scenarios: Scenario[]): number {
  return scenarios.reduce((m, s) => Math.max(m, s.score), 0);
}

// Absolute 1-based rank by score, keyed by id (render-order independent).
export function scoreRankMap(scenarios: Scenario[]): Map<string, number> {
  const m = new Map<string, number>();
  byScoreDesc(scenarios).forEach((s, i) => m.set(s.id, i + 1));
  return m;
}

// Top-3 by raw score (score-absolute, so a floated pin doesn't get a medal).
export function medalMap(scenarios: Scenario[]): Map<string, 1 | 2 | 3> {
  const m = new Map<string, 1 | 2 | 3>();
  byScoreDesc(scenarios)
    .slice(0, 3)
    .forEach((s, i) => m.set(s.id, (i + 1) as 1 | 2 | 3));
  return m;
}

// Score as percent of top (best = 100%), clamped. 0 when no positive top
// (divide-by-zero guard). Single source for every "relative strength" figure.
export function relativeStrengthPct(score: number, topScore: number): number {
  if (topScore <= 0) return 0;
  return clamp(Math.round((score / topScore) * 100), 0, 100);
}
