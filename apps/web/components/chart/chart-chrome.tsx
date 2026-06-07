"use client";

import {
  ArrowLeftRight,
  Download,
  GitCompare,
  Layers as LayersIcon,
  Maximize2,
  X,
} from "lucide-react";
import { useState } from "react";
import { LEGEND_ROLES, ROLE_COLOR, type LegendRole } from "@/lib/chart/helpers";
import { roleShort } from "@/lib/scenario-format";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { Scenario } from "@/lib/types";

const TIME_RANGES: { id: string; label: string; months: number }[] = [
  { id: "1m", label: "1M", months: 1 },
  { id: "3m", label: "3M", months: 3 },
  { id: "6m", label: "6M", months: 6 },
  { id: "1y", label: "1Y", months: 12 },
];

// `compare` is already null'd by the parent when it matches the primary scenario.
export function ChartToolbar({
  compare,
  onClear,
  onSwap,
  onExport,
}: {
  compare: Scenario | null;
  onClear?: () => void;
  onSwap?: () => void;
  onExport: () => void;
}) {
  return (
    <div className="ewl-chart-topright">
      {compare && (
        <CompareBadge onClear={onClear} onSwap={onSwap} />
      )}
      <button
        type="button"
        onClick={onExport}
        aria-label="Export chart as PNG"
        title="Export as PNG"
        className="ewl-chart-action-btn"
      >
        <Download className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

function CompareBadge({
  onClear,
  onSwap,
}: {
  onClear?: () => void;
  onSwap?: () => void;
}) {
  // No family/score text — the right rail + chart overlay already identify it.
  return (
    <span className="ewl-chart-compare-badge">
      <GitCompare className="h-3 w-3" />
      {onSwap && (
        <button
          type="button"
          onClick={onSwap}
          aria-label="Swap compare and primary scenario"
          title="Swap compare ↔ primary"
          className="ewl-chart-compare-icon-btn"
        >
          <ArrowLeftRight className="h-2.5 w-2.5" />
        </button>
      )}
      {onClear && (
        <button
          type="button"
          onClick={onClear}
          aria-label="Clear comparison"
          title="Clear comparison"
          className="ewl-chart-compare-icon-btn"
        >
          <X className="h-2.5 w-2.5" />
        </button>
      )}
    </span>
  );
}

export function ChartLegend({
  isolatedRole,
  hoveredRole,
  onIsolate,
  onHover,
}: {
  isolatedRole: LegendRole | null;
  hoveredRole: LegendRole | null;
  onIsolate: (r: LegendRole) => void;
  onHover: (r: LegendRole | null) => void;
}) {
  const [open, setOpen] = useState(false);
  const activeRole = isolatedRole ?? hoveredRole;

  return (
    <>
      <div className="ewl-chart-legend">
        <span
          className="ewl-chart-legend-item"
          data-static="true"
          title="Backbone — ZigZag through active pivots"
        >
          <span
            className="ewl-chart-legend-swatch"
            style={{
              background:
                "repeating-linear-gradient(90deg, rgba(148, 163, 184, 0.7) 0 3px, transparent 3px 6px)",
            }}
          />
          Backbone
        </span>
        {LEGEND_ROLES.map((role) => (
          <button
            key={role}
            type="button"
            className="ewl-chart-legend-item"
            data-isolated={isolatedRole === role}
            data-dimmed={activeRole != null && activeRole !== role}
            onClick={() => onIsolate(role)}
            onMouseEnter={() => onHover(role)}
            onMouseLeave={() => onHover(null)}
            aria-pressed={isolatedRole === role}
            title={`Isolate wave ${roleShort(role)}`}
          >
            <span
              className="ewl-chart-legend-swatch"
              style={{ background: ROLE_COLOR[role] }}
            />
            {roleShort(role)}
          </button>
        ))}
      </div>

      {/* Mobile (<lg) popover trigger — replaces the inline legend. */}
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <button
            type="button"
            aria-label="Toggle legend"
            title="Legend"
            className="ewl-chart-legend-mobile-trigger ewl-chart-action-btn"
          >
            <LayersIcon className="h-3.5 w-3.5" />
          </button>
        </PopoverTrigger>
        <PopoverContent side="top" aria-label="Legend" className="flex flex-col gap-0.5">
          {LEGEND_ROLES.map((role) => (
            <button
              key={role}
              type="button"
              className="ewl-chart-legend-item"
              data-isolated={isolatedRole === role}
              aria-pressed={isolatedRole === role}
              onClick={() => {
                onIsolate(role);
                setOpen(false);
              }}
            >
              <span
                className="ewl-chart-legend-swatch"
                style={{ background: ROLE_COLOR[role] }}
              />
              {roleShort(role)}
            </button>
          ))}
        </PopoverContent>
      </Popover>
    </>
  );
}

export function TimeChips({
  onPick,
  disabled,
}: {
  onPick: (months: number | "all") => void;
  disabled: boolean;
}) {
  return (
    <div className="ewl-chart-chips" role="group" aria-label="Time range presets">
      {TIME_RANGES.map((r, i) => (
        <span key={r.id} className="inline-flex items-center">
          <button
            type="button"
            onClick={() => onPick(r.months)}
            disabled={disabled}
            className="ewl-chart-chip"
            aria-label={`Show last ${r.label}`}
            title={`Show last ${r.label}`}
          >
            {r.label}
          </button>
          {i === TIME_RANGES.length - 1 && <span className="ewl-chart-chip-divider" />}
        </span>
      ))}
      <button
        type="button"
        onClick={() => onPick("all")}
        disabled={disabled}
        aria-label="Reset zoom (fit content)"
        title="Reset zoom"
        className="ewl-chart-chip"
      >
        <Maximize2 className="h-3 w-3" />
      </button>
    </div>
  );
}
