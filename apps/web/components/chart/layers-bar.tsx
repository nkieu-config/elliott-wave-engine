"use client";

import {
  Activity,
  AlertTriangle,
  Check,
  Hourglass,
  Layers as LayersIcon,
  Link2,
  RotateCcw,
  Siren,
  Spline,
  Target as TargetIcon,
} from "lucide-react";
import { useState } from "react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { toast } from "sonner";
import {
  LAYER_DEFAULTS,
  LAYER_KEYS,
  type ChartLayerKey,
  useLayers,
} from "@/lib/chart-store";
import { inactiveNotes } from "@/lib/chart/layer-notes";
import { cn } from "@/lib/cn";
import type { Layer1Result, Scenario } from "@/lib/types";

interface LayerSpec {
  key: ChartLayerKey;
  label: string;
  tooltip: string;
  Icon: typeof Hourglass;
  /** Tucked behind the desktop "More" popover so the primary pill row stays one
   * line at 1280–1440 (6 pills wrapped). */
  debug?: boolean;
}

// `latest` has NO pill on purpose — it stays on at default (the "Latest" line
// is always drawn).
const LAYERS: LayerSpec[] = [
  {
    key: "in_progress",
    label: "In progress",
    tooltip: "Dashed extension showing where the still-forming leg currently reaches",
    Icon: Hourglass,
  },
  {
    key: "fib_targets",
    label: "Targets",
    tooltip: "Fibonacci projection levels for the next wave (cyan = confirmation, dim = flow)",
    Icon: TargetIcon,
  },
  {
    key: "invalidation",
    label: "Invalidation",
    tooltip: "Price where the current wave count is structurally wrong",
    Icon: AlertTriangle,
  },
  {
    key: "bottleneck",
    label: "Bottleneck",
    tooltip: "Highlight the leg dragging the confidence score down (leg_smoothness only)",
    Icon: Siren,
  },
  {
    key: "raw_zigzag",
    label: "Raw zigzag",
    tooltip: "Debug — raw ATR ZigZag polyline, every pivot before the min-bars spacing filter drops the clustered ones",
    Icon: Activity,
    debug: true,
  },
  {
    key: "trendline",
    label: "Trendline",
    tooltip: "Debug — W2→W4 channel trendline (drawn for 5-wave scenarios only)",
    Icon: Spline,
    debug: true,
  },
];

interface Props {
  scenario: Scenario | null;
  layer1: Layer1Result | null;
  drilled?: boolean;
}

function ResetLayersButton({ onReset }: { onReset: () => void }) {
  return (
    <button
      type="button"
      onClick={onReset}
      aria-label="Reset layers to default"
      title="Reset layers to default"
      className={cn(
        "ml-auto shrink-0 inline-flex items-center gap-1 h-7 px-2 rounded-md text-[12px] uppercase tracking-[0.14em] font-medium transition-colors font-mono",
        "text-accent-bright hover:bg-accent-soft",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
      )}
    >
      <RotateCcw className="h-3 w-3" />
      Reset
    </button>
  );
}

