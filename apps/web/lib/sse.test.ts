import { describe, expect, it } from "vitest";
import { parseSSE } from "./sse";

async function collect(text: string) {
  // `new Response(text)` exposes a ReadableStream body (undici, Node 18+).
  const out: { event: string; data: string }[] = [];
  for await (const msg of parseSSE(new Response(text))) out.push(msg);
  return out;
}

describe("parseSSE", () => {
  it("parses event + data frames separated by a blank line", async () => {
    const text = 'event: start\ndata: {"a":1}\n\nevent: token\ndata: hi\n\n';
    expect(await collect(text)).toEqual([
      { event: "start", data: '{"a":1}' },
      { event: "token", data: "hi" },
    ]);
  });

  it("defaults event to 'message', strips one leading space, ignores comments", async () => {
    expect(await collect(":keepalive\ndata: hello\n\n")).toEqual([
      { event: "message", data: "hello" },
    ]);
  });

  it("normalizes CRLF and flushes a trailing frame with no blank line", async () => {
    const text = "event: token\r\ndata: x\r\n\r\nevent: done\ndata: {}\n";
    expect(await collect(text)).toEqual([
      { event: "token", data: "x" },
      { event: "done", data: "{}" },
    ]);
  });

  it("joins multiple data: lines with a newline", async () => {
    expect(await collect("data: line1\ndata: line2\n\n")).toEqual([
      { event: "message", data: "line1\nline2" },
    ]);
  });

  it("yields nothing and tears down when the signal is already aborted", async () => {
    const ac = new AbortController();
    ac.abort();
    const out: { event: string; data: string }[] = [];
    for await (const m of parseSSE(new Response("event: token\ndata: x\n\n"), ac.signal)) {
      out.push(m);
    }
    expect(out).toEqual([]);
  });
});
