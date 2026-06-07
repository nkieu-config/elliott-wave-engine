"use client";

import { useQueryStates } from "nuqs";
import { type ReactNode, useEffect, useRef, useState } from "react";
import { useSelectedScenario } from "@/lib/chart-store";
import { configParsers } from "@/lib/config";
import { useLocale } from "@/lib/locale";
import { FLAT, numDelta, type DeltaDir, type DeltaMeta } from "@/lib/kpi-format";
import { usePipeline, useLayer1 } from "@/lib/query";
import { findSelectedScenario } from "@/lib/scenario-format";
import type { Scenario, ScenarioCounts, Target as Layer1Target, TargetSet } from "@/lib/types";
import { AnimatedNumber } from "@/components/ui/animated-number";
import { TapeMeter, type Tone } from "@/components/ui/tape-meter";
import { BrandTear, StatusReadout } from "@/components/layout/app-header";

// Keyed so a config/scenario switch drops the baseline (never diff across
// instruments). Written in an effect so the render still reads the prior value;
// idempotent write keeps Strict Mode's double-invoke a no-op, not a 2x advance.
function usePrevious<T>(value: T, key: string): T | undefined {
  // Seed undefined so the first observation has no baseline (renders "—").
  const ref = useRef<{ key: string; value: T | undefined }>({ key, value: undefined });
  useEffect(() => {
    ref.current = { key, value };
  });
  return ref.current.key === key ? ref.current.value : undefined;
}

// One-shot DeltaDir on signal change, auto-clearing after the animation.
// Reduced-motion gated in CSS, so JS always fires (no window/SSR branch).
function useFlash(signal: number | string | null, dir: DeltaDir): DeltaDir | null {
  const [flash, setFlash] = useState<DeltaDir | null>(null);
  const prev = useRef(signal);
  useEffect(() => {
    if (prev.current === signal) return;
    prev.current = signal;
    if (dir === "flat") {
      setFlash(null);
      return;
    }
    setFlash(dir);
    const t = setTimeout(() => setFlash(null), 520);
    return () => clearTimeout(t);
  }, [signal, dir]);
  return flash;
}

// aria-hidden — change is voiced via Tear's sr-only live region.
// translate="no" so auto-translate can't mangle number/code text.
function DeltaChip({ meta }: { meta: DeltaMeta }) {
  const glyph = meta.dir === "up" ? "▲" : meta.dir === "down" ? "▼" : "—";
  return (
    <span className="ewl-tear-delta" data-dir={meta.dir} aria-hidden="true">
      <span className="g">{glyph}</span>
      {meta.noTranslate ? <span translate="no">{meta.text}</span> : meta.text}
    </span>
  );
}

export function KpiRow() {
  const [config] = useQueryStates(configParsers);
  const pipeline = usePipeline(config);
  const [selectedId] = useSelectedScenario();

  // Falls back to top_scenario before ChartShell's selection effect runs.
  const selected = findSelectedScenario(pipeline.data, selectedId);

  // Disabled until a scenario is locked in so we don't fire a useless first call.
  const layer1 = useLayer1(config, selected?.id ?? null);

  const currentClose = pipeline.data?.bars.length
    ? pipeline.data.bars[pipeline.data.bars.length - 1].close
    : null;

  const configKey = JSON.stringify(config);

  // A non-top scenario is picked → cells 01/02/04 reflect it; tagged in Pattern.
  const topId = pipeline.data?.top_scenario?.id ?? null;
  const inspecting = !!selected && topId != null && selected.id !== topId;

  return (
    <div className="ewl-cmd-bar">
      {/* Generic <header>, NOT a banner landmark — it sits inside <main>.
          Desktop-only: phones show the brand in MobileToolbar. */}
      <header className="ewl-cmd-brand">
        <BrandTear />
      </header>
      <section className="ewl-tear-strip" aria-label="Key metrics for the selected scenario">
        <PatternTear scenario={selected} configKey={configKey} inspecting={inspecting} />
        <ConfidenceTear scenario={selected} configKey={configKey} />
        <ScenariosTear counts={pipeline.data?.scenario_counts} configKey={configKey} />
        <NextTargetTear
          scenario={selected}
          targets={layer1.data?.targets ?? null}
          currentClose={currentClose}
          isLoading={layer1.isLoading || layer1.isFetching}
          configKey={configKey}
        />
      </section>
      <div className="ewl-cmd-controls">
        <StatusReadout />
      </div>
    </div>
  );
}

