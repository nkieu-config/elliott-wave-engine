// Caller passes elapsed (now - timestamp) to keep this pure/testable.
export function formatAgo(elapsedMs: number): string {
  const ago = Math.max(0, Math.floor(elapsedMs / 1000));
  return ago < 60 ? `${ago}s ago` : `${Math.floor(ago / 60)}m ago`;
}
