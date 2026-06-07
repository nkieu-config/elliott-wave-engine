import { describe, expect, it } from "vitest";
import { confidenceTier } from "./confidence";

describe("confidenceTier", () => {
  it("maps score to the Streamlit-parity tier bands", () => {
    expect(confidenceTier(0.6)).toEqual({ key: "high", word: "Strong" });
    expect(confidenceTier(0.5)).toEqual({ key: "high", word: "Strong" }); // inclusive
    expect(confidenceTier(0.3)).toEqual({ key: "mid", word: "Moderate" });
    expect(confidenceTier(0.25)).toEqual({ key: "mid", word: "Moderate" }); // inclusive
    expect(confidenceTier(0.1)).toEqual({ key: "low", word: "Low" });
    expect(confidenceTier(0)).toEqual({ key: "low", word: "Low" });
  });
});
