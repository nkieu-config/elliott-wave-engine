import { describe, expect, it } from "vitest";
import { parseBlocks, splitInline } from "./narration-format";

describe("parseBlocks", () => {
  it("splits paragraphs on blank lines", () => {
    expect(parseBlocks("First para.\n\nSecond para.")).toEqual([
      { type: "p", text: "First para." },
      { type: "p", text: "Second para." },
    ]);
  });

  it("reads an all-bullet block as a ul and strips -, •, * markers", () => {
    expect(parseBlocks("- one\n- two\n• three")).toEqual([
      { type: "ul", items: ["one", "two", "three"] },
    ]);
  });

  it("reads an all-numbered block as an ol (1. and 1) both count)", () => {
    expect(parseBlocks("1. a\n2) b")).toEqual([{ type: "ol", items: ["a", "b"] }]);
  });

  it("falls back to a paragraph when the lines are mixed", () => {
    expect(parseBlocks("- bullet\nplain line")[0].type).toBe("p");
  });

  it("drops empty/whitespace chunks (tolerates partial streaming text)", () => {
    expect(parseBlocks("\n\n  \n\nreal")).toEqual([{ type: "p", text: "real" }]);
  });
});

describe("splitInline", () => {
  it("flags **bold** runs and leaves the rest plain", () => {
    expect(splitInline("a **b** c")).toEqual([
      { bold: false, text: "a " },
      { bold: true, text: "b" },
      { bold: false, text: " c" },
    ]);
  });

  it("returns a single plain run when there is no bold", () => {
    expect(splitInline("plain")).toEqual([{ bold: false, text: "plain" }]);
  });
});
