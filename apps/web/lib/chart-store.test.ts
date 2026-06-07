// @vitest-environment jsdom
import { act, renderHook } from "@testing-library/react";
import { withNuqsTestingAdapter } from "nuqs/adapters/testing";
import { afterEach, describe, expect, it } from "vitest";
import { LAYER_DEFAULTS } from "./chart-layers";
import {
  useCompareScenario,
  useDrillPath,
  useLayers,
  usePanelControls,
  useSelectedScenario,
} from "./chart-store";

// The nuqs-backed hooks read/write URL state, so they render under the testing
// adapter (which seeds searchParams). usePanelControls is a plain zustand store,
// exercised directly via its static getState/setState.

const adapter = (searchParams = "") => withNuqsTestingAdapter({ searchParams });

describe("useLayers", () => {
  it("starts from LAYER_DEFAULTS with no url state", () => {
    const { result } = renderHook(() => useLayers(), { wrapper: adapter() });
    expect(result.current.layers).toEqual(LAYER_DEFAULTS);
  });

  it("hydrates enabled layers from the ?layers param", () => {
    const { result } = renderHook(() => useLayers(), {
      wrapper: adapter("?layers=raw_zigzag,trendline"),
    });
    expect(result.current.layers.raw_zigzag).toBe(true);
    expect(result.current.layers.trendline).toBe(true);
    expect(result.current.layers.latest).toBe(false);
  });

  it("toggle flips a single key, leaving the rest intact", () => {
    const { result } = renderHook(() => useLayers(), { wrapper: adapter() });
    act(() => result.current.toggle("trendline"));
    expect(result.current.layers.trendline).toBe(true);
    expect(result.current.layers.latest).toBe(LAYER_DEFAULTS.latest);
  });

  it("reset returns to defaults after edits", () => {
    const { result } = renderHook(() => useLayers(), {
      wrapper: adapter("?layers=raw_zigzag"),
    });
    expect(result.current.layers.raw_zigzag).toBe(true);
    act(() => result.current.reset());
    expect(result.current.layers).toEqual(LAYER_DEFAULTS);
  });

  it("restore applies a full snapshot", () => {
    const { result } = renderHook(() => useLayers(), { wrapper: adapter() });
    const snapshot = { ...LAYER_DEFAULTS, fib_targets: true, invalidation: true };
    act(() => result.current.restore(snapshot));
    expect(result.current.layers).toEqual(snapshot);
  });
});

describe("scenario selection hooks", () => {
  it("useSelectedScenario reads ?scenario and defaults to null", () => {
    const seeded = renderHook(() => useSelectedScenario(), {
      wrapper: adapter("?scenario=abc"),
    });
    expect(seeded.result.current[0]).toBe("abc");

    const empty = renderHook(() => useSelectedScenario(), { wrapper: adapter() });
    expect(empty.result.current[0]).toBeNull();
  });

  it("useCompareScenario reads ?compare and defaults to null", () => {
    const seeded = renderHook(() => useCompareScenario(), {
      wrapper: adapter("?compare=xyz"),
    });
    expect(seeded.result.current[0]).toBe("xyz");

    const empty = renderHook(() => useCompareScenario(), { wrapper: adapter() });
    expect(empty.result.current[0]).toBeNull();
  });
});

describe("useDrillPath", () => {
  it("defaults to an empty path", () => {
    const { result } = renderHook(() => useDrillPath(), { wrapper: adapter() });
    expect(result.current[0]).toEqual([]);
  });

  it("parses a dotted ?drill path into indices", () => {
    const { result } = renderHook(() => useDrillPath(), { wrapper: adapter("?drill=2.0.1") });
    expect(result.current[0]).toEqual([2, 0, 1]);
  });
});

describe("usePanelControls", () => {
  afterEach(() => {
    usePanelControls.setState({ toggleLeft: () => {}, toggleRight: () => {} });
  });

  it("starts with harmless no-op toggles", () => {
    expect(() => {
      usePanelControls.getState().toggleLeft();
      usePanelControls.getState().toggleRight();
    }).not.toThrow();
  });

  it("register installs the real toggle handlers", () => {
    let left = 0;
    let right = 0;
    usePanelControls.getState().register({
      toggleLeft: () => (left += 1),
      toggleRight: () => (right += 1),
    });
    usePanelControls.getState().toggleLeft();
    usePanelControls.getState().toggleRight();
    expect(left).toBe(1);
    expect(right).toBe(1);
  });
});
