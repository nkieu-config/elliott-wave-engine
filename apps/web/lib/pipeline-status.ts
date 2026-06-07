export type StatusKey = "ok" | "warn" | "err";

export interface PipelineStatus {
  status: StatusKey;
  label: string;
}

// Precedence: hard error → loading → load error → refetch → no count → ready.
export function derivePipelineStatus(q: {
  isError: boolean;
  isFetching: boolean;
  data: { load_error?: string | null; top_scenario?: unknown } | undefined;
}): PipelineStatus {
  if (q.isError) return { status: "err", label: "Error" };
  if (!q.data) return { status: "warn", label: "Loading…" };
  if (q.data.load_error) return { status: "err", label: "Error" };
  if (q.isFetching) return { status: "warn", label: "Updating…" };
  if (!q.data.top_scenario) return { status: "warn", label: "No count" };
  return { status: "ok", label: "Ready" };
}
