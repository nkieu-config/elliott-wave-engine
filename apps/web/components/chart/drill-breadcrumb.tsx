"use client";

import { ChevronRight, CornerUpLeft } from "lucide-react";
import { cn } from "@/lib/cn";
import { buildDrillCrumbs } from "@/lib/scenario-format";
import type { Scenario } from "@/lib/types";

// Intermediate crumbs navigate up, trailing crumb is current scope. null at root.
export function DrillBreadcrumb({
  scenario,
  path,
  onNavigate,
  onReset,
}: {
  scenario: Scenario;
  /** Indices into successive `drawableLegs`. */
  path: number[];
  onNavigate: (path: number[]) => void;
  onReset: () => void;
}) {
  if (path.length === 0) return null;

  const crumbs = buildDrillCrumbs(scenario, path);

  return (
    <div
      className="flex items-center gap-1 px-5 py-1.5 border-b border-border bg-accent-soft/40 text-[12px] ewl-num overflow-x-auto"
      role="navigation"
      aria-label="Drilled wave path"
    >
      <span className="uppercase tracking-[0.14em] font-semibold text-accent-bright mr-1 shrink-0">
        Drilled
      </span>
      {crumbs.map((c, i) => {
        const isLast = i === crumbs.length - 1;
        return (
          <span key={i} className="flex items-center gap-1 shrink-0">
            {i > 0 && (
              <ChevronRight className="h-3 w-3 text-faint" aria-hidden="true" />
            )}
            {isLast ? (
              <span
                aria-current="location"
                className="px-1.5 py-0.5 rounded font-semibold uppercase tracking-[0.1em] bg-accent/20 text-accent-bright"
              >
                {c.label}
              </span>
            ) : (
              <button
                type="button"
                onClick={() => onNavigate(c.path)}
                className={cn(
                  "px-1.5 py-0.5 rounded uppercase tracking-[0.1em] font-medium text-text-dim transition-colors",
                  "hover:bg-panel-elev hover:text-text",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                )}
                title={`Back to ${c.label}`}
              >
                {c.label}
              </button>
            )}
          </span>
        );
      })}
      <button
        type="button"
        onClick={onReset}
        aria-label="Exit drill — back to the full scenario"
        title="Exit drill"
        className={cn(
          "ml-2 shrink-0 inline-flex items-center gap-1 px-1.5 py-0.5 rounded uppercase tracking-[0.14em] font-medium transition-colors",
          "text-muted hover:bg-panel-elev hover:text-text",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
        )}
      >
        <CornerUpLeft className="h-3 w-3" />
        Reset
      </button>
    </div>
  );
}
