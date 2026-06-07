import { describe, expect, it } from "vitest";
import { buildErrorReport } from "./error-report";

describe("buildErrorReport", () => {
  it("composes a region + message + stack + URL + UA block", () => {
    const out = buildErrorReport(
      "Chart",
      { message: "boom", stack: "at foo()" },
      { href: "https://x/y", ua: "TestUA" },
    );
    expect(out).toBe(
      ["Chart error: boom", "", "at foo()", "", "URL: https://x/y", "UA: TestUA"].join("\n"),
    );
  });

  it("falls back to (no stack) when the error has none", () => {
    const out = buildErrorReport("App", { message: "x" }, { href: "h", ua: "u" });
    expect(out).toContain("(no stack)");
  });
});
