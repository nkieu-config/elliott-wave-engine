import { describe, expect, it } from "vitest";
import {
  buildDrillCrumbs,
  drawableLegs,
  familyColor,
  findSelectedScenario,
  isDrillable,
  patternSubtype,
  prettyFamily,
  resolveScopeNode,
  roleShort,
  scopeLegs,
} from "./scenario-format";
import { makePivot, makeScenario, makeWave } from "./test-support/waves";
import type { SampleData, Scenario, Wave } from "./types";

const pivot = (price = 1) => makePivot({ price });

const wave = (role: string, children: Wave[] = [], hasEnd = true): Wave =>
  makeWave(role, { span_start: pivot(1), span_end: hasEnd ? pivot(2) : null, children });

const scenario = (root: Wave): Scenario => makeScenario({ id: "x", root });

describe("drawableLegs", () => {
  it("skips the anchor child and legs without a span_end", () => {
    const root = wave("root", [
      wave("anchor"),
      wave("s1"),
      wave("s2", [], /* hasEnd */ false),
      wave("s3"),
    ]);
    expect(drawableLegs(root).map((l) => l.role)).toEqual(["s1", "s3"]);
  });
});

describe("isDrillable", () => {
  it("is true only when a leg has its own drawable sub-legs", () => {
    expect(isDrillable(wave("s3", [wave("s1"), wave("s2")]))).toBe(true);
    expect(isDrillable(wave("s1"))).toBe(false);
    // children present but all undrawable (anchor / no end) → not drillable
    expect(isDrillable(wave("s1", [wave("anchor"), wave("s1", [], false)]))).toBe(false);
  });
});

describe("resolveScopeNode / scopeLegs", () => {
  const w3 = wave("s3", [wave("s1"), wave("s2"), wave("s3")]);
  const root = wave("root", [wave("anchor"), wave("s1"), wave("s2"), w3, wave("s4"), wave("s5")]);
  const sc = scenario(root);

  it("empty path resolves to the root and its drawable legs", () => {
    expect(resolveScopeNode(sc, [])).toBe(root);
    expect(scopeLegs(sc, []).map((l) => l.role)).toEqual(["s1", "s2", "s3", "s4", "s5"]);
  });

  it("a path indexes into successive drawableLegs (anchor not counted)", () => {
    // index 2 of drawable legs [s1,s2,s3,s4,s5] is W3 (the drillable one)
    expect(resolveScopeNode(sc, [2])).toBe(w3);
    expect(scopeLegs(sc, [2]).map((l) => l.role)).toEqual(["s1", "s2", "s3"]);
  });

  it("an out-of-range path does not resolve, and scopeLegs falls back to root", () => {
    expect(resolveScopeNode(sc, [99])).toBeNull();
    expect(scopeLegs(sc, [99]).map((l) => l.role)).toEqual(["s1", "s2", "s3", "s4", "s5"]);
  });
});

describe("display helpers", () => {
  it("prettyFamily replaces every underscore", () => {
    expect(prettyFamily("5W_TREND")).toBe("5W TREND");
    expect(prettyFamily("SOME_LONG_NAME")).toBe("SOME LONG NAME"); // not just the first
  });

  it("patternSubtype keeps only the part after the family separator", () => {
    expect(patternSubtype("5-Wave Sideway · Expand")).toBe("Expand");
    expect(patternSubtype("3-Wave · Normal")).toBe("Normal");
    expect(patternSubtype("3-Wave · Wave 2 longer + Wave 3 shorter")).toBe(
      "Wave 2 longer + Wave 3 shorter",
    );
    expect(patternSubtype(null)).toBe("");
    expect(patternSubtype("NoSeparator")).toBe("NoSeparator"); // defensive passthrough
  });

  it("roleShort maps parser roles to the W-convention", () => {
    expect(roleShort("s1")).toBe("W1");
    expect(roleShort("anchor")).toBe("ANCHOR");
    expect(roleShort("weird")).toBe("WEIRD"); // defensive uppercase fallback
  });

  it("familyColor returns a token, muted for unknown families", () => {
    expect(familyColor("5W_TREND")).toBe("var(--color-blue)");
    expect(familyColor("???")).toBe("var(--color-muted)");
  });
});

describe("buildDrillCrumbs", () => {
  const w3 = wave("s3", [wave("s1"), wave("s2"), wave("s3")]);
  const root = wave("root", [wave("anchor"), wave("s1"), wave("s2"), w3, wave("s4"), wave("s5")]);
  const sc = scenario(root);

  it("always starts with Root and walks the path", () => {
    const crumbs = buildDrillCrumbs(sc, [2]);
    expect(crumbs.map((c) => c.label)).toEqual(["Root", "W3"]);
    expect(crumbs[1].path).toEqual([2]);
  });

  it("returns just Root for an empty path", () => {
    expect(buildDrillCrumbs(sc, []).map((c) => c.label)).toEqual(["Root"]);
  });

  it("stops early at a stale / out-of-range index", () => {
    expect(buildDrillCrumbs(sc, [2, 99]).map((c) => c.label)).toEqual(["Root", "W3"]);
  });
});

describe("findSelectedScenario", () => {
  const sc = (id: string): Scenario => ({ ...scenario(wave("root")), id });
  const data = { report: { scenarios: [sc("a"), sc("b")] }, top_scenario: sc("a") } as SampleData;

  it("returns top_scenario when there is no report", () => {
    const noReport = { report: null, top_scenario: sc("t") } as SampleData;
    expect(findSelectedScenario(noReport, "x")?.id).toBe("t");
  });

  it("returns the id match when it still exists", () => {
    expect(findSelectedScenario(data, "b")?.id).toBe("b");
  });

  it("falls back to top_scenario for a missing id, and null for no data", () => {
    expect(findSelectedScenario(data, "missing")?.id).toBe("a");
    expect(findSelectedScenario(undefined, "x")).toBeNull();
  });
});
