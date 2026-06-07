import { describe, expect, it } from "vitest";
import { formatAgo } from "./format-time";

describe("formatAgo", () => {
  it("shows seconds under a minute", () => {
    expect(formatAgo(0)).toBe("0s ago");
    expect(formatAgo(12_000)).toBe("12s ago");
    expect(formatAgo(59_000)).toBe("59s ago");
  });

  it("rolls over to minutes at 60s", () => {
    expect(formatAgo(60_000)).toBe("1m ago");
    expect(formatAgo(125_000)).toBe("2m ago");
  });

  it("floors a negative elapsed (clock skew) to 0s", () => {
    expect(formatAgo(-5_000)).toBe("0s ago");
  });
});
