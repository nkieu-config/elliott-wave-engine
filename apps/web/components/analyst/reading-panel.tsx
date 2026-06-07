"use client";

import { ChevronDown, MessageCircleQuestion } from "lucide-react";
import { useMemo } from "react";
import { useQueryStates } from "nuqs";
import { useAskPanel } from "@/lib/ask-store";
import { useSelectedScenario } from "@/lib/chart-store";
import { cn } from "@/lib/cn";
import { configParsers } from "@/lib/config";
import { usePipeline } from "@/lib/query";
import { familyColor, findSelectedScenario, prettyFamily } from "@/lib/scenario-format";
import { NarrationTabs } from "@/components/analyst/narration-tabs";
import { QaPanel } from "@/components/qa/qa-panel";
import { ErrorBoundary } from "@/components/feedback/error-boundary";

export function ReadingPanel() {
  const [config] = useQueryStates(configParsers);
  const query = usePipeline(config);
  const [selectedId] = useSelectedScenario();
  // In-place disclosure, not an overlay, so a question reads as part of the same
  // flow. Open state in a store so "/" hotkey and the follow-up link share it.
  const askOpen = useAskPanel((s) => s.open);
  const toggleAsk = useAskPanel((s) => s.toggle);

  const selected = useMemo(
    () => findSelectedScenario(query.data, selectedId),
    [query.data, selectedId],
  );

  return (
    <div className="flex flex-col bg-bg">
      {/* Scrolls away; NarrationTabs is the single sticky bar. Score isn't
          repeated — the KPI command bar pins Confidence. */}
      <header className="flex items-center gap-2 h-11 px-5 shrink-0 border-b border-border bg-panel">
        <span
          aria-hidden="true"
          className="h-3 w-[3px] rounded-[2px] shrink-0 bg-gradient-to-b from-accent to-cyan"
        />
        <h2 className="text-[13px] font-bold uppercase tracking-[0.18em] text-text m-0">
          AI Reading
        </h2>
        <div className="ml-auto flex items-center gap-2.5 shrink-0">
          {selected && (
            <span
              className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.08em] ewl-num"
              style={{ color: familyColor(selected.family) }}
              title="Scenario currently being read"
            >
              <span
                className="h-1.5 w-1.5 rounded-full"
                style={{ background: familyColor(selected.family) }}
                aria-hidden="true"
              />
              {prettyFamily(selected.family)}
            </span>
          )}
          <button
            type="button"
            onClick={toggleAsk}
            aria-expanded={askOpen}
            aria-controls="ai-reading-ask"
            title={"Ask the theory · press /"}
            className={cn(
              "inline-flex items-center gap-1.5 h-7 px-2 rounded-md text-[12px] font-semibold transition-colors",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent",
              askOpen
                ? "text-accent bg-accent-soft"
                : "text-muted hover:text-accent hover:bg-panel-elev",
            )}
          >
            <MessageCircleQuestion className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Ask</span>
            <ChevronDown
              className={cn("h-3 w-3 transition-transform", askOpen && "rotate-180")}
              aria-hidden="true"
            />
          </button>
        </div>
      </header>
      {/* Stays mounted (so a Q&A exchange survives close→reopen), animating
          height via grid-rows 0fr→1fr. While shut it's `inert` and QaPanel is
          told it's closed so it won't steal focus. */}
      <div
        id="ai-reading-ask"
        className={cn(
          "grid bg-bg transition-[grid-template-rows] duration-200 ease-out motion-reduce:transition-none",
          askOpen
            ? "grid-rows-[1fr] border-b border-border"
            : "grid-rows-[0fr] border-b border-transparent",
        )}
      >
        <div className="overflow-hidden" inert={!askOpen}>
          <ErrorBoundary context="Ask the theory">
            <QaPanel open={askOpen} />
          </ErrorBoundary>
        </div>
      </div>
      <ErrorBoundary context="AI Reading">
        <NarrationTabs scenario={selected} />
      </ErrorBoundary>
    </div>
  );
}
