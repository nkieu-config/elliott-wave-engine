// LLM emits prose with occasional **bold** and dash/number lists — a full
// markdown lib is overkill. Parsers tolerate partial text mid-stream.

export type Block =
  | { type: "p"; text: string }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[] };

export function parseBlocks(text: string): Block[] {
  return text
    .split(/\n{2,}/)
    .map((raw) => raw.trimEnd())
    .filter((raw) => raw.length > 0)
    .map((raw): Block => {
      const lines = raw.split("\n");
      const bullet = lines.length > 0 && lines.every((l) => /^\s*[-•*]\s+/.test(l));
      if (bullet) return { type: "ul", items: lines.map((l) => l.replace(/^\s*[-•*]\s+/, "")) };
      const numbered = lines.length > 0 && lines.every((l) => /^\s*\d+[.)]\s+/.test(l));
      if (numbered) return { type: "ol", items: lines.map((l) => l.replace(/^\s*\d+[.)]\s+/, "")) };
      return { type: "p", text: raw };
    });
}

export function splitInline(text: string): { bold: boolean; text: string }[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part) =>
    part.startsWith("**") && part.endsWith("**")
      ? { bold: true, text: part.slice(2, -2) }
      : { bold: false, text: part },
  );
}
