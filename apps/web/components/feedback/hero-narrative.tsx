"use client";

import { AlertCircle, AlertTriangle, Info, RotateCw, SearchX, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/cn";
import { resolveHero, type HeroTone } from "@/lib/hero-state";
import type { SampleData } from "@/lib/types";

// resolveHero stays icon-free so it's node-testable.
const HERO_ICON: Record<string, typeof AlertCircle> = {
  "fetch-error": AlertCircle,
  "load-error": AlertCircle,
  "no-data": Info,
  "no-anchor": SearchX,
  "no-scenarios": AlertTriangle,
};

const TONE_ICON_COLOR: Record<HeroTone, string> = {
  danger: "text-down",
  warn: "text-warn",
  info: "text-info",
};

const TONE_TITLE_COLOR: Record<HeroTone, string> = {
  danger: "text-down",
  warn: "text-warn",
  info: "text-text",
};

// Per-session dismissals in sessionStorage, keyed by HeroState.key.
function useDismissed(): {
  isDismissed: (key: string) => boolean;
  dismiss: (key: string) => void;
} {
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  useEffect(() => {
    try {
      const raw = window.sessionStorage.getItem("ewl-hero-dismissed");
      if (raw) setDismissed(new Set(JSON.parse(raw) as string[]));
    } catch {
      /* private mode / disabled */
    }
  }, []);

  const dismiss = useCallback((key: string) => {
    setDismissed((prev) => {
      const next = new Set(prev);
      next.add(key);
      try {
        window.sessionStorage.setItem(
          "ewl-hero-dismissed",
          JSON.stringify([...next]),
        );
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  return {
    isDismissed: (key) => dismissed.has(key),
    dismiss,
  };
}

export function HeroNarrative({
  data,
  error = null,
}: {
  data: SampleData | undefined;
  /** Pipeline fetch failure — highest-priority banner; null when healthy. */
  error?: Error | null;
}) {
  const queryClient = useQueryClient();
  const { isDismissed, dismiss } = useDismissed();

  const retry = () => {
    void queryClient.refetchQueries({ queryKey: ["pipeline"] });
  };

  const hero = resolveHero(data, error);
  if (!hero) return null;
  if (isDismissed(hero.key)) return null;

  const Icon = HERO_ICON[hero.key];

  return (
    <div
      role="status"
      aria-live="polite"
      className="ewl-hero-narrative"
      data-tone={hero.tone}
    >
      <span
        className={cn(
          "grid place-items-center h-6 w-6 shrink-0 rounded-md",
          TONE_ICON_COLOR[hero.tone],
        )}
        aria-hidden="true"
      >
        <Icon className="h-4 w-4" />
      </span>
      <div className="min-w-0 flex-1">
        <div
          className={cn(
            "text-[14px] font-semibold leading-tight",
            TONE_TITLE_COLOR[hero.tone],
          )}
        >
          {hero.title}
        </div>
        <div className="text-[13px] text-muted mt-0.5 leading-relaxed">
          {hero.body}
        </div>
      </div>
      <div className="flex items-center gap-1 shrink-0">
        {hero.retry && (
          <button
            type="button"
            onClick={retry}
            className={cn(
              "inline-flex items-center gap-1.5 h-8 px-3 rounded-md text-[12px] font-semibold uppercase tracking-[0.08em] transition-colors",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent",
              hero.tone === "danger"
                ? "bg-down-soft text-down border border-down/30 hover:bg-down/15"
                : "bg-accent-soft text-accent-bright border border-border-glow hover:bg-accent/15",
            )}
          >
            <RotateCw className="h-3 w-3" />
            Retry
          </button>
        )}
        <button
          type="button"
          onClick={() => dismiss(hero.key)}
          aria-label="Dismiss this notice"
          title="Dismiss for this session"
          className="grid place-items-center w-8 h-8 rounded-md text-faint hover:text-text hover:bg-panel-elev focus:outline-none focus-visible:ring-2 focus-visible:ring-accent transition-colors"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
