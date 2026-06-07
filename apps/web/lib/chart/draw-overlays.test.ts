import type { IChartApi, UTCTimestamp } from "lightweight-charts";
import { describe, expect, it, vi } from "vitest";
import { allLayersOff as layers, makePivot, makeScenario, makeWave } from "../test-support/waves";
import type { Bar, Pivot, Scenario, Segment, Wave } from "../types";
import { toUTC } from "./helpers";
import { OVERLAY_STYLE, drawOverlays } from "./draw-overlays";

// LineSeries is a runtime value; mock it so the node env doesn't pull the
// browser charting lib. Only an opaque token here.
vi.mock("lightweight-charts", () => ({ LineSeries: {} }));

interface Series {
  opts: Record<string, unknown>;
  data: { time: UTCTimestamp; value: number }[];
}

// Records every addSeries call so we can assert what drawOverlays computed
// without a real canvas.
function fakeChart() {
  const created: Series[] = [];
  const chart = {
    addSeries(_type: unknown, opts: Record<string, unknown>) {
      const s: Series = { opts, data: [] };
      created.push(s);
      return { setData: (d: Series["data"]) => (s.data = d) };
    },
  };
  return { chart: chart as unknown as IChartApi, created };
}

const piv = (time: string, price: number, kind: Pivot["kind"] = "low"): Pivot =>
  makePivot({ time, price, kind });
const bar = (time: string, close = 1): Bar => ({ time, open: close, high: close, low: close, close, volume: 0 });
const seg = (end: Pivot, start: Pivot = piv("2019-01-01T00:00:00", 0)): Segment => ({ start, end });

// Local defaults (span 10→12 over Jan→Feb) differ from the generic builder, so
// wrap makeWave rather than calling it bare.
const wv = (
  role: string,
  opts: Partial<{ start: Pivot; end: Pivot | null; segments: Segment[]; children: Wave[] }> = {},
): Wave =>
  makeWave(role, {
    span_start: opts.start ?? piv("2020-01-01T00:00:00", 10),
    span_end: opts.end !== undefined ? opts.end : piv("2020-02-01T00:00:00", 12),
    segments: opts.segments ?? [],
    children: opts.children ?? [],
  });

const scen = (root: Wave, over: Partial<Scenario> = {}): Scenario => makeScenario({ root, ...over });

const base = {
  bars: [] as Bar[],
  activePivots: [] as Pivot[],
  rawPivots: [] as Pivot[],
  selectedScenario: null as Scenario | null,
  compareScenario: null as Scenario | null,
  drillPath: [] as number[],
  layers: layers(),
};

