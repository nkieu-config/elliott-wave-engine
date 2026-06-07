// Parse an SSE stream from a fetch Response body. Not EventSource (GET-only); we
// POST so the prompt/config goes in the body. Malformed frames are dropped.
export interface SSEMessage {
  event: string;
  data: string;
}

export async function* parseSSE(
  response: Response,
  signal?: AbortSignal,
): AsyncGenerator<SSEMessage> {
  if (!response.body) throw new Error("SSE: response has no body");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  try {
    while (true) {
      if (signal?.aborted) return;
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });

      // Normalise CRLF (some proxies rewrite line endings) so the parser
      // stays single-newline; frames are separated by a blank line.
      buf = buf.replace(/\r\n/g, "\n");

      let sepIdx: number;
      while ((sepIdx = buf.indexOf("\n\n")) !== -1) {
        const raw = buf.slice(0, sepIdx);
        buf = buf.slice(sepIdx + 2);
        const msg = parseSSEMessage(raw);
        if (msg) yield msg;
      }
    }
    // Flush trailing multi-byte UTF-8 from the streaming decoder.
    buf += decoder.decode();
    if (buf.trim()) {
      const msg = parseSSEMessage(buf);
      if (msg) yield msg;
    }
  } finally {
    // Cancel the body before releasing — a consumer that breaks early (done /
    // error / abort) otherwise leaves the connection draining, and releaseLock()
    // on a still-flowing stream can throw.
    try {
      await reader.cancel();
    } catch {
      /* already closed */
    }
    reader.releaseLock();
  }
}

function parseSSEMessage(raw: string): SSEMessage | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of raw.split("\n")) {
    if (!line || line.startsWith(":")) continue; // empty / comment / keepalive
    const colon = line.indexOf(":");
    if (colon === -1) continue;
    const field = line.slice(0, colon);
    const value = line.slice(colon + 1).replace(/^ /, "");
    if (field === "event") event = value;
    else if (field === "data") dataLines.push(value);
  }
  if (dataLines.length === 0) return null;
  return { event, data: dataLines.join("\n") };
}