function Tear({
  idx,
  label,
  tone = "muted",
  textValue = false,
  value,
  sub,
  tape,
  ariaLabel,
  delta,
  flash = null,
}: {
  idx: string;
  label: string;
  tone?: Tone;
  /** word/string hero (looser tracking, smaller) vs numeric hero. */
  textValue?: boolean;
  value: ReactNode;
  sub: ReactNode;
  /** omit on no-data/loading branches (renders a spacer). */
  tape?: ReactNode;
  ariaLabel: string;
  delta?: DeltaMeta;
  flash?: DeltaDir | null;
}) {
  // Only on a real signal; flat resting state stays hidden.
  const hasDelta = !!delta && (delta.dir !== "flat" || delta.announce !== "");
  return (
    <div
      className="ewl-tear"
      data-tone={tone === "muted" ? undefined : tone}
      data-kind={textValue ? "text" : undefined}
      data-flash={flash ?? undefined}
      role="group"
      aria-label={ariaLabel}
    >
      <div className="ewl-tear-kicker">
        <span className="idx" aria-hidden="true">
          {idx}
        </span>
        {label}
      </div>
      {hasDelta && delta && <DeltaChip meta={delta} />}
      <div className="ewl-tear-value">{value}</div>
      {/* No-tape cells reserve the meter slot so hero/sub baselines stay aligned. */}
      {tape ?? <span className="ewl-tape-spacer" aria-hidden="true" />}
      <div className="ewl-tear-sub">{sub}</div>
      {/* Chip is aria-hidden, so the change reaches screen readers only here. */}
      {delta?.announce ? (
        <span className="sr-only" aria-live="polite">
          {delta.announce}
        </span>
      ) : null}
    </div>
  );
}

// Pattern is categorical, so a fill meter would fake a measurement — a 2-node
// developing→complete stepper fills the meter slot instead.
function StageTrack({ complete }: { complete: boolean }) {
  return (
    <div className="ewl-tear-track" data-complete={complete ? "true" : undefined} aria-hidden="true">
      <span className="ewl-tear-track-node" data-on="true" />
      <span className="ewl-tear-track-line" />
      <span className="ewl-tear-track-node" data-on={complete ? "true" : undefined} />
    </div>
  );
}

function PatternTear({
  scenario,
  configKey,
  inspecting,
}: {
  scenario: Scenario | null;
  configKey: string;
  inspecting: boolean;
}) {
  const family = scenario?.family_label || scenario?.family || "—";
  const pattern = scenario?.pattern_label || family || "unclassified";
  const status = scenario?.is_complete && scenario?.pattern_kind ? "complete" : "developing";

  // Categorical delta: advancing → "locked", regressing → "reopened", relabel → "reclassed".
  const sig = scenario ? `${pattern}␟${status}` : null;
  const prevSig = usePrevious(sig, `${configKey}:${scenario?.id ?? "none"}`);
  let delta: DeltaMeta = FLAT;
  if (scenario && prevSig != null && prevSig !== sig) {
    const [pPat, pStatus] = prevSig.split("␟");
    if (pPat !== pattern) {
      delta = { dir: "flat", text: "reclassed", announce: `Pattern reclassified to ${pattern}`, noTranslate: false };
    } else if (pStatus !== status) {
      delta =
        status === "complete"
          ? { dir: "up", text: "locked", announce: "Pattern locked", noTranslate: false }
          : { dir: "down", text: "reopened", announce: "Pattern reopened", noTranslate: false };
    }
  }
  const flash = useFlash(sig, delta.dir);

  if (!scenario) {
    return (
      <Tear
        idx="01"
        label="Pattern"
        textValue
        value="—"
        ariaLabel="Pattern: no result yet"
        sub={<span className="word">no result yet</span>}
      />
    );
  }
  return (
    <Tear
      idx="01"
      label="Pattern"
      tone="primary"
      textValue
      value={pattern}
      ariaLabel={`Pattern: ${pattern}, ${status}`}
      delta={delta}
      flash={flash}
      tape={<StageTrack complete={status === "complete"} />}
      // Avoid printing "5W Trend · 5W Trend" when pattern resolves to family.
      sub={
        <>
          {inspecting && (
            <>
              <span className="ewl-tear-inspecting">inspecting</span>
              <span aria-hidden="true">·</span>
            </>
          )}
          {pattern === family ? (
            <span className={status === "complete" ? "word done" : "word"}>{status}</span>
          ) : (
            <>
              <span>{family}</span>
              <span aria-hidden="true">·</span>
              <span className={status === "complete" ? "word done" : "word"}>{status}</span>
            </>
          )}
        </>
      }
    />
  );
}

