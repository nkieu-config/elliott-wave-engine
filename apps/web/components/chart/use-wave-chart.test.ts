// @vitest-environment jsdom
import { renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

// hoisted so the (hoisted) vi.mock factory below can reference these spies.
const { fitContent, setData } = vi.hoisted(() => ({ fitContent: vi.fn(), setData: vi.fn() }));

vi.mock("lightweight-charts", () => {
  const series = { setData, applyOptions: vi.fn() };
  const chart = {
    addSeries: vi.fn(() => series),
    priceScale: vi.fn(() => ({ applyOptions: vi.fn() })),
    timeScale: vi.fn(() => ({ fitContent })),
    remove: vi.fn(),
  };
  return {
    createChart: vi.fn(() => chart),
    CandlestickSeries: {},
    createSeriesMarkers: vi.fn(),
  };
});

import { useChartInstance } from "./use-wave-chart";
import type { Bar } from "@/lib/types";

const bar = (time: string, c = 100): Bar => ({
  time, open: c, high: c + 1, low: c - 1, close: c, volume: 0,
});
const windowA: Bar[] = [bar("2024-01-01"), bar("2024-01-08"), bar("2024-01-15")];
const windowB: Bar[] = [bar("2020-06-01", 50), bar("2020-06-08", 52)];

const render = (bars: Bar[]) => {
  const ref = { current: document.createElement("div") };
  return renderHook(({ b }) => useChartInstance(ref, "linear", b, "en-US"), {
    initialProps: { b: bars },
  });
};

afterEach(() => vi.clearAllMocks());

describe("useChartInstance fitContent", () => {
  it("fits the chart on initial data load", () => {
    render(windowA);
    expect(fitContent).toHaveBeenCalledTimes(1);
  });

  it("refits only when the data window changes, not on a same-window re-render", () => {
    const { rerender } = render(windowA);
    expect(fitContent).toHaveBeenCalledTimes(1);

    // Same window, new array ref (e.g. overlay update re-renders) → keep user's zoom.
    rerender({ b: [...windowA] });
    expect(fitContent).toHaveBeenCalledTimes(1);

    // Different window (ticker / period switch) → refit (the bug: this was skipped).
    rerender({ b: windowB });
    expect(fitContent).toHaveBeenCalledTimes(2);
  });
});
