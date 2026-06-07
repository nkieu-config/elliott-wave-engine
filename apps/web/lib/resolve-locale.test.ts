import { describe, expect, it } from "vitest";
import { FALLBACK_LOCALE, gregorianLocale, resolveLocale } from "./resolve-locale";

describe("resolveLocale", () => {
  it("falls back when the header is missing", () => {
    expect(resolveLocale(null)).toBe(FALLBACK_LOCALE);
    expect(resolveLocale(undefined)).toBe(FALLBACK_LOCALE);
    expect(resolveLocale("")).toBe(FALLBACK_LOCALE);
  });

  it("picks the highest q-weighted tag", () => {
    expect(resolveLocale("fr;q=0.8,en-US;q=0.9")).toBe("en-US");
  });

  it("skips a malformed tag to the next valid one", () => {
    expect(resolveLocale("!!,th-TH")).toBe("th-TH");
  });

  it("ignores the wildcard and falls back", () => {
    expect(resolveLocale("*")).toBe(FALLBACK_LOCALE);
  });
});

describe("gregorianLocale", () => {
  it("appends the gregorian calendar when absent", () => {
    expect(gregorianLocale("th-TH")).toBe("th-TH-u-ca-gregory");
  });

  it("is idempotent when already gregorian", () => {
    expect(gregorianLocale("th-TH-u-ca-gregory")).toBe("th-TH-u-ca-gregory");
  });

  it("merges into an existing -u- block without producing a double block", () => {
    const out = gregorianLocale("th-TH-u-nu-thai");
    expect(out).toContain("ca-gregory");
    expect(out.match(/-u-/g)?.length).toBe(1); // exactly one valid -u- extension
  });

  it("leaves a malformed tag untouched", () => {
    expect(gregorianLocale("!!")).toBe("!!");
  });
});