function ConfidenceTear({ scenario, configKey }: { scenario: Scenario | null; configKey: string }) {
  const score = scenario
    ? Math.round((scenario.score_components?.total ?? scenario.score) * 100)
    : null;
  const prevScore = usePrevious(score, `${configKey}:${scenario?.id ?? "none"}`);
  const locale = useLocale();
  const delta =
    score == null ? FLAT : numDelta("Confidence", score, prevScore, { unit: "points", locale });
  const flash = useFlash(score, delta.dir);

  if (!scenario || score == null) {
    return (
      <Tear
        idx="02"
        label="Confidence"
        textValue
        value="—"
        ariaLabel="Confidence: no result yet"
        sub={<span className="word">—</span>}
      />
    );
  }
  const tier = scenario.confidence_tier;
  const tone: Tone = tier.key === "high" ? "up" : tier.key === "mid" ? "warn" : "down";
  return (
    <Tear
      idx="02"
      label="Confidence"
      tone={tone}
      textValue
      value={tier.word}
      ariaLabel={`Confidence: ${tier.word}, score ${score}`}
      delta={delta}
      flash={flash}
      // The strip's only true 0–100 magnitude.
      tape={<TapeMeter tone={tone} fill={score} />}
      sub={
        <>
          <span>{score}</span>
          <span className="word">score</span>
        </>
      }
    />
  );
}

function ScenariosTear({ counts, configKey }: { counts: ScenarioCounts | undefined; configKey: string }) {
  const total = counts?.total ?? null;
  // Count is config-level (not scenario-scoped), so baseline keys on config alone.
  const prevTotal = usePrevious(total, configKey);
  const locale = useLocale();
  const delta = total == null ? FLAT : numDelta("Scenarios", total, prevTotal, { locale });
  const flash = useFlash(total, delta.dir);

  if (!counts) {
    return (
      <Tear
        idx="03"
        label="Scenarios"
        value="—"
        ariaLabel="Scenarios: no result yet"
        sub={<span className="word">—</span>}
        tape={<TapeMeter empty />}
      />
    );
  }
  if (counts.total === 0) {
    return (
      <Tear
        idx="03"
        label="Scenarios"
        tone="down"
        value="0"
        ariaLabel="Scenarios: none — no valid wave count"
        delta={delta}
        flash={flash}
        sub={<span className="word">no valid wave count</span>}
        tape={<TapeMeter empty />}
      />
    );
  }
  // complete + open === total → two segments fill the whole meter (stacked ratio).
  const completePct = (counts.complete / counts.total) * 100;
  const openPct = (counts.open / counts.total) * 100;
  return (
    <Tear
      idx="03"
      label="Scenarios"
      tone="primary"
      value={<AnimatedNumber value={counts.total} format={(n) => String(Math.round(n))} />}
      ariaLabel={`Scenarios: ${counts.total} total, ${counts.complete} complete, ${counts.open} open`}
      delta={delta}
      flash={flash}
      tape={<TapeMeter tone="up" fill={completePct} openFill={openPct} />}
      sub={
        <>
          <span className="done">{counts.complete}</span>
          <span className="word">complete</span>
          <span aria-hidden="true">·</span>
          <span className="open">{counts.open}</span>
          <span className="word">open</span>
        </>
      }
    />
  );
}

