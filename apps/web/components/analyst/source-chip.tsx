// Page-grouped: repeat citations to one page collapse to one chip, cited
// sentences ride the tooltip. Shared by reading-pane + qa-panel.
export function SourceChip({ page, sentences }: { page: number; sentences: string[] }) {
  // aria-label spells out the p./×n glyphs (else SR reads bare punctuation).
  const count = sentences.length;
  return (
    <span
      title={sentences.join("\n\n")}
      aria-label={`Page ${page}, ${count} ${count === 1 ? "citation" : "citations"}`}
      className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded border border-border-hi bg-panel-elev/60 text-text-dim"
    >
      <span className="text-muted" aria-hidden="true">p.</span>
      <span className="text-accent-bright font-semibold" aria-hidden="true">{page}</span>
      {count > 1 && <span className="text-muted" aria-hidden="true">×{count}</span>}
    </span>
  );
}
