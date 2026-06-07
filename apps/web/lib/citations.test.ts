import { describe, expect, it } from "vitest";
import { groupCitationsByPage } from "./citations";

describe("groupCitationsByPage", () => {
  it("collapses repeat pages, keeps sentence order, sorts pages ascending", () => {
    expect(
      groupCitationsByPage([
        { page: 17, claim_sentence: "a" },
        { page: 3, claim_sentence: "b" },
        { page: 17, claim_sentence: "c" },
      ]),
    ).toEqual([
      [3, ["b"]],
      [17, ["a", "c"]],
    ]);
  });

  it("returns an empty array for no citations", () => {
    expect(groupCitationsByPage([])).toEqual([]);
  });
});
