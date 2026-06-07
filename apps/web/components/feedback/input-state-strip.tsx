"use client";

import { Anchor, BarChart3, Waves } from "lucide-react";
import { toUTC } from "@/lib/chart/helpers";
import { useLocale } from "@/lib/locale";
import { gregorianLocale } from "@/lib/resolve-locale";
import type { SampleData } from "@/lib/types";

export function InputStateStrip({ data }: { data: SampleData | undefined }) {
  const locale = useLocale();
  if (!data || data.bars.length === 0) return null;

  const barCount = data.bars.length;
  const rawCount = data.raw_pivots.length;
  const activeCount = data.active_pivots.length;
  const anchor = data.selected_anchor;
  const anchorDate = anchor
    ? // toUTC + UTC tz to match the chart axis (local parse drifts a day).
      new Date(toUTC(anchor.time) * 1000).toLocaleDateString(gregorianLocale(locale), {
        year: "numeric",
        month: "short",
        day: "numeric",
        timeZone: "UTC",
      })
    : null;

  return (
    <div
      // Hidden on phones to give the chart back a row.
      className="hidden sm:flex items-center gap-3 px-5 py-1.5 border-b border-border bg-bg/40 text-[12px] ewl-num text-muted tracking-[0.04em] overflow-x-auto"
      role="status"
      aria-label="Pipeline input state"
    >
      <span className="flex items-center gap-1 shrink-0">
        <BarChart3 className="h-3 w-3 text-accent" aria-hidden="true" />
        <span className="text-text-dim">{barCount.toLocaleString(locale)}</span>
        <span>bars</span>
      </span>
      <span aria-hidden="true" className="text-faint">·</span>
      <span className="flex items-center gap-1 shrink-0">
        <Waves className="h-3 w-3 text-cyan" aria-hidden="true" />
        {rawCount === activeCount ? (
          <>
            <span className="text-text-dim">{activeCount}</span>
            <span>pivots</span>
          </>
        ) : (
          <>
            <span className="text-text-dim">{rawCount}</span>
            <span aria-hidden="true">→</span>
            <span className="text-text-dim">{activeCount}</span>
            <span>pivots</span>
          </>
        )}
      </span>
      {anchor && anchorDate && (
        <>
          <span aria-hidden="true" className="text-faint">·</span>
          <span className="flex items-center gap-1 shrink-0">
            <Anchor className="h-3 w-3 text-violet" aria-hidden="true" />
            <span className="text-text-dim">
              ${anchor.price.toLocaleString(locale, { maximumFractionDigits: 2 })}
            </span>
            <span>· {anchorDate}</span>
          </span>
        </>
      )}
    </div>
  );
}
