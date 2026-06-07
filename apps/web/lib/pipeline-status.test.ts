import { describe, expect, it } from "vitest";
import { derivePipelineStatus } from "./pipeline-status";

type Q = Parameters<typeof derivePipelineStatus>[0];
const q = (over: Partial<Q>): Q => ({
  isError: false,
  isFetching: false,
  data: { top_scenario: {} },
  ...over,
});

describe("derivePipelineStatus", () => {
  it("a hard error wins over everything", () => {
    expect(derivePipelineStatus(q({ isError: true }))).toEqual({ status: "err", label: "Error" });
  });

  it("no data yet → loading", () => {
    expect(derivePipelineStatus(q({ data: undefined }))).toEqual({
      status: "warn",
      label: "Loading…",
    });
  });

  it("a load_error in the payload → error", () => {
    expect(derivePipelineStatus(q({ data: { load_error: "x", top_scenario: {} } }))).toEqual({
      status: "err",
      label: "Error",
    });
  });

  it("background refetch over existing data → updating", () => {
    expect(derivePipelineStatus(q({ isFetching: true }))).toEqual({
      status: "warn",
      label: "Updating…",
    });
  });

  it("data but no top scenario → no count", () => {
    expect(derivePipelineStatus(q({ data: { top_scenario: null } }))).toEqual({
      status: "warn",
      label: "No count",
    });
  });

  it("healthy → ok / Ready", () => {
    expect(derivePipelineStatus(q({}))).toEqual({ status: "ok", label: "Ready" });
  });
});
