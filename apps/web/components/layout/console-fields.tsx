"use client";

import { useCallback, type ReactNode } from "react";
import { cn } from "@/lib/cn";
import { HelpTooltip } from "@/components/ui/help-tooltip";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { TapeMeter } from "@/components/ui/tape-meter";

export function Field({
  label,
  children,
}: {
  label: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      {typeof label === "string" ? <Label>{label}</Label> : label}
      {children}
    </div>
  );
}

export function LabelWithHelp({ text, help }: { text: string; help: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <Label>{text}</Label>
      <HelpTooltip text={help} />
    </div>
  );
}

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  ariaLabel,
}: {
  options: readonly T[];
  value: T;
  onChange: (v: T) => void;
  ariaLabel: string;
}) {
  return (
    <div
      className={cn(
        "grid rounded-md border border-border bg-bg p-0.5",
      )}
      style={{ gridTemplateColumns: `repeat(${options.length}, minmax(0, 1fr))` }}
      role="radiogroup"
      aria-label={ariaLabel}
    >
      {options.map((opt) => {
        const active = opt === value;
        return (
          <button
            key={opt}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(opt)}
            className={cn(
              "h-7 rounded text-[12px] font-medium uppercase tracking-wider transition-colors",
              active
                ? "bg-accent-soft text-accent-bright shadow-[inset_0_0_0_1px_var(--color-border-glow)]"
                : "text-muted hover:text-text",
            )}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}

function fmtBound(
  v: number,
  decimals: number,
  unit: string,
  displayMultiplier: number,
) {
  return `${(v * displayMultiplier).toFixed(decimals)}${unit}`;
}

export function SliderField({
  label,
  help,
  value,
  min,
  max,
  step,
  decimals = 0,
  unit = "",
  displayMultiplier = 1,
  onChange,
}: {
  label: string;
  help?: string;
  value: number;
  min: number;
  max: number;
  step: number;
  decimals?: number;
  unit?: string;
  /** Multiplier applied to the displayed number (e.g. 100 for percentage). */
  displayMultiplier?: number;
  onChange: (v: number) => void;
}) {
  const handleChange = useCallback(
    ([v]: number[]) => onChange(v),
    [onChange],
  );
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 min-w-0">
          <Label>{label}</Label>
          {help && <HelpTooltip text={help} />}
        </div>
        <span className="ewl-slider-val">
          {(value * displayMultiplier).toFixed(decimals)}
          {unit && <span className="unit">{unit}</span>}
        </span>
      </div>
      <Slider
        value={[value]}
        min={min}
        max={max}
        step={step}
        onValueChange={handleChange}
        thumbAriaLabels={[label]}
      />
      <div className="ewl-slider-scale" aria-hidden="true">
        <span>{fmtBound(min, decimals, unit, displayMultiplier)}</span>
        <span>{fmtBound(max, decimals, unit, displayMultiplier)}</span>
      </div>
    </div>
  );
}

export function RangeField({
  label,
  help,
  value,
  min,
  max,
  step,
  decimals = 0,
  onChange,
}: {
  label: string;
  help?: string;
  value: [number, number];
  min: number;
  max: number;
  step: number;
  decimals?: number;
  onChange: (v: number[]) => void;
}) {
  const [lo, hi] = value;
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 min-w-0">
          <Label>{label}</Label>
          {help && <HelpTooltip text={help} />}
        </div>
        <span className="ewl-slider-val">
          {lo.toFixed(decimals)}
          <span className="unit mx-1">–</span>
          {hi.toFixed(decimals)}
        </span>
      </div>
      <Slider
        value={[lo, hi]}
        min={min}
        max={max}
        step={step}
        onValueChange={onChange}
        thumbAriaLabels={[`${label} lower`, `${label} upper`]}
        minStepsBetweenThumbs={1}
      />
      <div className="ewl-slider-scale" aria-hidden="true">
        <span>{min.toFixed(decimals)}</span>
        <span>{max.toFixed(decimals)}</span>
      </div>
    </div>
  );
}

// How many raw ATR pivots survive the min-bars spacing filter.
export function DetectReadout({ raw, active }: { raw: number | null; active: number | null }) {
  const pending = raw === null || active === null;
  const dropped = pending ? 0 : raw - active;
  const pct = pending || raw === 0 ? 0 : Math.round((active / raw) * 100);
  return (
    <div className="ewl-readout" aria-live="polite">
      <div className="ewl-readout-row">
        <span>
          {pending ? (
            "pivot detection pending…"
          ) : (
            <>
              <b>{raw}</b> raw <span aria-hidden="true">→</span> <b>{active}</b> kept
            </>
          )}
        </span>
        {!pending && dropped > 0 && (
          <span className="ewl-readout-drop">−{dropped}</span>
        )}
      </div>
      <TapeMeter fill={pct} empty={pending} />
    </div>
  );
}
