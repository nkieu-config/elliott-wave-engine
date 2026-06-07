import { describe, expect, it } from "vitest";
import { resolveHero } from "./hero-state";
import type { SampleData } from "./types";

// Minimal healthy payload; each test overrides one field to trip a branch.
const ok = {
  load_error: null,
  bars: [{}],
  selected_anchor: {},
  report: { scenarios: [{}], diagnostic: null },
} as unknown as SampleData;

describe("resolveHero", () => {
  it("fetch error takes precedence over everything else", () => {
    const h = resolveHero(ok, new Error("boom"));
    expect(h).toMatchObject({ key: "fetch-error", tone: "danger", retry: true });
    expect(h?.body).toBe("boom");
  });

  it("returns null for absent data", () => {
    expect(resolveHero(undefined, null)).toBeNull();
  });

  it("surfaces load_error as a retryable danger banner", () => {
    const h = resolveHero({ ...ok, load_error: "disk full" } as unknown as SampleData, null);
    expect(h).toMatchObject({ key: "load-error", retry: true });
    expect(h?.body).toBe("disk full");
  });

  it("walks the progress ladder: no bars → no anchor", () => {
    expect(resolveHero({ ...ok, bars: [] } as unknown as SampleData, null)?.key).toBe("no-data");
    expect(
      resolveHero({ ...ok, selected_anchor: null } as unknown as SampleData, null)?.key,
    ).toBe("no-anchor");
  });

  it("no scenarios: trimmed suggested_action wins, else a generic hint", () => {
    const withHint = {
      ...ok,
      report: { scenarios: [], diagnostic: { suggested_action: "  widen pivots  " } },
    } as unknown as SampleData;
    expect(resolveHero(withHint, null)?.body).toBe("widen pivots");

    const noHint = {
      ...ok,
      report: { scenarios: [], diagnostic: null },
    } as unknown as SampleData;
    expect(resolveHero(noHint, null)?.body).toContain("Elliott rule set");
  });

  it("returns null when the data is healthy", () => {
    expect(resolveHero(ok, null)).toBeNull();
  });
});
