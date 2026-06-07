import { describe, expect, it } from "vitest";
import { calibratedPct, resolveBottleneck, scoreTier } from "./score-components";
import type { Scenario } from "./types";

describe("scoreTier", () => {
  it("uses wider slot bands [0.4, 0.7]", () => {
    expect(scoreTier(0.39, { parent: false })).toBe("low");
    expect(scoreTier(0.55, { parent: false })).toBe("mid");
    expect(scoreTier(0.7, { parent: false })).toBe("high");
  });

  it("uses tighter parent bands [0.25, 0.5] (MIN aggregation compresses parents)", () => {
    expect(scoreTier(0.24, { parent: true })).toBe("low");
    expect(scoreTier(0.4, { parent: true })).toBe("mid");
    expect(scoreTier(0.5, { parent: true })).toBe("high");
  });
});

describe("calibratedPct", () => {
  it("clamps to 0..100 and is monotonic non-decreasing", () => {
    const slot = (v: number) => calibratedPct(v, { parent: false });
    expect(slot(-1)).toBe(0);
    expect(slot(2)).toBe(100);
    expect(slot(0.2)).toBeLessThan(slot(0.5));
    expect(slot(0.5)).toBeLessThan(slot(0.9));
  });

  it("maps the mid-band cutoff to ~35% and the high cutoff to ~70% fill", () => {
    expect(calibratedPct(0.4, { parent: false })).toBe(35);
    expect(calibratedPct(0.7, { parent: false })).toBe(70);
  });
});

describe("resolveBottleneck", () => {
  const scen = (components: Record<string, number>): Scenario =>
    ({ score: 0.3, score_components: components }) as unknown as Scenario;

  it("flags the weakest slot when quality drags (not progress)", () => {
    const r = resolveBottleneck(
      scen({
        total: 0.2,
        quality: 0.4,
        commitment: 0.9,
        speed_cluster: 0.8,
        fib_push_pairs: 0.3,
        pull_depth_discipline: 0.5,
      }),
    );
    expect(r.kind).toBe("slot");
    expect(r.slot?.key).toBe("fib_push_pairs"); // the weakest of the three
    expect(r.slots).toHaveLength(3);
  });

  it("flags progress when commitment is the lower factor", () => {
    const r = resolveBottleneck(
      scen({ total: 0.2, quality: 0.6, commitment: 0.3, speed_cluster: 0.6 }),
    );
    expect(r.kind).toBe("progress");
    expect(r.slot).toBeNull();
  });

  it("is 'none' with no slot components, and falls total back to scenario.score", () => {
    const r = resolveBottleneck(scen({}));
    expect(r.kind).toBe("none");
    expect(r.slots).toEqual([]);
    expect(r.total).toBe(0.3); // no total key → scenario.score
  });
});
