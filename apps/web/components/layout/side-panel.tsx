"use client";

import { useQueryStates } from "nuqs";
import { useCallback, useEffect, useState } from "react";
import { PanelLeftClose, RotateCcw } from "lucide-react";
import { toast } from "sonner";
import {
  COMMITMENT_CURVES,
  CONFIG_DEFAULTS,
  PERIODS,
  SCALE_MODES,
  TIMEFRAMES,
  configParsers,
  type CommitmentCurve,
  type Period,
  type ScaleMode,
  type Timeframe,
} from "@/lib/config";
import { cn } from "@/lib/cn";
import { orderedWindow } from "@/lib/math";
import { usePipeline } from "@/lib/query";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ConsoleStep } from "@/components/layout/console-step";
import {
  DetectReadout,
  Field,
  LabelWithHelp,
  RangeField,
  SegmentedControl,
  SliderField,
} from "@/components/layout/console-fields";

// Config keys per section — drives the per-section dirty indicator.
const SECTION_FIELDS = {
  instrument: ["symbol"],
  window: ["timeframe", "period", "scale_mode"],
  detect: ["atr_period", "atr_multiplier", "atr_floor", "min_bars_between"],
  score: [
    "k_sigma",
    "log_tol_fib",
    "pull_depth_lo",
    "pull_depth_hi",
    "pull_depth_tol",
    "pivot_window",
    "commitment_curve",
  ],
} as const satisfies Record<string, ReadonlyArray<keyof typeof CONFIG_DEFAULTS>>;