function NextTargetTear({
  scenario,
  targets,
  currentClose,
  isLoading,
  configKey,
}: {
  scenario: Scenario | null;
  targets: TargetSet | null;
  currentClose: number | null;
  isLoading: boolean;
  configKey: string;
}) {
  // Resolve up front so the delta hooks run before early returns.
  // Priority: confirmation > Fib flow > invalidation.
  let chosen: Layer1Target | null = null;
  let kindLabel = "";
  if (targets) {
    if (targets.confirmation_targets.length > 0) {
      chosen = targets.confirmation_targets[0];
      kindLabel = "confirmation";
    } else if (targets.fib_flow_targets.length > 0) {
      chosen = targets.fib_flow_targets[0];
      kindLabel = "Fibonacci flow";
    } else if (targets.invalidation) {
      chosen = targets.invalidation;
      kindLabel = "invalidation";
    }
  }
  // Delta = target price drift between runs.
  const price = chosen?.price ?? null;
  const prevPrice = usePrevious(price, `${configKey}:${scenario?.id ?? "none"}`);
  const locale = useLocale();
  const delta =
    price == null ? FLAT : numDelta("Next target", price, prevPrice, { currency: true, locale });
  const flash = useFlash(price, delta.dir);

  if (!scenario) {
    return (
      <Tear
        idx="04"
        label="Next Target"
        value="—"
        ariaLabel="Next target: no result yet"
        sub={<span className="word">—</span>}
        tape={<TapeMeter empty />}
      />
    );
  }
  if (isLoading && !targets) {
    return (
      <Tear
        idx="04"
        label="Next Target"
        value={<span className="ewl-tear-loading" aria-label="Loading target…" />}
        ariaLabel="Next target: resolving"
        sub={<span className="word">resolving…</span>}
        tape={<TapeMeter empty />}
      />
    );
  }
  if (!targets) {
    return (
      <Tear
        idx="04"
        label="Next Target"
        value="—"
        ariaLabel="Next target: unavailable"
        sub={<span className="word">targets unavailable</span>}
        tape={<TapeMeter empty />}
      />
    );
  }
  if (chosen === null) {
    return (
      <Tear
        idx="04"
        label="Next Target"
        value="—"
        ariaLabel="Next target: none for this pattern"
        sub={<span className="word">no target for this pattern</span>}
        tape={<TapeMeter empty />}
      />
    );
  }

  const isInvalidation = kindLabel === "invalidation";
  const movePct =
    currentClose && currentClose > 0 ? ((chosen.price - currentClose) / currentClose) * 100 : null;
  // Downside target reads rose so a green "$115" can't be misread as upside
  // against a −46% sub.
  const tone: Tone = isInvalidation || (movePct != null && movePct < 0) ? "down" : "primary";
  // min 6% so a tiny move still reads, capped at 100%.
  const tapeTone: Tone = isInvalidation || (movePct != null && movePct < 0) ? "down" : "up";
  const fillMag = movePct != null ? Math.min(100, Math.max(6, Math.abs(movePct))) : 100;
  const moveStr = movePct != null ? `${movePct >= 0 ? "+" : ""}${movePct.toFixed(0)}%` : "";

  return (
    <Tear
      idx="04"
      label="Next Target"
      tone={tone}
      value={
        <>
          $
          <AnimatedNumber
            value={chosen.price}
            format={(n) => n.toLocaleString(locale, { maximumFractionDigits: 0 })}
          />
        </>
      }
      ariaLabel={`Next target: $${Math.round(chosen.price).toLocaleString(locale)}${moveStr ? `, ${moveStr}` : ""}, ${kindLabel}`}
      delta={delta}
      flash={flash}
      tape={<TapeMeter tone={tapeTone} fill={fillMag} />}
      sub={
        movePct != null ? (
          <>
            <span className={movePct >= 0 ? "pos" : "neg"}>{moveStr}</span>
            <span aria-hidden="true">·</span>
            <span className="word">{kindLabel}</span>
          </>
        ) : (
          <span className="word">{kindLabel}</span>
        )
      }
    />
  );
}
