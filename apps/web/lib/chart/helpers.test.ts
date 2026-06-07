import type { UTCTimestamp } from "lightweight-charts";
import { describe, expect, it } from "vitest";
import { makePivot, makeSegment, makeWave } from "../test-support/waves";
import type { Wave } from "../types";
import { collectLeafWaves, dedupeByTime, fmtPrice, toUTC } from "./helpers";

describe("toUTC", () => {
  it("forces a tz-less datetime to UTC (not local) by appending Z", () => {
    // 2020-01-01T00:00:00Z = 1577836800s — pinned so a non-UTC CI runner can't drift it.
    expect(toUTC("2020-01-01T00:00:00")).toBe(1577836800);
    expect(toUTC("2020-01-01T00:00:00")).toBe(toUTC("2020-01-01T00:00:00Z"));
  });

  it("honours an explicit offset instead of appending Z", () => {
    expect(toUTC("2020-01-01T07:00:00+07:00")).toBe(toUTC("2020-01-01T00:00:00Z"));
  });
});

describe("dedupeByTime", () => {
  const p = (n: number) => ({ time: n as UTCTimestamp, value: n });

  it("drops consecutive duplicate timestamps (lightweight-charts rejects them)", () => {
    expect(dedupeByTime([p(1), p(1), p(2), p(2), p(2), p(3)]).map((x) => x.time)).toEqual([
      1, 2, 3,
    ]);
  });

  it("only collapses *adjacent* duplicates — a later repeat is kept", () => {
    expect(dedupeByTime([p(1), p(2), p(1)]).map((x) => x.time)).toEqual([1, 2, 1]);
  });

  it("passes through empty and singleton arrays", () => {
    expect(dedupeByTime([])).toEqual([]);
    expect(dedupeByTime([p(5)]).map((x) => x.time)).toEqual([5]);
  });
});

describe("fmtPrice", () => {
  it("uses 0 decimals + thousands separators at >= 1000", () => {
    expect(fmtPrice(1500)).toBe("1,500");
    expect(fmtPrice(2_000_000)).toBe("2,000,000");
    expect(fmtPrice(-1500)).toBe("-1,500");
  });

  it("uses up to 2 decimals in [1, 1000)", () => {
    expect(fmtPrice(42.5)).toBe("42.5");
    expect(fmtPrice(1)).toBe("1");
    expect(fmtPrice(999.99)).toBe("999.99");
  });

  it("uses up to 4 decimals below 1 (ratios / sub-dollar prices)", () => {
    expect(fmtPrice(0.1234)).toBe("0.1234");
    expect(fmtPrice(0.5)).toBe("0.5");
  });
});

describe("collectLeafWaves", () => {
  const piv = (price = 1) => makePivot({ price });
  const seg = () => makeSegment({ start: piv(1), end: piv(2) });
  // Drawable = non-anchor + span_end + at least one segment.
  const leaf = (role: string, children: Wave[] = []): Wave =>
    makeWave(role, { span_start: piv(1), span_end: piv(2), segments: [seg()], children });
  const bare = (role: string): Wave => ({ ...leaf(role), segments: [] });

  it("collects a lone drawable leaf", () => {
    expect(collectLeafWaves(leaf("s1")).map((n) => n.role)).toEqual(["s1"]);
  });

  it("collects the leaves, not their drawable parent", () => {
    const parent = leaf("s3", [leaf("s1"), leaf("s2")]);
    expect(collectLeafWaves(parent).map((n) => n.role)).toEqual(["s1", "s2"]);
  });

  it("treats a node whose only child is segment-less as the leaf, and skips anchors", () => {
    // s3's child has no segments → s3 has no *drawable* children → s3 is itself the leaf.
    expect(collectLeafWaves(leaf("s3", [bare("s1")])).map((n) => n.role)).toEqual(["s3"]);
    // anchor children are never collected.
    expect(
      collectLeafWaves(leaf("root", [leaf("anchor"), leaf("s1")])).map((n) => n.role),
    ).toEqual(["s1"]);
  });

  it("returns nothing for a non-drawable node (no segments)", () => {
    expect(collectLeafWaves(bare("s1"))).toEqual([]);
  });
});
