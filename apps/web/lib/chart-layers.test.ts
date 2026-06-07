import { describe, expect, it } from "vitest";
import { parseDrill, parseLayers, serializeDrill, serializeLayers } from "./chart-layers";

describe("parseLayers / serializeLayers", () => {
  it("parses a comma list into a full boolean record", () => {
    const r = parseLayers("raw_zigzag,trendline");
    expect(r.raw_zigzag).toBe(true);
    expect(r.trendline).toBe(true);
    expect(r.in_progress).toBe(false);
  });

  it("drops unknown keys so a stale shared link can't inject junk", () => {
    const r = parseLayers("trendline,bogus,latest");
    expect(r.trendline).toBe(true);
    expect(r.latest).toBe(true);
    expect((r as Record<string, boolean>).bogus).toBeUndefined();
  });

  it("round-trips through serialize (in canonical key order)", () => {
    expect(serializeLayers(parseLayers("bottleneck,fib_targets"))).toBe(
      "fib_targets,bottleneck",
    );
  });
});

describe("parseDrill / serializeDrill", () => {
  it("parses dot-separated indices; empty → root", () => {
    expect(parseDrill("2.0.1")).toEqual([2, 0, 1]);
    expect(parseDrill("")).toEqual([]);
  });

  it("rejects malformed paths (non-integer / negative) → root", () => {
    expect(parseDrill("abc")).toEqual([]);
    expect(parseDrill("1.-2")).toEqual([]);
  });

  it("round-trips", () => {
    expect(serializeDrill([3, 1])).toBe("3.1");
  });
});