export function LayersBar({ scenario, layer1, drilled = false }: Props) {
  const { layers, toggle, reset, restore } = useLayers();
  const [open, setOpen] = useState(false);
  const activeCount = LAYERS.filter((l) => layers[l.key]).length;
  const notes = inactiveNotes(
    layers,
    scenario ? scenario.is_complete : null,
    scenario ? scenario.family : null,
    layer1,
    drilled,
  );

  const dirty = LAYER_KEYS.some((k) => layers[k] !== LAYER_DEFAULTS[k]);

  // Destructive (a user may have built a combo for screenshots) — offer Undo.
  const onReset = () => {
    const prev = { ...layers };
    reset();
    toast.success("Layers reset to default", {
      duration: 5000,
      action: {
        label: "Undo",
        onClick: () => restore(prev),
      },
    });
  };

  return (
    <div className="border-b border-border bg-panel/60 backdrop-blur-sm">
      {/* Reset is a separate top-aligned cell so a full pill row doesn't push
          it onto a lonely line. */}
      <div className="hidden lg:flex items-start gap-2 px-5 py-2.5">
        <div className="flex flex-wrap items-center gap-2 flex-1 min-w-0">
          <span
            className="flex items-center text-accent mr-0.5 shrink-0"
            aria-hidden="true"
          >
            <LayersIcon className="h-3.5 w-3.5" />
          </span>
          {LAYERS.map(({ key, label, tooltip, Icon }) => {
            const active = layers[key];
            return (
              <button
                key={key}
                type="button"
                onClick={() => toggle(key)}
                data-active={active}
                aria-pressed={active}
                title={tooltip}
                className={cn(
                  "ewl-pill h-8 shrink-0 text-[12px] font-medium uppercase tracking-[0.1em]",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-panel",
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </button>
            );
          })}
        </div>
        {dirty && <ResetLayersButton onReset={onReset} />}
      </div>

      {/* Popover on mobile — the wrapping pill row ate ~2 rows above the chart. */}
      <div className="flex lg:hidden items-center gap-2 px-4 py-2 relative">
        <Popover open={open} onOpenChange={setOpen}>
          <PopoverTrigger asChild>
            <button
              type="button"
              aria-label="Toggle chart layers"
              data-active={activeCount > 0}
              className={cn(
                "ewl-pill h-8 shrink-0 text-[12px] font-medium uppercase tracking-[0.1em]",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
              )}
            >
              <LayersIcon className="h-3.5 w-3.5" />
              Layers
              {activeCount > 0 && (
                <span className="ml-0.5 grid place-items-center min-w-4 h-4 px-1 rounded-full bg-accent text-[#062018] text-[10px] font-bold ewl-num">
                  {activeCount}
                </span>
              )}
            </button>
          </PopoverTrigger>
          <PopoverContent aria-label="Chart layers" className="flex flex-col gap-0.5 min-w-[210px]">
            {LAYERS.map(({ key, label, tooltip, Icon }) => {
              const active = layers[key];
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => toggle(key)}
                  aria-pressed={active}
                  title={tooltip}
                  className={cn(
                    "flex items-center gap-2 px-2.5 py-2 rounded text-[12px] font-medium transition-colors",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                    active
                      ? "text-accent-bright bg-accent-soft"
                      : "text-text-dim hover:bg-panel-elev",
                  )}
                >
                  <Icon className="h-3.5 w-3.5 shrink-0" />
                  <span className="flex-1 text-left">{label}</span>
                  {active && (
                    <Check className="h-3.5 w-3.5 shrink-0 text-accent" />
                  )}
                </button>
              );
            })}
          </PopoverContent>
        </Popover>
        {dirty && <ResetLayersButton onReset={onReset} />}
      </div>
      {/* Only when root is a link-wave node (sets populated). */}
      {scenario?.root.sets && scenario.root.sets.length > 0 && (
        <div className="px-5 pb-2 text-[13px] text-text-dim leading-relaxed flex items-start gap-1.5">
          <Link2 className="h-3.5 w-3.5 mt-0.5 shrink-0 text-faint" aria-hidden="true" />
          <span>
            <span className="font-semibold text-text">
              {scenario.pattern_label ?? scenario.family_label ?? "Link-Wave"}
            </span>
            <span className="text-faint"> — </span>
            {scenario.root.sets.map((s, i) => (
              <span key={i}>
                {i > 0 && (
                  <span className="text-faint mx-1.5">·</span>
                )}
                <span className="font-semibold text-text-dim">
                  Set {i + 1}
                </span>
                <span className="text-faint">: </span>
                <span>{s.pattern_label}</span>
              </span>
            ))}
          </span>
        </div>
      )}
      {notes.length > 0 && (
        <ul
          className="px-5 pb-2 flex flex-col gap-1"
          role="status"
          aria-live="polite"
        >
          {notes.map((n) => (
            <li
              key={n.layer}
              className="text-[13px] text-warn leading-relaxed"
            >
              <span className="opacity-60">·</span> {n.text}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
