"use client";

import { createParser, parseAsString, useQueryState } from "nuqs";
import { useCallback } from "react";
import { create } from "zustand";
import {
  LAYER_DEFAULTS,
  LAYER_KEYS,
  parseDrill,
  parseLayers,
  serializeDrill,
  serializeLayers,
  type ChartLayerKey,
} from "./chart-layers";

export type { ChartLayerKey };
export { LAYER_DEFAULTS, LAYER_KEYS };

// Imperative side-pane toggles registered by ResizableWorkspace so an
// out-of-subtree caller can reach them. No-op defaults keep a pre-mount/mobile
// invocation harmless.
interface PanelControlsState {
  toggleLeft: () => void;
  toggleRight: () => void;
  register: (c: { toggleLeft: () => void; toggleRight: () => void }) => void;
}

export const usePanelControls = create<PanelControlsState>((set) => ({
  toggleLeft: () => {},
  toggleRight: () => {},
  register: (c) => set(c),
}));

// ?layers=raw_zigzag,trendline so a shared link carries the chart config.
const layersParser = createParser({
  parse: parseLayers,
  serialize: serializeLayers,
  // Lets nuqs skip URL writes when state collapses back to default.
  eq: (a, b) => LAYER_KEYS.every((k) => a[k] === b[k]),
}).withDefault(LAYER_DEFAULTS).withOptions({ history: "replace" });

export function useLayers() {
  const [layers, setLayers] = useQueryState("layers", layersParser);
  const toggle = useCallback(
    (key: ChartLayerKey) => {
      void setLayers((prev) => ({ ...prev, [key]: !prev[key] }));
    },
    [setLayers],
  );
  const reset = useCallback(() => void setLayers(LAYER_DEFAULTS), [setLayers]);
  // Backs the reset Undo action in LayersBar.
  const restore = useCallback(
    (snapshot: Record<ChartLayerKey, boolean>) => void setLayers(snapshot),
    [setLayers],
  );
  return { layers, toggle, reset, restore };
}

// ?scenario=...; null = auto-pick top scorer (fallback in chart-shell.tsx).
const scenarioParser = parseAsString.withOptions({ history: "replace" });

export function useSelectedScenario() {
  return useQueryState("scenario", scenarioParser);
}

export function useCompareScenario() {
  return useQueryState("compare", scenarioParser);
}

// ?drill=2.0: indices into successive drawableLegs; empty = root. replace
// history so it doesn't spam back.
const drillParser = createParser({
  parse: parseDrill,
  serialize: serializeDrill,
  eq: (a, b) => a.length === b.length && a.every((x, i) => x === b[i]),
})
  .withDefault([])
  .withOptions({ history: "replace" });

export function useDrillPath() {
  return useQueryState("drill", drillParser);
}
