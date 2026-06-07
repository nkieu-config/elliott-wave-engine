// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import { copyToClipboard } from "./copy-to-clipboard";

// jsdom 29 doesn't define document.execCommand at all, so install a mock rather
// than spying on a missing property.
function stubExec(impl?: () => boolean) {
  const exec = vi.fn(impl);
  Object.defineProperty(document, "execCommand", {
    value: exec,
    configurable: true,
    writable: true,
  });
  return exec;
}

afterEach(() => vi.unstubAllGlobals());

describe("copyToClipboard", () => {
  it("uses navigator.clipboard when available (secure context)", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText } });
    const exec = stubExec();
    expect(await copyToClipboard("hi")).toBe(true);
    expect(writeText).toHaveBeenCalledWith("hi");
    expect(exec).not.toHaveBeenCalled();
  });

  it("falls back to execCommand when the clipboard write rejects", async () => {
    vi.stubGlobal("navigator", {
      clipboard: { writeText: vi.fn().mockRejectedValue(new Error("denied")) },
    });
    const exec = stubExec(() => true);
    expect(await copyToClipboard("hi")).toBe(true);
    expect(exec).toHaveBeenCalledWith("copy");
  });

  it("falls back to execCommand when clipboard is absent (LAN-IP dev URL)", async () => {
    vi.stubGlobal("navigator", {}); // no clipboard
    stubExec(() => true);
    expect(await copyToClipboard("hi")).toBe(true);
  });

  it("returns false when the execCommand fallback throws", async () => {
    vi.stubGlobal("navigator", {});
    stubExec(() => {
      throw new Error("nope");
    });
    expect(await copyToClipboard("hi")).toBe(false);
  });
});
