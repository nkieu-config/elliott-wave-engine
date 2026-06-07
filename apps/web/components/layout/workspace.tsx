"use client";

import { useDesktop, useTablet } from "@/lib/hooks/use-media-query";
import { ChartShell } from "@/components/chart/chart-shell";
import { ErrorBoundary } from "@/components/feedback/error-boundary";
import {
  ResizableWorkspace,
  TabletWorkspace,
} from "@/components/layout/resizable-workspace";

// Mounts exactly ONE layout per viewport — CSS display:none would keep both
// trees alive, spinning up two lightweight-charts instances (one in a 0×0
// container burning CPU). Both hooks return false during SSR (phone branch
// first), so server and first client render agree — no hydration mismatch.
export function Workspace() {
  const isDesktop = useDesktop();
  const isTablet = useTablet();
  return (
    <div id="main-content" className="flex-1 flex min-h-0">
      {isDesktop ? (
        <ResizableWorkspace />
      ) : isTablet ? (
        // Tablet: chart + scenarios; Lab Notebook stays a MobileToolbar drawer.
        <ErrorBoundary context="Workspace">
          <TabletWorkspace />
        </ErrorBoundary>
      ) : (
        <div className="flex-1 flex min-h-0">
          {/* Phone: chart only — sidebar + scenarios live in the
              MobileToolbar drawers. */}
          <ErrorBoundary context="Chart">
            <ChartShell />
          </ErrorBoundary>
        </div>
      )}
    </div>
  );
}
