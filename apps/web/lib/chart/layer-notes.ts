import type { ChartLayerKey } from "../chart-store";
import type { Layer1Result } from "../types";

export interface InactiveNote {
  layer: ChartLayerKey;
  text: string;
}

// Explain when a toggled-on layer renders nothing, so it never reads as broken.
export function inactiveNotes(
  layers: Record<ChartLayerKey, boolean>,
  scenarioIsComplete: boolean | null,
  scenarioFamily: string | null,
  layer1: Layer1Result | null,
  drilled: boolean,
): InactiveNote[] {
  const notes: InactiveNote[] = [];
  if (layers.in_progress && drilled) {
    notes.push({
      layer: "in_progress",
      text: "In progress hidden while drilled into a sub-pattern — reset the drill to see the projection.",
    });
  } else if (layers.in_progress && scenarioIsComplete === true) {
    notes.push({
      layer: "in_progress",
      text: "In progress hidden — the selected scenario is complete, so there's nothing to project.",
    });
  }
  // The S2→S4 trendline is only meaningful on five-wave structures; other
  // families silently draw nothing.
  if (
    layers.trendline &&
    scenarioFamily !== null &&
    !scenarioFamily.startsWith("5W")
  ) {
    notes.push({
      layer: "trendline",
      text: "Trendline only drawn for 5-wave scenarios (W2→W4 line).",
    });
  }
  if (layers.fib_targets && (layer1 === null || layer1.targets === null)) {
    notes.push({
      layer: "fib_targets",
      text: "Targets unavailable — Layer-1 hasn't produced projection levels for this scenario.",
    });
  }
  if (layers.invalidation && (layer1 === null || layer1.targets === null)) {
    notes.push({
      layer: "invalidation",
      text: "Invalidation unavailable — Layer-1 has no boundary level for this scenario.",
    });
  }
  if (layers.bottleneck) {
    if (layer1 === null || layer1.bottleneck === null) {
      notes.push({
        layer: "bottleneck",
        text: "Bottleneck unavailable — no diagnostic for this scenario.",
      });
    } else if (layer1.bottleneck.slot_name !== "leg_smoothness") {
      // Only leg_smoothness maps onto a single leg span; other slots can't be
      // highlighted on the chart.
      notes.push({
        layer: "bottleneck",
        text: `Bottleneck is ${layer1.bottleneck.slot_name} — only leg_smoothness has a chart highlight.`,
      });
    }
  }
  return notes;
}
