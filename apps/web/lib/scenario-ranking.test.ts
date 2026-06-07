import { describe, expect, it } from "vitest";
import {
  byScoreDesc,
  medalMap,
  relativeStrengthPct,
  scoreRankMap,
} from "./scenario-ranking";
import type { Scenario } from "./types";

// Ranking fns only read id and score.
function sc(id: string, score: number): Scenario {
  return { id, score } as unknown as Scenario;
}

// Laid out ascending so the ranking fns must sort, not trust input order.
function makeShuffled(n: number): Scenario[] {
  return Array.from({ length: n }, (_, i) => sc(`s${n - i}`, (i + 1) / 100));
}

describe("byScoreDesc", () => {
  it("sorts by score descending without mutating input", () => {
    const input = [sc("a", 0.1), sc("b", 0.3), sc("c", 0.2)];
    const out = byScoreDesc(input);
    expect(out.map((s) => s.id)).toEqual(["b", "c", "a"]);
    expect(input.map((s) => s.id)).toEqual(["a", "b", "c"]); // unmutated
  });
});

describe("scoreRankMap & medalMap", () => {
  const scenarios = makeShuffled(8);

  it("assigns 1-based rank by score regardless of input order", () => {
    const ranks = scoreRankMap(scenarios);
    expect(ranks.get("s1")).toBe(1);
    expect(ranks.get("s2")).toBe(2);
    expect(ranks.get("s8")).toBe(8);
  });

  it("awards medals to the top 3 only", () => {
    const medals = medalMap(scenarios);
    expect(medals.get("s1")).toBe(1);
    expect(medals.get("s2")).toBe(2);
    expect(medals.get("s3")).toBe(3);
    expect(medals.has("s4")).toBe(false);
  });
});

describe("relativeStrengthPct", () => {
  it("is 100% at the top and scales linearly below it", () => {
    expect(relativeStrengthPct(0.4, 0.4)).toBe(100);
    expect(relativeStrengthPct(0.2, 0.4)).toBe(50);
    expect(relativeStrengthPct(0.1, 0.4)).toBe(25);
  });

  it("guards a non-positive top (no divide-by-zero)", () => {
    expect(relativeStrengthPct(0.3, 0)).toBe(0);
    expect(relativeStrengthPct(0.3, -1)).toBe(0);
  });

  it("clamps into [0, 100]", () => {
    expect(relativeStrengthPct(0.6, 0.4)).toBe(100); // score above the top → clamp
    expect(relativeStrengthPct(-0.1, 0.4)).toBe(0);
  });
});
