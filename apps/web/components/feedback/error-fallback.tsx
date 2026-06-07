"use client";

import { AlertTriangle, ClipboardCopy, RefreshCw, RotateCw } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/cn";
import { buildErrorReport } from "@/lib/error-report";
import { TOAST_DURATION } from "@/lib/ui";

export function ErrorFallback({
  error,
  reset,
  context,
  compact = false,
}: {
  error: Error;
  reset: () => void;
  /** Region label — surfaces in title and copy-paste payload. */
  context?: string;
  /** Tight layout for in-panel failures; page-level boundary stays spacious. */
  compact?: boolean;
}) {
  const region = context ?? "App";

  const copyDetails = () => {
    const details = buildErrorReport(region, error, {
      href: typeof window !== "undefined" ? window.location.href : "(SSR)",
      ua: typeof navigator !== "undefined" ? navigator.userAgent : "(SSR)",
    });
    if (typeof navigator === "undefined" || !navigator.clipboard) {
      toast.error("Clipboard unavailable in this browser");
      return;
    }
    navigator.clipboard.writeText(details).then(
      () => toast.success("Error details copied", { duration: TOAST_DURATION }),
      () => toast.error("Couldn’t copy — clipboard blocked"),
    );
  };

  const reload = () => {
    if (typeof window !== "undefined") window.location.reload();
  };

  return (
    <div
      role="alert"
      className={cn(
        "grid place-items-center h-full bg-bg",
        compact ? "p-4" : "p-8",
      )}
    >
      <div
        className={cn(
          "text-center space-y-3",
          compact ? "max-w-sm" : "max-w-md space-y-4",
        )}
      >
        <span
          className={cn(
            "mx-auto grid place-items-center rounded-lg border border-down/40 bg-down/10 text-down",
            compact ? "h-10 w-10" : "h-14 w-14",
          )}
        >
          <AlertTriangle className={compact ? "h-5 w-5" : "h-7 w-7"} aria-hidden="true" />
        </span>
        <h2
          className={cn(
            "font-semibold text-text",
            compact ? "text-sm" : "text-base",
          )}
        >
          {region} hit an error
        </h2>
        <p
          className={cn(
            "text-text-dim",
            compact ? "text-[13px]" : "text-sm",
          )}
        >
          Something inside <span className="font-medium">{region}</span> stopped
          working. Try the action below — your settings and chart state are safe.
        </p>
        <details
          className={cn(
            "text-left rounded-md bg-panel border border-border overflow-hidden",
            compact ? "text-[12px]" : "text-[13px]",
          )}
        >
          <summary
            className={cn(
              "cursor-pointer select-none px-3 py-1.5 text-muted font-medium hover:bg-panel-elev/50",
            )}
          >
            Show details
          </summary>
          <pre
            className={cn(
              "ewl-num text-down whitespace-pre-wrap break-all px-3 py-2 max-h-32 overflow-auto overscroll-contain border-t border-border",
            )}
          >
            {error.message}
          </pre>
        </details>
        <div className="flex flex-wrap items-center justify-center gap-2">
          <button
            type="button"
            onClick={reset}
            className={cn(
              "inline-flex items-center gap-1.5 h-9 px-3.5 rounded-md text-xs font-semibold transition-colors",
              "border border-border-glow bg-accent-soft text-accent-bright",
              "hover:bg-accent/20",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent",
            )}
          >
            <RotateCw className="h-3.5 w-3.5" aria-hidden="true" />
            Try again
          </button>
          <button
            type="button"
            onClick={reload}
            className={cn(
              "inline-flex items-center gap-1.5 h-9 px-3 rounded-md text-xs font-medium transition-colors",
              "border border-border bg-panel text-text-dim",
              "hover:bg-panel-elev hover:text-text",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent",
            )}
          >
            <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
            Reload page
          </button>
          <button
            type="button"
            onClick={copyDetails}
            className={cn(
              "inline-flex items-center gap-1.5 h-9 px-3 rounded-md text-xs font-medium transition-colors",
              "border border-transparent text-muted",
              "hover:text-text hover:bg-panel-elev",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent",
            )}
          >
            <ClipboardCopy className="h-3.5 w-3.5" aria-hidden="true" />
            Copy details
          </button>
        </div>
      </div>
    </div>
  );
}