export function SidePanel({
  embed = false,
  onCollapse,
}: { embed?: boolean; onCollapse?: () => void } = {}) {
  const [config, setConfig] = useQueryStates(configParsers, {
    history: "replace",
    shallow: true,
    throttleMs: 200,
  });
  // Reuses the cached pipeline result (dedupes on config key).
  const pipeline = usePipeline(config);
  const rawCount = pipeline.data?.raw_pivots.length ?? null;
  const activeCount = pipeline.data?.active_pivots.length ?? null;

  const isDirty = (k: keyof typeof CONFIG_DEFAULTS) => config[k] !== CONFIG_DEFAULTS[k];
  const globalDirty = (Object.keys(CONFIG_DEFAULTS) as Array<keyof typeof CONFIG_DEFAULTS>)
    .some(isDirty);
  const sectionDirty = (section: keyof typeof SECTION_FIELDS) =>
    SECTION_FIELDS[section].some(isDirty);

  // Reset is destructive — toast carries an Undo while it's visible (5s).
  const reset = () => {
    const prev = { ...config };
    setConfig(CONFIG_DEFAULTS);
    toast.success("Config reset to defaults", {
      duration: 5000,
      action: {
        label: "Undo",
        onClick: () => setConfig(prev),
      },
    });
  };

  // Commit on blur/Enter, not per keystroke — each commit rekeys the pipeline
  // query, so typing "DDOG" would otherwise fire 4 fetches.
  const [symbolDraft, setSymbolDraft] = useState(config.symbol);
  useEffect(() => setSymbolDraft(config.symbol), [config.symbol]);
  const commitSymbol = useCallback(() => {
    const next = symbolDraft.trim().toUpperCase();
    if (next && next !== config.symbol) setConfig({ symbol: next });
    else setSymbolDraft(config.symbol); // empty/unchanged → revert to canonical
  }, [symbolDraft, config.symbol, setConfig]);

  // lo/hi clamp must stay in sync across rapid drags.
  const setPullDepth = useCallback(
    ([lo, hi]: number[]) => {
      const [pull_depth_lo, pull_depth_hi] = orderedWindow(lo, hi);
      setConfig({ pull_depth_lo, pull_depth_hi });
    },
    [setConfig],
  );

  return (
    <aside
      className={cn(
        "flex flex-col",
        embed
          ? "h-full"
          : "hidden lg:flex w-72 xl:w-80 shrink-0 border-r border-border ewl-surface-sidebar",
      )}
      aria-label="Pipeline configuration"
    >
      <header className="flex items-center justify-between gap-2 px-4 py-3 border-b border-border">
        {/* Header lockup shared verbatim across the three panels so they read
            as one landmark system. */}
        <h2 className="flex items-center gap-2 text-[13px] font-bold uppercase tracking-[0.18em] text-text m-0">
          <span
            aria-hidden="true"
            className="h-3 w-[3px] rounded-[2px] shrink-0 bg-gradient-to-b from-accent to-cyan"
          />
          Lab Notebook
        </h2>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={reset}
            disabled={!globalDirty}
            aria-label="Reset all configuration to defaults"
            title="Reset all to defaults"
            className={cn(
              "grid place-items-center h-7 w-7 rounded-md shrink-0 transition-colors",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
              globalDirty
                ? "text-accent-bright hover:bg-accent-soft"
                : "text-faint cursor-not-allowed",
            )}
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
          {onCollapse && (
            <button
              type="button"
              onClick={onCollapse}
              aria-label="Collapse Lab Notebook panel"
              title="Collapse panel"
              className={cn(
                "grid place-items-center h-7 w-7 rounded-md shrink-0 transition-colors",
                "text-faint hover:text-text hover:bg-panel-elev",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
              )}
            >
              <PanelLeftClose className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </header>

      <div className="flex-1 overflow-y-auto overscroll-contain px-3.5 py-4">
        <div className="ewl-console">
          <ConsoleStep num={1} title="Instrument" dirty={sectionDirty("instrument")} collapsible={false}>
            <Field label="Symbol">
              <div className="ewl-symbol-input">
                <input
                  value={symbolDraft}
                  onChange={(e) => setSymbolDraft(e.target.value.toUpperCase())}
                  onBlur={commitSymbol}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") e.currentTarget.blur(); // blur → commit
                  }}
                  placeholder="DDOG"
                  name="symbol"
                  // A ticker is not a credential — opt out so password managers
                  // and autocomplete don't pop over the field.
                  autoComplete="off"
                  autoCorrect="off"
                  spellCheck={false}
                  autoCapitalize="characters"
                  aria-label="Ticker symbol"
                />
              </div>
            </Field>
          </ConsoleStep>

          <ConsoleStep num={2} title="Window & scale" dirty={sectionDirty("window")} defaultOpen>
            <Field label="Timeframe">
              <Select
                value={config.timeframe}
                onValueChange={(v) => setConfig({ timeframe: v as Timeframe })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TIMEFRAMES.map((tf) => (
                    <SelectItem key={tf} value={tf}>
                      {tf}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
            <Field label="Period">
              <Select
                value={config.period}
                onValueChange={(v) => setConfig({ period: v as Period })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PERIODS.map((p) => (
                    <SelectItem key={p} value={p}>
                      {p}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
            <Field label="Price scale">
              <SegmentedControl<ScaleMode>
                options={SCALE_MODES}
                value={config.scale_mode}
                onChange={(v) => setConfig({ scale_mode: v })}
                ariaLabel="Price scale"
              />
            </Field>
          </ConsoleStep>

          <ConsoleStep num={3} title="Detect waves" dirty={sectionDirty("detect")} defaultOpen>
            <SliderField
              label="ATR period"
              help="Window of bars used to compute the ATR baseline that drives ZigZag pivot detection. Larger = smoother, fewer pivots."
              value={config.atr_period}
              min={4}
              max={60}
              step={1}
              unit="bars"
              onChange={(v) => setConfig({ atr_period: v })}
            />
            <SliderField
              label="ATR multiplier"
              help="Minimum swing size required to count as a pivot, expressed as multiples of ATR. Higher = only larger swings registered."
              value={config.atr_multiplier}
              min={0.5}
              max={6}
              step={0.1}
              decimals={1}
              unit="×"
              onChange={(v) => setConfig({ atr_multiplier: v })}
            />
            <SliderField
              label="ATR floor"
              help="Hard minimum swing size as a fraction of price (e.g. 0.10 = 10%). Filters out micro-swings on very low-volatility windows."
              value={config.atr_floor}
              min={0}
              max={0.3}
              step={0.01}
              decimals={2}
              unit="%"
              displayMultiplier={100}
              onChange={(v) => setConfig({ atr_floor: v })}
            />
            <SliderField
              label="Min bars between"
              help="Minimum bars required between two pivots. Drops same-direction clusters that the ATR test alone misses."
              value={config.min_bars_between}
              min={1}
              max={12}
              step={1}
              unit="bars"
              onChange={(v) => setConfig({ min_bars_between: v })}
            />
            <DetectReadout raw={rawCount} active={activeCount} />
          </ConsoleStep>

          <ConsoleStep num={4} title="Score" dirty={sectionDirty("score")} last>
            <div className="ewl-step-subhead">Scoring · tuning</div>
            <SliderField
              label="Speed cluster (k_σ)"
              help="Tolerance for wave-speed dispersion, in standard deviations. Lower = stricter requirement that push waves share a similar bar-rate."
              value={config.k_sigma}
              min={0.1}
              max={1.5}
              step={0.05}
              decimals={2}
              unit="σ"
              onChange={(v) => setConfig({ k_sigma: v })}
            />
            <SliderField
              label="Fib tolerance"
              help="Allowed deviation from canonical Fibonacci ratios when matching wave-length ratios, in log-space."
              value={config.log_tol_fib}
              min={0.01}
              max={0.3}
              step={0.01}
              decimals={2}
              unit="±"
              onChange={(v) => setConfig({ log_tol_fib: v })}
            />
            <RangeField
              label="Pull-depth band"
              help="Acceptable retracement band for pullback waves (S2/S4) — drag the two thumbs to set the lower and upper bound."
              value={[config.pull_depth_lo, config.pull_depth_hi]}
              min={0}
              max={0.95}
              step={0.01}
              decimals={2}
              onChange={setPullDepth}
            />
            <SliderField
              label="Pull-depth tol"
              help="Soft margin around the band edges. Pullbacks slightly outside the band still score, but with a penalty."
              value={config.pull_depth_tol}
              min={0.01}
              max={0.5}
              step={0.01}
              decimals={2}
              unit="±"
              onChange={(v) => setConfig({ pull_depth_tol: v })}
            />
            <SliderField
              label="Pivot window"
              help="Bars around a pivot used to score its sharpness. Larger = more lenient on rounded turns."
              value={config.pivot_window}
              min={1}
              max={5}
              step={1}
              unit="bars"
              onChange={(v) => setConfig({ pivot_window: v })}
            />

            <div className="ewl-step-subhead">Display · filter</div>
            <Field
              label={
                <LabelWithHelp
                  text="Commitment curve"
                  help="Curve used to weight in-progress (still-developing) scenarios. 'off' = no penalty, 'sqrt' = soft, 'linear' = strict."
                />
              }
            >
              <SegmentedControl<CommitmentCurve>
                options={COMMITMENT_CURVES}
                value={config.commitment_curve}
                onChange={(v) => setConfig({ commitment_curve: v })}
                ariaLabel="Commitment curve"
              />
            </Field>
          </ConsoleStep>
        </div>
      </div>

      <footer className="px-4 py-3 border-t border-border text-[13px] leading-relaxed text-faint">
        <span className="inline-flex items-center gap-1.5 text-muted">
          <span className="ewl-pulse-dot ewl-pulse" aria-hidden="true" />
          URL state
        </span>{" "}
        — share the link to load the same setup.
      </footer>
    </aside>
  );
}
