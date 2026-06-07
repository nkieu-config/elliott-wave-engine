// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { createElement, type ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchPipeline } from "./api";
import { usePipeline } from "./query";
import type { Layer1Result, SampleData } from "./types";

vi.mock("./api", () => ({
  fetchPipeline: vi.fn(),
  fetchLayer1: vi.fn(),
  fetchEducation: vi.fn(),
}));
const mockFetch = vi.mocked(fetchPipeline);

afterEach(() => vi.clearAllMocks());

function makeWrapper(qc: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return createElement(QueryClientProvider, { client: qc }, children);
  };
}
const freshClient = () =>
  new QueryClient({ defaultOptions: { queries: { retry: false } } });

describe("usePipeline cache warming", () => {
  it("seeds the layer-1 cache from the embedded top-scenario payload", async () => {
    const embedded = { targets: null } as unknown as Layer1Result;
    mockFetch.mockResolvedValue({
      top_scenario: { id: "t" },
      top_scenario_layer1: embedded,
    } as unknown as SampleData);

    const qc = freshClient();
    const config = { symbol: "X" };
    const { result } = renderHook(() => usePipeline(config), {
      wrapper: makeWrapper(qc),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    await waitFor(() =>
      expect(qc.getQueryData(["layer1", config, "t"])).toEqual(embedded),
    );
  });

  it("does not seed the cache when there's no embedded payload", async () => {
    mockFetch.mockResolvedValue({
      top_scenario: { id: "t" },
      top_scenario_layer1: null,
    } as unknown as SampleData);

    const qc = freshClient();
    const config = { symbol: "Y" };
    const { result } = renderHook(() => usePipeline(config), {
      wrapper: makeWrapper(qc),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(qc.getQueryData(["layer1", config, "t"])).toBeUndefined();
  });
});
