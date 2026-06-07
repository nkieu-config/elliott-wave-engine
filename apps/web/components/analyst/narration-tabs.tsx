"use client";

import { AlertCircle, ArrowRight, MessageCircleQuestion, Square, Zap } from "lucide-react";
import { parseAsStringLiteral, useQueryState, useQueryStates } from "nuqs";
import { useCallback, useEffect, useRef } from "react";
import { useAskPanel } from "@/lib/ask-store";
import { cn } from "@/lib/cn";
import { configParsers } from "@/lib/config";
import { type CSSVars } from "@/lib/ui";
import { useNarrationStream, type Status } from "@/lib/hooks/use-narration-stream";
import type { Scenario } from "@/lib/types";
import { LearnBlock } from "@/components/analyst/learn-block";
import { MODES } from "@/components/analyst/narration-modes";
import { ReadingPane } from "@/components/analyst/reading-pane";

interface Props {
  scenario: Scenario | null;
}

// MODES is static — build the parser once.
const lensParser = parseAsStringLiteral(MODES.map((m) => m.key)).withDefault("explanation");

export function NarrationTabs({ scenario }: Props) {
  const [config] = useQueryStates(configParsers);
  const openAsk = useAskPanel((s) => s.openAsk);

  const { states, startMode, stopMode, stopAll, startAll } = useNarrationStream(
    scenario?.id ?? null,
    config,
  );

  // Lens in the URL (?lens=) so a read is deep-linkable. Others stream in the
  // background so switching is instant.
  const [active, setActive] = useQueryState("lens", lensParser);

  // Reset lens only on a real scenario→scenario switch — skip null→first so a
  // deep-linked ?lens= survives load.
  const lastScenarioId = useRef<string | null>(null);
  useEffect(() => {
    const id = scenario?.id ?? null;
    if (id !== null && lastScenarioId.current !== null && id !== lastScenarioId.current) {
      void setActive("explanation");
    }
    lastScenarioId.current = id;
  }, [scenario, setActive]);

  // Roving focus with arrows, jump with digit keys.
  const onTablistKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const idx = MODES.findIndex((m) => m.key === active);
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        setActive(MODES[(idx + 1) % MODES.length].key);
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        setActive(MODES[(idx - 1 + MODES.length) % MODES.length].key);
      } else if (e.key === "Home") {
        e.preventDefault();
        setActive(MODES[0].key);
      } else if (e.key === "End") {
        e.preventDefault();
        setActive(MODES[MODES.length - 1].key);
      } else if (/^[1-4]$/.test(e.key)) {
        e.preventDefault();
        setActive(MODES[Number(e.key) - 1].key);
      }
    },
    [active, setActive],
  );

  if (!scenario) {
    return (
      <div className="grid place-items-center min-h-[240px] px-5 py-8">
        <div className="w-full max-w-md space-y-3">
          <div className="ewl-section-head !mt-0">
            <span>Select a scenario to read</span>
          </div>
          <p className="text-[13px] text-muted leading-relaxed m-0">
            Each detected count is read four ways:
          </p>
          <ul className="grid grid-cols-2 gap-x-4 gap-y-2">
            {MODES.map((m) => (
              <li
                key={m.key}
                className="flex items-center gap-2 text-[13px] text-text-dim"
                style={{ "--lens": m.accent } as CSSVars}
              >
                <span className="ewl-read-kicker">
                  <span className="node" aria-hidden="true" />
                  <span className="idx">{m.num.padStart(2, "0")}</span>
                </span>
                <span>{m.tab}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  }

  const anyStreaming = MODES.some((m) => states[m.key].status === "streaming");
  const activeMeta = MODES.find((m) => m.key === active) ?? MODES[0];
  const activeState = states[active];

  return (
    <div className="flex flex-col">
      {/* Sticky (top-0) so it doesn't couple to the header's exact height. */}
      <div className="ewl-lens-bar">
        <div
          role="tablist"
          aria-label="Reading modes"
          onKeyDown={onTablistKeyDown}
          // flex-1 so the right-edge fade only bites into a tab once the row
          // actually overflows.
          className="ewl-lens-rail flex-1 flex items-center gap-1 min-w-0 overflow-x-auto"
        >
          {MODES.map((m) => {
            const st = states[m.key];
            const isActive = m.key === active;
            return (
              <button
                key={m.key}
                id={`lens-tab-${m.key}`}
                role="tab"
                aria-selected={isActive}
                aria-controls="lens-panel"
                tabIndex={isActive ? 0 : -1}
                onClick={() => void setActive(m.key)}
                title={m.title}
                data-active={isActive}
                className="ewl-lens focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                style={{ "--lens": m.accent } as CSSVars}
              >
                <StatusDot status={st.status} accent={m.accent} />
                <span className="ewl-lens-idx">{m.num.padStart(2, "0")}</span>
                <span>{m.tab}</span>
              </button>
            );
          })}
        </div>

        <div className="ml-auto flex items-center gap-1.5 shrink-0">
          <button
            type="button"
            onClick={anyStreaming ? stopAll : startAll}
            className={cn(
              "ewl-runall flex items-center gap-1.5 h-8 px-2.5 rounded-md text-[12px] font-semibold border transition-colors",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
              anyStreaming
                ? "border-border-hi text-text hover:bg-panel-elev"
                : "border-border text-accent-bright hover:bg-accent-soft hover:border-border-glow",
            )}
            aria-label={anyStreaming ? "Stop all reads" : "Run all reads"}
            title={anyStreaming ? "Stop every running read" : "Run all four reads in parallel"}
          >
            {anyStreaming ? (
              <>
                <Square className="h-3 w-3 fill-current" aria-hidden="true" />
                <span className="hidden sm:inline">Stop all</span>
              </>
            ) : (
              <>
                <Zap className="h-3 w-3 fill-current" aria-hidden="true" />
                <span className="hidden sm:inline">Run all</span>
              </>
            )}
          </button>
        </div>
      </div>

      <div
        id="lens-panel"
        role="tabpanel"
        aria-labelledby={`lens-tab-${active}`}
      >
        <ReadingPane
          meta={activeMeta}
          state={activeState}
          startMode={startMode}
          stopMode={stopMode}
        />
      </div>

      {/* Opens the Ask region grounded on this count. */}
      <div className="shrink-0 px-5 pt-1 pb-3">
        <button
          type="button"
          onClick={() => openAsk({ grounded: true })}
          className="group inline-flex items-center gap-1.5 text-[12px] font-semibold text-muted hover:text-accent transition-colors rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          <MessageCircleQuestion className="h-3.5 w-3.5" aria-hidden="true" />
          Ask a follow-up about this count
          <ArrowRight
            className="h-3 w-3 transition-transform group-hover:translate-x-0.5"
            aria-hidden="true"
          />
        </button>
      </div>

      <div className="shrink-0 px-5 py-3 border-t border-border">
        <LearnBlock family={scenario.family} />
      </div>
    </div>
  );
}

function StatusDot({ status, accent }: { status: Status; accent: string }) {
  if (status === "streaming") {
    return (
      <span
        className="h-2 w-2 rounded-full animate-pulse shrink-0"
        style={{ background: accent, boxShadow: `0 0 6px ${accent}` }}
        aria-hidden="true"
      />
    );
  }
  if (status === "done") {
    return <span className="h-2 w-2 rounded-full shrink-0" style={{ background: accent }} aria-hidden="true" />;
  }
  // error/cancelled differ by shape, not just hue — readable without colour.
  if (status === "error") {
    return <AlertCircle className="h-2.5 w-2.5 text-down shrink-0" aria-hidden="true" />;
  }
  if (status === "cancelled") {
    return <Square className="h-2 w-2 fill-current text-warn shrink-0" aria-hidden="true" />;
  }
  return (
    <span
      className="h-2 w-2 rounded-full border border-border-hi shrink-0"
      aria-hidden="true"
    />
  );
}

