// Builders own the full SHAPE in one place, so adding a field to a domain type
// is a one-line change here rather than a sweep across every test.

import type { ChartLayerKey } from "../chart-store";
import type { Pivot, Scenario, Segment, Wave } from "../types";

export function makePivot(over: Partial<Pivot> = {}): Pivot {
  return { index: 0, time: "2020-01-01T00:00:00", price: 1, kind: "low", bar_index: 0, ...over };
}

export function makeSegment(over: Partial<Segment> = {}): Segment {
  return { start: makePivot({ price: 0 }), end: makePivot({ price: 1 }), ...over };
}

export function makeWave(role: string, over: Partial<Wave> = {}): Wave {
  return {
    role,
    pattern_kind: null,
    degree_label: null,
    span_start: makePivot({ price: 1 }),
    span_end: makePivot({ price: 2 }),
    nesting_level: 0,
    segments: [],
    children: [],
    sets: null,
    ...over,
  };
}

export function makeScenario(over: Partial<Scenario> = {}): Scenario {
  return {
    id: "primary",
    score: 0.3,
    score_components: {},
    family: "5W_TREND",
    family_label: "5-Wave Trend",
    pattern_kind: null,
    pattern_label: null,
    is_complete: false,
    depth: 1,
    confidence_tier: { key: "mid", word: "Moderate" },
    root: makeWave("root"),
    open_subtree: null,
    ...over,
  };
}

// All chart layers off — the neutral base for layer-visibility tests.
export const ALL_LAYERS_OFF: Record<ChartLayerKey, boolean> = {
  raw_zigzag: false,
  trendline: false,
  latest: false,
  in_progress: false,
  fib_targets: false,
  invalidation: false,
  bottleneck: false,
};

export const allLayersOff = (
  over: Partial<Record<ChartLayerKey, boolean>> = {},
): Record<ChartLayerKey, boolean> => ({ ...ALL_LAYERS_OFF, ...over });