describe("drawOverlays", () => {
  it("draws only the backbone zigzag when there's no scenario", () => {
    const { chart, created } = fakeChart();
    const r = drawOverlays(chart, {
      ...base,
      activePivots: [piv("2020-01-01T00:00:00", 10), piv("2020-02-01T00:00:00", 12)],
    });
    expect(created).toHaveLength(1);
    expect(created[0].opts).toBe(OVERLAY_STYLE.backbone); // dashed reference line
    expect(created[0].data).toEqual([
      { time: toUTC("2020-01-01T00:00:00"), value: 10 },
      { time: toUTC("2020-02-01T00:00:00"), value: 12 },
    ]);
    expect(r.overlays).toHaveLength(1);
    expect(r.subLegSeries).toEqual([]);
    expect(r.markers).toEqual([]);
  });

  it("skips the backbone when fewer than 2 active pivots", () => {
    const { chart, created } = fakeChart();
    drawOverlays(chart, { ...base, activePivots: [piv("2020-01-01T00:00:00", 10)] });
    expect(created).toHaveLength(0);
  });

  it("dedupes clustered raw pivots that share a timestamp", () => {
    const { chart, created } = fakeChart();
    drawOverlays(chart, {
      ...base,
      layers: layers({ raw_zigzag: true }),
      rawPivots: [
        piv("2020-01-01T00:00:00", 10),
        piv("2020-01-01T00:00:00", 11), // same time → must be dropped
        piv("2020-02-01T00:00:00", 12),
      ],
    });
    const raw = created.find((c) => c.opts === OVERLAY_STYLE.rawZigzag);
    expect(raw?.data).toHaveLength(2);
  });

  it("draws the root spine through leg endpoints + one marker per leg", () => {
    const { chart, created } = fakeChart();
    const root = wv("root", {
      children: [
        wv("anchor"),
        wv("s1", {
          start: piv("2020-01-01T00:00:00", 10),
          end: piv("2020-02-01T00:00:00", 20, "high"),
        }),
        wv("s2", {
          start: piv("2020-02-01T00:00:00", 20, "high"),
          end: piv("2020-03-01T00:00:00", 15),
        }),
      ],
    });
    const r = drawOverlays(chart, { ...base, selectedScenario: scen(root) });

    const spine = created.find((c) => c.opts === OVERLAY_STYLE.spine);
    expect(spine?.data).toEqual([
      { time: toUTC("2020-01-01T00:00:00"), value: 10 },
      { time: toUTC("2020-02-01T00:00:00"), value: 20 },
      { time: toUTC("2020-03-01T00:00:00"), value: 15 },
    ]);
    // s1 ends on a high → above/arrowDown; s2 ends on a low → below/arrowUp.
    expect(r.markers).toEqual([
      expect.objectContaining({ position: "aboveBar", shape: "arrowDown", text: "W1" }),
      expect.objectContaining({ position: "belowBar", shape: "arrowUp", text: "W2" }),
    ]);
  });

  it("flags a drillable leg's marker with ◆", () => {
    const { chart } = fakeChart();
    const s3 = wv("s3", {
      end: piv("2020-03-01T00:00:00", 30, "high"),
      children: [wv("s1"), wv("s2")], // legs with span_end → drillable
    });
    const root = wv("root", { children: [wv("s1"), s3] });
    const r = drawOverlays(chart, { ...base, selectedScenario: scen(root) });
    expect(r.markers.find((m) => m.text?.startsWith("W3"))?.text).toBe("W3 ◆");
  });

  it("draws + tracks dimmed sub-wave series under a leg, tagged by root role", () => {
    const { chart } = fakeChart();
    const sub1 = wv("s1", { segments: [seg(piv("2020-01-15T00:00:00", 11))] });
    const sub2 = wv("s2", { segments: [seg(piv("2020-01-20T00:00:00", 13))] });
    const s3 = wv("s3", {
      segments: [seg(piv("2020-03-01T00:00:00", 30))],
      children: [sub1, sub2],
    });
    const root = wv("root", { children: [s3] });
    const r = drawOverlays(chart, { ...base, selectedScenario: scen(root) });
    expect(r.subLegSeries).toHaveLength(2);
    expect(r.subLegSeries.every((e) => e.rootRole === "s3")).toBe(true);
  });

  it("draws compare markers as circles, distinct from the primary's arrows", () => {
    const { chart } = fakeChart();
    const primary = scen(wv("root", { children: [wv("s1")] }), { id: "A" });
    const compare = scen(
      wv("root", { children: [wv("s1", { end: piv("2020-02-01T00:00:00", 22, "high") })] }),
      { id: "B" },
    );
    const r = drawOverlays(chart, { ...base, selectedScenario: primary, compareScenario: compare });
    expect(r.markers.some((m) => m.shape === "circle")).toBe(true);
    expect(r.markers.some((m) => m.shape === "arrowUp" || m.shape === "arrowDown")).toBe(true);
  });

  it("skips the compare overlay when it is the same scenario as the primary", () => {
    const { chart } = fakeChart();
    const r = drawOverlays(chart, {
      ...base,
      selectedScenario: scen(wv("root", { children: [wv("s1")] }), { id: "same" }),
      compareScenario: scen(wv("root", { children: [wv("s1")] }), { id: "same" }),
    });
    expect(r.markers.some((m) => m.shape === "circle")).toBe(false);
  });

  it("extends the S2–S4 trendline to the last bar (5W only)", () => {
    const { chart, created } = fakeChart();
    const root = wv("root", {
      children: [
        wv("s1"),
        wv("s2", { end: piv("2020-01-01T00:00:00", 100) }),
        wv("s3"),
        wv("s4", { end: piv("2020-03-01T00:00:00", 120) }),
      ],
    });
    drawOverlays(chart, {
      ...base,
      selectedScenario: scen(root, { family: "5W_TREND" }),
      layers: layers({ trendline: true }),
      bars: [bar("2020-04-01T00:00:00")],
    });

    const t1 = toUTC("2020-01-01T00:00:00");
    const t2 = toUTC("2020-03-01T00:00:00");
    const tl = toUTC("2020-04-01T00:00:00");
    const expected = 120 + ((120 - 100) / (t2 - t1)) * (tl - t2);

    const trend = created.find((c) => c.opts === OVERLAY_STYLE.trendline);
    expect(trend?.data).toHaveLength(3);
    expect(trend?.data[2]).toEqual({ time: tl, value: expected });
  });

  it("traces the in-progress projection through open_subtree leaf endpoints", () => {
    const { chart, created } = fakeChart();
    const root = wv("root", {
      children: [wv("s1"), wv("s2", { end: piv("2020-02-01T00:00:00", 50) })],
    });
    const openSubtree = wv("s3", {
      children: [
        wv("a", { end: piv("2020-03-01T00:00:00", 60) }),
        wv("b", { end: piv("2020-04-01T00:00:00", 55) }),
      ],
    });
    drawOverlays(chart, {
      ...base,
      selectedScenario: scen(root, { is_complete: false, open_subtree: openSubtree }),
      layers: layers({ in_progress: true }),
      bars: [bar("2020-05-01T00:00:00")],
    });

    const proj = created.find((c) => c.opts === OVERLAY_STYLE.projection);
    expect(proj?.data).toEqual([
      { time: toUTC("2020-02-01T00:00:00"), value: 50 }, // last closed leg's end
      { time: toUTC("2020-03-01T00:00:00"), value: 60 }, // leaf a
      { time: toUTC("2020-04-01T00:00:00"), value: 55 }, // leaf b
    ]);
  });
});
