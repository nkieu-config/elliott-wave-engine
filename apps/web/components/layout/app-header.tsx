"use client";

import { RefreshCw, Waves } from "lucide-react";
import Link from "next/link";
import { useQueryStates } from "nuqs";
import { useEffect, useState } from "react";
import { configParsers } from "@/lib/config";
import { usePipeline } from "@/lib/query";
import { useRefreshPipeline } from "@/lib/hooks/use-refresh-pipeline";
import { cn } from "@/lib/cn";
import { formatAgo } from "@/lib/format-time";
import { derivePipelineStatus, type StatusKey } from "@/lib/pipeline-status";

const STATUS_COLOR: Record<StatusKey, string> = {
  ok: "var(--color-up)",
  warn: "var(--color-warn)",
  err: "var(--color-down)",
};

// Plain span, not a heading: the page <h1> lives sr-only in page.tsx, so a
// heading here would duplicate it across brand copies.
export function BrandMark({ showText = true }: { showText?: boolean } = {}) {
  return (
    <Link
      href="/"
      className="ewl-topbar-brand-link"
      aria-label="Elliott Wave Lab — home"
    >
      <span className="ewl-topbar-mark" aria-hidden="true">
        <Waves className="h-4 w-4" />
      </span>
      {showText && <span className="ewl-topbar-title">EWL Lab</span>}
    </Link>
  );
}

export function BrandTear() {
  return (
    <Link href="/" className="ewl-cmd-brand-link" aria-label="Elliott Wave Lab — home">
      <span className="ewl-cmd-brand-mark" aria-hidden="true">
        <Waves className="h-3.5 w-3.5" />
      </span>
      {/* translate="no": "Lab" is a brand token, not a word to auto-translate. */}
      <span className="ewl-cmd-brand-word" translate="no">
        <span>EWL</span>
        <span className="tail">Lab</span>
      </span>
    </Link>
  );
}

type PipelineQuery = ReturnType<typeof usePipeline>;

function usePipelineStatus(): { status: StatusKey; label: string; query: PipelineQuery } {
  const [config] = useQueryStates(configParsers);
  const query = usePipeline(config);
  const { status, label } = derivePipelineStatus(query);
  return { status, label, query };
}

// `minimal` drops label/timestamp to just dot + refresh.
export function StatusPill({ minimal = false }: { minimal?: boolean } = {}) {
  const { status, label, query } = usePipelineStatus();
  const refreshPipeline = useRefreshPipeline();

  return (
    <div
      // shrink-0 in minimal mode so the scenario button absorbs the shrink and
      // can't squeeze refresh off the mobile toolbar's right edge.
      className={cn("ewl-topbar-status", minimal && "!min-w-0 gap-1 shrink-0")}
      role="status"
      aria-live="polite"
      aria-label={`Pipeline status: ${label}`}
    >
      {/* Refresh inside the pill — it acts on the status it shows. */}
      <button
        type="button"
        onClick={() => refreshPipeline()}
        disabled={query.isFetching}
        aria-label="Refresh data"
        title={query.isFetching ? "Already refreshing…" : "Refresh pipeline"}
        className="ewl-topbar-status-refresh"
      >
        <RefreshCw className={cn("h-3 w-3", query.isFetching && "animate-spin")} />
      </button>
      <span
        className="ewl-pulse-dot ewl-pulse"
        data-tone={status === "ok" ? undefined : status}
        aria-hidden="true"
      />
      {!minimal && (
        <>
          <span
            className="ewl-topbar-status-label"
            style={{ color: STATUS_COLOR[status] }}
          >
            {label}
          </span>
          <LastUpdated
            dataUpdatedAt={query.dataUpdatedAt}
            isFetching={query.isFetching}
          />
        </>
      )}
    </div>
  );
}

export function StatusReadout() {
  const { status, label, query } = usePipelineStatus();
  return (
    <div
      className="ewl-cmd-status"
      role="status"
      aria-live="polite"
      aria-label={`Pipeline status: ${label}`}
      title={statusTitle(label, query.dataUpdatedAt, query.isFetching)}
    >
      {/* aria-hidden — the dot+word already carry status to assistive tech. */}
      <span className="ewl-cmd-status-kicker" aria-hidden="true">
        Pipeline
      </span>
      <span className="ewl-cmd-status-row">
        <span
          className="ewl-pulse-dot ewl-pulse"
          data-tone={status === "ok" ? undefined : status}
          aria-hidden="true"
        />
        <span className="ewl-cmd-status-label" style={{ color: STATUS_COLOR[status] }}>
          {label}
        </span>
      </span>
    </div>
  );
}

function statusTitle(label: string, dataUpdatedAt: number, isFetching: boolean): string {
  if (!dataUpdatedAt || isFetching) return label;
  return `${label} · updated ${formatAgo(Date.now() - dataUpdatedAt)}`;
}

function LastUpdated({
  dataUpdatedAt,
  isFetching,
}: {
  dataUpdatedAt: number;
  isFetching: boolean;
}) {
  // Tick every 5s so "12s ago" advances; timer only starts once data exists.
  const [, setTick] = useState(0);

  useEffect(() => {
    if (!dataUpdatedAt) return;
    const id = setInterval(() => setTick((t) => t + 1), 5000);
    return () => clearInterval(id);
  }, [dataUpdatedAt]);

  // Slot rendered even when empty so pill width stays stable loading → ready.
  const showText = dataUpdatedAt && !isFetching;
  const text = showText ? formatAgo(Date.now() - dataUpdatedAt) : "";
  return (
    <span
      className="text-[10px] ewl-num text-faint tracking-[0.06em] ml-1 hidden lg:inline-block min-w-[58px]"
      aria-hidden={!showText}
    >
      {showText ? `· ${text}` : ""}
    </span>
  );
}
