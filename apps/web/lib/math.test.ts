import { describe, expect, it } from "vitest";
import { clamp, clamp01, easeOutCubic, lerp, orderedWindow, wrapIndex } from "./math";

describe("clamp / clamp01", () => {
  it("bounds to [lo, hi]", () => {
    expect(clamp(5, 0, 10)).toBe(5);
    expect(clamp(-1, 0, 10)).toBe(0);
    expect(clamp(99, 0, 10)).toBe(10);
  });
  it("clamp01 bounds to [0, 1]", () => {
    expect(clamp01(0.5)).toBe(0.5);
    expect(clamp01(-2)).toBe(0);
    expect(clamp01(2)).toBe(1);
  });
});

describe("lerp", () => {
  it("interpolates the endpoints and midpoint", () => {
    expect(lerp(10, 20, 0)).toBe(10);
    expect(lerp(10, 20, 1)).toBe(20);
    expect(lerp(10, 20, 0.5)).toBe(15);
  });
});

describe("easeOutCubic", () => {
  it("starts at 0, ends at 1, and eases out", () => {
    expect(easeOutCubic(0)).toBe(0);
    expect(easeOutCubic(1)).toBe(1);
    expect(easeOutCubic(0.5)).toBeCloseTo(0.875); // 1 - 0.5^3
  });
});

describe("wrapIndex", () => {
  it("cycles within [0, len) in both directions", () => {
    expect(wrapIndex(0, 1, 4)).toBe(1);
    expect(wrapIndex(3, 1, 4)).toBe(0); // wrap forward off the end
    expect(wrapIndex(0, -1, 4)).toBe(3); // wrap backward off the start
  });
});

describe("orderedWindow", () => {
  it("leaves an already-valid window unchanged", () => {
    expect(orderedWindow(0.382, 0.618)).toEqual([0.382, 0.618]);
  });
  it("nudges the pair apart when a drag inverts them", () => {
    const [lo, hi] = orderedWindow(0.7, 0.65);
    expect(lo).toBeLessThan(hi);
    expect(lo).toBeCloseTo(0.64); // min(0.7, 0.65 - 0.01)
  });
});
