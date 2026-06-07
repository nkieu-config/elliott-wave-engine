"use client";

import { Layers, PanelRightClose } from "lucide-react";
import {
  type KeyboardEvent as ReactKeyboardEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { toast } from "sonner";
import { useCompareScenario, useSelectedScenario } from "@/lib/chart-store";
import { cn } from "@/lib/cn";
import { wrapIndex } from "@/lib/math";
import { maxScore, medalMap, scoreRankMap } from "@/lib/scenario-ranking";
import { prettyFamily } from "@/lib/scenario-format";
import type { Scenario, SampleData } from "@/lib/types";
import { TOAST_DURATION } from "@/lib/ui";
import { ScenarioCard } from "@/components/scenarios/scenario-card";
import { ScenarioInspector } from "@/components/scenarios/scenario-inspector";
import { HelpTooltip } from "@/components/ui/help-tooltip";

const FAMILY_LEGEND =
  "Family codes — 5W TREND: impulsive 5-wave move. 5W SIDEWAY: 5-wave with wave-3 shortest (sideways/range). 3W: corrective 3-wave move (zigzag, flat, triangle).";

export function ScenariosPanel({
  data,
  embed = false,
  onCollapse,
}: {
  data: SampleData | undefined;
  embed?: boolean;
  onCollapse?: () => void;
}) {
  const scenarios = useMemo(() => data?.report?.scenarios ?? [], [data]);
  const [selectedId, setSelectedId] = useSelectedScenario();
  const [compareId, setCompareId] = useCompareScenario();

  // Absolute medal rank: top-3 by raw score, independent of list position.
  const medalById = useMemo(() => medalMap(scenarios), [scenarios]);

  // Real scores cluster low (final = min(structural, visual) * commitment), so
  // absolute bars read as slivers; normalise against the top for legibility.
  const topScore = useMemo(() => maxScore(scenarios), [scenarios]);

  const scoreRankById = useMemo(() => scoreRankMap(scenarios), [scenarios]);

  // Both the render order and the ↑/↓ keyboard-nav order — keep them one array.
  const ordered = useMemo(
    () => [...scenarios].sort((a, b) => b.score - a.score),
    [scenarios],
  );

  const effectiveId = selectedId ?? ordered[0]?.id ?? null;
  const selected =
    scenarios.find((s) => s.id === effectiveId) ?? ordered[0] ?? null;
  const selectedRank = selected ? (scoreRankById.get(selected.id) ?? null) : null;

  const listRef = useRef<HTMLUListElement>(null);

  // Listbox-style up/down: moves selection + focus, wrapping at the ends.
  const onListKeyDown = useCallback(
    (e: ReactKeyboardEvent<HTMLUListElement>) => {
      if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
      if (ordered.length === 0) return;
      e.preventDefault();
      const currentIdx = ordered.findIndex((s) => s.id === effectiveId);
      const start = currentIdx === -1 ? 0 : currentIdx;
      const delta = e.key === "ArrowDown" ? 1 : -1;
      const next = wrapIndex(start, delta, ordered.length);
      const target = ordered[next];
      if (!target) return;
      if (target.id === compareId) void setCompareId(null);
      void setSelectedId(target.id);
      requestAnimationFrame(() => {
        listRef.current
          ?.querySelector<HTMLButtonElement>(
            `button[data-scenario-id="${CSS.escape(target.id)}"]`,
          )
          ?.focus();
      });
    },
    [ordered, effectiveId, compareId, setCompareId, setSelectedId],
  );

  // Identity-stable handlers so the memo'd cards (60+) don't all re-render per
  // selection tick. `compareId` read via ref so it needn't be a callback dep.
  const compareIdRef = useRef(compareId);
  useEffect(() => {
    compareIdRef.current = compareId;
  }, [compareId]);
  const onSelectCard = useCallback(
    (id: string) => {
      if (id === compareIdRef.current) void setCompareId(null);
      void setSelectedId(id);
    },
    [setCompareId, setSelectedId],
  );
  const onToggleCompareCard = useCallback(
    (sc: Scenario) => handleToggleCompare(sc, compareIdRef.current, setCompareId),
    [setCompareId],
  );

  // Dependency-free FLIP: one highlight springs to the selected card's measured
  // box. Measured relative to `wrapRef`, not the viewport, so it stays correct
  // while the list scrolls.
  const wrapRef = useRef<HTMLDivElement>(null);
  const [glideRect, setGlideRect] = useState<{
    top: number;
    left: number;
    width: number;
    height: number;
  } | null>(null);

  const measureGlide = useCallback(() => {
    const wrap = wrapRef.current;
    if (!wrap || !effectiveId) {
      setGlideRect(null);
      return;
    }
    const el = wrap.querySelector<HTMLElement>(
      `[data-scenario-id="${CSS.escape(effectiveId)}"]`,
    );
    if (!el) {
      setGlideRect(null);
      return;
    }
    const wr = wrap.getBoundingClientRect();
    const r = el.getBoundingClientRect();
    setGlideRect({
      top: r.top - wr.top,
      left: r.left - wr.left,
      width: r.width,
      height: r.height,
    });
  }, [effectiveId]);

  useEffect(() => {
    measureGlide();
  }, [measureGlide, ordered]);

  // Re-measure on panel resize / reflow (lg→xl breakpoint, card wrapping, etc.).
  useEffect(() => {
    const wrap = wrapRef.current;
    if (!wrap || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(() => measureGlide());
    ro.observe(wrap);
    return () => ro.disconnect();
  }, [measureGlide]);

  return (
    <aside
      className={cn(
        "flex flex-col min-h-0",
        embed
          ? "h-full"
          : "hidden lg:flex w-80 xl:w-96 shrink-0 border-l border-border ewl-surface-panel",
      )}
      aria-label="Detected scenarios"
    >
      {/* Shares the panel-header lockup with Lab Notebook + AI Reading. */}
      <header className="flex items-center justify-between gap-2 px-5 py-3 border-b border-border">
        <h2 className="flex items-center gap-2 text-[13px] font-bold uppercase tracking-[0.18em] text-text m-0">
          <span
            aria-hidden="true"
            className="h-3 w-[3px] rounded-[2px] shrink-0 bg-gradient-to-b from-accent to-cyan"
          />
          Scenarios
          <HelpTooltip text={FAMILY_LEGEND} label="About scenario families" />
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-[12px] ewl-num text-muted">
            {scenarios.length} {scenarios.length === 1 ? "count" : "counts"}
          </span>
          {onCollapse && (
            <button
              type="button"
              onClick={onCollapse}
              aria-label="Collapse Scenarios panel"
              title="Collapse panel"
              className={cn(
                "grid place-items-center h-6 w-6 rounded-md shrink-0 transition-colors",
                "text-faint hover:text-text hover:bg-panel-elev",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
              )}
            >
              <PanelRightClose className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </header>

      {selected && (
        <ScenarioInspector
          scenario={selected}
          rank={selectedRank}
          medalRank={medalById.get(selected.id) ?? null}
          topScore={topScore}
          totalScenarios={scenarios.length}
        />
      )}

      {/* `overscroll-contain` stops scroll chaining past the list's edge. */}
      <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain">
        {ordered.length === 0 ? (
          <div className="px-5 py-10 text-center text-sm text-muted">
            <Layers className="h-7 w-7 mx-auto mb-2 text-faint" />
            No scenarios returned by the pipeline.
          </div>
        ) : (
          <div ref={wrapRef} className="relative">
            {/* The only selection affordance (rows are flat). */}
            {glideRect && (
              <div
                aria-hidden="true"
                className="pointer-events-none absolute z-10"
                style={{
                  top: glideRect.top,
                  left: glideRect.left,
                  width: glideRect.width,
                  height: glideRect.height,
                  backgroundColor: "color-mix(in srgb, var(--color-accent) 6%, transparent)",
                  boxShadow:
                    "inset 0 0 0 1px var(--color-border-glow), 0 0 18px -10px var(--color-accent-glow)",
                  transition:
                    "top 440ms cubic-bezier(0.34,1.56,0.64,1), left 440ms cubic-bezier(0.34,1.56,0.64,1), width 320ms ease, height 320ms ease",
                }}
              />
            )}
            <ul
              ref={listRef}
              className="py-1 divide-y divide-border"
              // Skip off-screen rows on long lists (globals.css `ul[data-cv-rows]`).
              // Gated on count: paint containment clips the compare button's
              // expanded tap zone — fine when long, needless when short.
              data-cv-rows={ordered.length > 20 ? "" : undefined}
              onKeyDown={onListKeyDown}
            >
              {ordered.map((sc) => (
                <ScenarioCard
                  key={sc.id}
                  scoreRank={scoreRankById.get(sc.id) ?? 0}
                  medalRank={medalById.get(sc.id) ?? null}
                  scenario={sc}
                  topScore={topScore}
                  selected={sc.id === effectiveId}
                  isCompared={sc.id === compareId}
                  canCompare={sc.id !== effectiveId}
                  onSelect={onSelectCard}
                  onToggleCompare={onToggleCompareCard}
                />
              ))}
            </ul>
          </div>
        )}
      </div>
    </aside>
  );
}

function handleToggleCompare(
  sc: Scenario,
  compareId: string | null,
  setCompareId: (id: string | null) => Promise<URLSearchParams> | void,
) {
  if (sc.id === compareId) {
    void setCompareId(null);
    toast.success("Compare cleared", { duration: TOAST_DURATION });
  } else {
    void setCompareId(sc.id);
    toast.success(`Comparing vs ${prettyFamily(sc.family)}`, { duration: TOAST_DURATION });
  }
}
