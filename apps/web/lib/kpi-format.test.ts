import { describe, expect, it } from "vitest";
import { FLAT, numDelta } from "./kpi-format";

describe("numDelta", () => {
  it("is the flat resting state when there is no baseline", () => {
    expect(numDelta("Confidence", 5, null)).toBe(FLAT);
    expect(numDelta("Confidence", 5, undefined)).toBe(FLAT);
  });

  it("is a silent flat '0' for an unchanged value (refetch that changed nothing)", () => {
    expect(numDelta("Confidence", 5, 5)).toMatchObject({
      dir: "flat",
      text: "0",
      announce: "",
    });
  });

  it("signs the delta and builds a screen-reader announce (plain + unit)", () => {
    const up = numDelta("Scenarios", 7, 5);
    expect(up.dir).toBe("up");
    expect(up.announce).toBe("Scenarios up 2");
    expect(up.text).toContain("2");

    const down = numDelta("Confidence", 3, 5, { unit: "points" });
    expect(down.dir).toBe("down");
    expect(down.announce).toBe("Confidence down 2 points");
  });

  it("formats currency deltas with $", () => {
    const d = numDelta("Next target", 110, 100, { currency: true });
    expect(d.dir).toBe("up");
    expect(d.announce).toBe("Next target up $10");
    expect(d.text).toContain("$10");
  });
});
