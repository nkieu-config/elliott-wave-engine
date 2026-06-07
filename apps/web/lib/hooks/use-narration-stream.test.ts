// @vitest-environment jsdom
import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { streamAnalyst } from "../api";
import { useNarrationStream } from "./use-narration-stream";

// Replace the network layer with a controllable async generator of SSE frames.
vi.mock("../api", () => ({ streamAnalyst: vi.fn() }));
const mockStream = vi.mocked(streamAnalyst);

type Frame = { event: string; data: string };
async function* streamOf(...frames: Frame[]): AsyncGenerator<Frame> {
  for (const f of frames) yield f;
}
// An async generator needs no `yield` to be a generator, so it can throw on
// first pull to model a stream that aborts before any frame.
async function* abortingStream(): AsyncGenerator<Frame> {
  throw Object.assign(new Error("aborted"), { name: "AbortError" });
}
const j = (o: unknown) => JSON.stringify(o);
const config = {} as Parameters<typeof useNarrationStream>[1];

afterEach(() => vi.clearAllMocks());

describe("useNarrationStream", () => {
  it("accumulates tokens and finishes on the done event", async () => {
    mockStream.mockReturnValue(
      streamOf(
        { event: "start", data: j({ model_id: "m1" }) },
        { event: "token", data: j({ text: "Hello " }) },
        { event: "token", data: j({ text: "world" }) },
        {
          event: "citations",
          data: j({
            citations: [{ page: 1, claim_sentence: "x" }],
            cached: true,
            fell_back: false,
            model_id: "m1",
          }),
        },
        { event: "done", data: "{}" },
      ),
    );

    const { result } = renderHook(() => useNarrationStream("sc-1", config));
    await act(async () => {
      await result.current.startMode("explanation");
    });

    const s = result.current.states.explanation;
    expect(s.status).toBe("done");
    expect(s.text).toBe("Hello world");
    expect(s.tokens).toBe(2);
    expect(s.modelId).toBe("m1");
    expect(s.cached).toBe(true);
    expect(s.citations).toHaveLength(1);
  });

  it("surfaces a server `error` event as error status", async () => {
    mockStream.mockReturnValue(
      streamOf(
        { event: "start", data: "{}" },
        { event: "error", data: j({ message: "boom" }) },
      ),
    );
    const { result } = renderHook(() => useNarrationStream("sc-1", config));
    await act(async () => {
      await result.current.startMode("outlook");
    });
    expect(result.current.states.outlook.status).toBe("error");
    expect(result.current.states.outlook.error).toBe("boom");
  });

  it("marks error (not done) when the stream ends without a done frame", async () => {
    // Server closed mid-narration: keep the partial text but flag the truncation.
    mockStream.mockReturnValue(streamOf({ event: "token", data: j({ text: "partial" }) }));
    const { result } = renderHook(() => useNarrationStream("sc-1", config));
    await act(async () => {
      await result.current.startMode("explanation");
    });
    expect(result.current.states.explanation.status).toBe("error");
    expect(result.current.states.explanation.text).toBe("partial");
  });

  it("marks the mode cancelled (not errored) when the stream aborts", async () => {
    mockStream.mockReturnValue(abortingStream());
    const { result } = renderHook(() => useNarrationStream("sc-1", config));
    await act(async () => {
      await result.current.startMode("risk");
    });
    expect(result.current.states.risk.status).toBe("cancelled");
  });

  it("is a no-op when there is no selected scenario", async () => {
    const { result } = renderHook(() => useNarrationStream(null, config));
    await act(async () => {
      await result.current.startMode("explanation");
    });
    expect(mockStream).not.toHaveBeenCalled();
    expect(result.current.states.explanation.status).toBe("idle");
  });

  it("resets every stream when the scenario id changes", async () => {
    mockStream.mockReturnValue(
      streamOf({ event: "token", data: j({ text: "hi" }) }, { event: "done", data: "{}" }),
    );
    const { result, rerender } = renderHook(
      ({ id }) => useNarrationStream(id, config),
      { initialProps: { id: "sc-1" as string | null } },
    );
    await act(async () => {
      await result.current.startMode("explanation");
    });
    expect(result.current.states.explanation.text).toBe("hi");

    await act(async () => {
      rerender({ id: "sc-2" });
    });
    expect(result.current.states.explanation.text).toBe("");
    expect(result.current.states.explanation.status).toBe("idle");
  });
});
