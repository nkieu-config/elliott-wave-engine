"use client";

import { FlaskConical, Layers } from "lucide-react";
import { useEffect, useState } from "react";
import { useQueryStates } from "nuqs";
import { configParsers } from "@/lib/config";
import { BREAKPOINTS, useMediaQuery } from "@/lib/hooks/use-media-query";
import { useSelectedScenario } from "@/lib/chart-store";
import { usePipeline } from "@/lib/query";
import { cn } from "@/lib/cn";
import { findSelectedScenario, prettyFamily } from "@/lib/scenario-format";
import { maxScore, relativeStrengthPct } from "@/lib/scenario-ranking";
import { BrandMark, StatusPill } from "@/components/layout/app-header";
import { ScenariosPanelContainer } from "@/components/scenarios/scenarios-panel-container";
import { SidePanel } from "@/components/layout/side-panel";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

export function MobileToolbar() {
  const [openConfig, setOpenConfig] = useState(false);
  const [openScenarios, setOpenScenarios] = useState(false);
  const [config] = useQueryStates(configParsers);
  const query = usePipeline(config);
  const [selectedId] = useSelectedScenario();

  // CSS hides the toolbar on lg+ but React state survives — clear stale drawer
  // state on resize. Scenarios go inline at md+, so close it there.
  const isLg = useMediaQuery(`(min-width: ${BREAKPOINTS.lg}px)`);
  const isMd = useMediaQuery(`(min-width: ${BREAKPOINTS.md}px)`);
  useEffect(() => {
    if (isLg) {
      setOpenConfig(false);
      setOpenScenarios(false);
    } else if (isMd) {
      setOpenScenarios(false);
    }
  }, [isLg, isMd]);

  const scenarios = query.data?.report?.scenarios ?? [];
  const selected = findSelectedScenario(query.data, selectedId);
  const scenarioCount = scenarios.length;

  // Relative-strength % (best count = 100%), matching the desktop Inspector.
  const topScore = maxScore(scenarios);
  const strengthPct =
    selected && topScore > 0 ? relativeStrengthPct(selected.score, topScore) : null;

  return (
    <div className="flex items-center gap-2 px-4 py-2 border-b border-border bg-panel/70 backdrop-blur lg:hidden">
      {/* Logo only — wordmark + symbol would crowd the row. */}
      <BrandMark showText={false} />

      <Sheet open={openConfig} onOpenChange={setOpenConfig}>
        <SheetTrigger
          className={cn(
            "inline-flex items-center gap-1.5 min-h-11 px-3 rounded-md border text-xs font-medium transition-colors shrink-0",
            "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent",
            "border-border bg-bg text-text-dim",
            "hover:bg-panel-elev hover:text-text",
            "data-[state=open]:bg-panel-elev data-[state=open]:text-text data-[state=open]:border-border-hi",
          )}
          aria-label="Open lab notebook"
        >
          <FlaskConical className="h-4 w-4 text-accent" />
          {/* Label dropped below sm so everything fits a 390px row. */}
          <span className="hidden sm:inline">Notebook</span>
        </SheetTrigger>
        <SheetContent side="left" title="Lab Notebook" className="p-0">
          <SidePanel embed />
        </SheetContent>
      </Sheet>

      <Sheet open={openScenarios} onOpenChange={setOpenScenarios}>
        <SheetTrigger
          className={cn(
            // flex-1 (not ml-auto): the middle cell truncates its own content so
            // it can never push refresh off the right edge. md:hidden — scenarios
            // are inline at tablet, so no drawer there.
            "md:hidden flex-1 flex items-center gap-2 min-h-11 px-3 rounded-md border text-xs font-medium transition-colors min-w-0",
            "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent",
            "border-border-glow bg-accent-soft text-accent-bright",
            "hover:bg-accent/15",
            "data-[state=open]:bg-accent/20",
          )}
          aria-label={
            selected
              ? `Open scenarios — currently inspecting ${prettyFamily(selected.family)}`
              : "Open scenarios"
          }
        >
          <Layers className="h-4 w-4 shrink-0" />
          <div className="flex flex-col items-start leading-tight min-w-0">
            {selected ? (
              <>
                <span className="truncate max-w-[140px] sm:max-w-[220px] uppercase tracking-[0.08em] text-[12px]">
                  {prettyFamily(selected.family)}
                </span>
                <span className="truncate max-w-[140px] sm:max-w-[220px] text-[11px] ewl-num text-muted tracking-[0.04em]">
                  {strengthPct !== null && `${strengthPct}% · `}
                  {scenarioCount}
                </span>
              </>
            ) : (
              <span className="uppercase tracking-[0.08em] text-[12px]">
                Scenarios{scenarioCount > 0 ? ` · ${scenarioCount}` : ""}
              </span>
            )}
          </div>
        </SheetTrigger>
        <SheetContent side="bottom" title="Scenarios" className="p-0">
          <ScenariosPanelContainer embed />
        </SheetContent>
      </Sheet>

      {/* Filler keeps the status pinned right where the scenarios trigger is hidden (tablet). */}
      <div className="hidden md:block flex-1" aria-hidden="true" />

      <StatusPill minimal />
    </div>
  );
}
