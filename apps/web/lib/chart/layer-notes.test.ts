import { describe, expect, it } from "vitest";
import { ALL_LAYERS_OFF as ALL_OFF, allLayersOff as on } from "../test-support/waves";
import type { ChartLayerKey } from "../chart-store";
import type { Layer1Result } from "../types";
import { inactiveNotes } from "./layer-notes";

const keys = (notes: { layer: ChartLayerKey }[]) => notes.map((n) => n.layer);
const l1 = (slot: string) =>
  ({ targets: {}, bottleneck: { slot_name: slot } }) as unknown as Layer1Result;

describe("inactiveNotes", () => {
  it("is empty when nothing is toggled on", () => {
    expect(inactiveNotes(ALL_OFF, false, "5W_TREND", null, false)).toEqual([]);
  });

  it("notes in_progress while drilled or when the scenario is complete, but not while active", () => {
    expect(keys(inactiveNotes(on({ in_progress: true }), false, "5W_TREND", null, true))).toEqual([
      "in_progress",
    ]);
    expect(keys(inactiveNotes(on({ in_progress: true }), true, "5W_TREND", null, false))).toEqual([
      "in_progress",
    ]);
    expect(inactiveNotes(on({ in_progress: true }), false, "5W_TREND", null, false)).toEqual([]);
  });

  it("notes the trendline only on non-5W families", () => {
    expect(keys(inactiveNotes(on({ trendline: true }), false, "3W", null, false))).toEqual([
      "trendline",
    ]);
    expect(inactiveNotes(on({ trendline: true }), false, "5W_TREND", null, false)).toEqual([]);
  });

  it("notes targets + invalidation when Layer-1 has no targets", () => {
    expect(
      keys(inactiveNotes(on({ fib_targets: true, invalidation: true }), false, "5W", null, false)),
    ).toEqual(["fib_targets", "invalidation"]);
  });

  it("notes bottleneck unless the slot is leg_smoothness", () => {
    expect(inactiveNotes(on({ bottleneck: true }), false, "5W", l1("leg_smoothness"), false)).toEqual([]);
    expect(keys(inactiveNotes(on({ bottleneck: true }), false, "5W", l1("speed_cluster"), false))).toEqual([
      "bottleneck",
    ]);
    expect(keys(inactiveNotes(on({ bottleneck: true }), false, "5W", null, false))).toEqual([
      "bottleneck",
    ]);
  });
});
