// No nuqs/zustand so it's node-testable and importable without React.

export type ChartLayerKey =
  | "raw_zigzag"
  | "trendline"
  | "latest"
  | "in_progress"
  | "fib_targets"
  | "invalidation"
  | "bottleneck";

export const LAYER_DEFAULTS: Record<ChartLayerKey, boolean> = {
  raw_zigzag: false,
  trendline: false,
  latest: true,
  in_progress: true,
  // Analyst overlays start hidden so the chart loads clean.
  fib_targets: false,
  invalidation: false,
  bottleneck: false,
};

export const LAYER_KEYS: ChartLayerKey[] = [
  "raw_zigzag",
  "trendline",
  "latest",
  "in_progress",
  "fib_targets",
  "invalidation",
  "bottleneck",
];

// Unknown keys dropped so a hand-edited / stale link can't inject junk.
export function parseLayers(raw: string): Record<ChartLayerKey, boolean> {
  const enabled = new Set(
    raw
      .split(",")
      .map((s) => s.trim())
      .filter((s): s is ChartLayerKey => LAYER_KEYS.includes(s as ChartLayerKey)),
  );
  return Object.fromEntries(LAYER_KEYS.map((k) => [k, enabled.has(k)])) as Record<
    ChartLayerKey,
    boolean
  >;
}

export function serializeLayers(v: Record<ChartLayerKey, boolean>): string {
  return LAYER_KEYS.filter((k) => v[k]).join(",");
}

// `?drill=2.0.1` → [2, 0, 1]. Rejects non-integer/negative (→ [] = root) so a
// malformed path never indexes into garbage.
export function parseDrill(raw: string): number[] {
  if (!raw) return [];
  const parts = raw.split(".").map((s) => Number.parseInt(s, 10));
  return parts.every((n) => Number.isInteger(n) && n >= 0) ? parts : [];
}

export function serializeDrill(v: number[]): string {
  return v.join(".");
}
