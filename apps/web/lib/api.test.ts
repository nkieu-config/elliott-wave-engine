import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { askQuestion, fetchEducation, fetchLayer1, fetchPipeline, streamAnalyst } from "./api";

// streamAnalyst's happy path uses a real Response so parseSSE runs end to end.

const okJson = (body: unknown): Response =>
  ({ ok: true, status: 200, json: async () => body, text: async () => "" }) as Response;

const errRes = (status: number, body: string, statusText = "Err"): Response =>
  ({
    ok: false,
    status,
    statusText,
    text: async () => body,
  }) as unknown as Response;

let fetchMock: ReturnType<typeof vi.fn>;
beforeEach(() => {
  fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
});
afterEach(() => vi.unstubAllGlobals());

function lastCall() {
  const [url, init] = fetchMock.mock.calls.at(-1) as [string, RequestInit];
  return { url, init };
}

describe("fetchPipeline", () => {
  it("POSTs the config as JSON and returns the parsed body", async () => {
    fetchMock.mockResolvedValue(okJson({ top_scenario: { id: "x" } }));
    const out = await fetchPipeline({ symbol: "DDOG", period: "max" });
    expect(out).toEqual({ top_scenario: { id: "x" } });

    const { url, init } = lastCall();
    expect(url).toContain("/api/v1/pipeline");
    expect(init.method).toBe("POST");
    expect(init.headers).toMatchObject({ "Content-Type": "application/json" });
    expect(JSON.parse(init.body as string)).toEqual({ symbol: "DDOG", period: "max" });
  });

  it("defaults to an empty config body", async () => {
    fetchMock.mockResolvedValue(okJson({}));
    await fetchPipeline();
    expect(JSON.parse(lastCall().init.body as string)).toEqual({});
  });

  it("throws status + body on a non-ok response", async () => {
    fetchMock.mockResolvedValue(errRes(500, "internal boom"));
    await expect(fetchPipeline()).rejects.toThrow("pipeline 500: internal boom");
  });

  it("falls back to statusText when the error body is empty", async () => {
    fetchMock.mockResolvedValue(errRes(502, "", "Bad Gateway"));
    await expect(fetchPipeline()).rejects.toThrow("pipeline 502: Bad Gateway");
  });

  it("tolerates a body that fails to read", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 503,
      statusText: "Unavailable",
      text: async () => {
        throw new Error("stream broke");
      },
    } as unknown as Response);
    await expect(fetchPipeline()).rejects.toThrow("pipeline 503: Unavailable");
  });
});

describe("fetchLayer1", () => {
  it("POSTs scenario_id with the config and returns the body", async () => {
    fetchMock.mockResolvedValue(okJson({ scenario_id: "sc-1" }));
    const out = await fetchLayer1({ scenario_id: "sc-1", symbol: "DDOG" });
    expect(out).toEqual({ scenario_id: "sc-1" });

    const { url, init } = lastCall();
    expect(url).toContain("/api/v1/scenario/layer1");
    expect(JSON.parse(init.body as string)).toEqual({ scenario_id: "sc-1", symbol: "DDOG" });
  });

  it("throws on a non-ok response", async () => {
    fetchMock.mockResolvedValue(errRes(404, "not found"));
    await expect(fetchLayer1({ scenario_id: "ghost" })).rejects.toThrow("layer1 404: not found");
  });
});

describe("fetchEducation", () => {
  it("GETs the url-encoded family and returns the body", async () => {
    fetchMock.mockResolvedValue(okJson({ family: "5W_TREND" }));
    const out = await fetchEducation("5W/TREND");
    expect(out).toEqual({ family: "5W_TREND" });

    const { url, init } = lastCall();
    expect(url).toContain("/api/v1/scenario/education?family=5W%2FTREND");
    // GET request — no explicit method, and it caches aggressively.
    expect(init.method).toBeUndefined();
    expect(init.cache).toBe("force-cache");
  });

  it("throws on a non-ok response", async () => {
    fetchMock.mockResolvedValue(errRes(404, "no entry"));
    await expect(fetchEducation("NOPE")).rejects.toThrow("education 404: no entry");
  });
});

describe("askQuestion", () => {
  it("POSTs the question + config and returns the parsed body", async () => {
    const body = { question: "q?", answer: "a (p.17).", citations: [], retrieved_pages: [17] };
    fetchMock.mockResolvedValue(okJson(body));
    const out = await askQuestion({ question: "q?", chart: { symbol: "DDOG", scenario_id: "s1" } });
    expect(out).toEqual(body);

    const { url, init } = lastCall();
    expect(url).toContain("/api/v1/qa");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({
      question: "q?",
      chart: { symbol: "DDOG", scenario_id: "s1" },
    });
  });

  it("maps a 503 (embedder off) to a thrown error", async () => {
    fetchMock.mockResolvedValue(errRes(503, "Q&A unavailable", "Unavailable"));
    await expect(askQuestion({ question: "q?" })).rejects.toThrow("qa 503: Q&A unavailable");
  });
});

describe("streamAnalyst", () => {
  it("yields parsed SSE frames on a 2xx stream", async () => {
    const sse =
      'event: start\ndata: {"model_id":"m1"}\n\n' +
      'event: token\ndata: {"text":"hi"}\n\n' +
      "event: done\ndata: {}\n\n";
    fetchMock.mockResolvedValue(new Response(sse, { status: 200 }));

    const frames = [];
    for await (const m of streamAnalyst({ scenario_id: "s", mode: "explanation" })) {
      frames.push(m);
    }
    expect(frames).toEqual([
      { event: "start", data: '{"model_id":"m1"}' },
      { event: "token", data: '{"text":"hi"}' },
      { event: "done", data: "{}" },
    ]);

    const { url, init } = lastCall();
    expect(url).toContain("/api/v1/analyst/stream");
    expect(init.method).toBe("POST");
    expect(init.headers).toMatchObject({ Accept: "text/event-stream" });
  });

  it("throws before the first frame on a non-ok response", async () => {
    fetchMock.mockResolvedValue(errRes(500, "model down", "Internal"));
    const gen = streamAnalyst({ scenario_id: "s", mode: "explanation" });
    await expect(gen.next()).rejects.toThrow("HTTP 500: model down");
  });
});
