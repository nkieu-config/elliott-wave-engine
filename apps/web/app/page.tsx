import { Suspense } from "react";
import { ErrorBoundary } from "@/components/feedback/error-boundary";
import { KpiRow } from "@/components/layout/kpi-row";
import { MobileToolbar } from "@/components/layout/mobile-toolbar";
import { Workspace } from "@/components/layout/workspace";
import { AskHotkeys } from "@/components/qa/ask-hotkeys";

// nuqs useSearchParams() fails Next 15's static generator; page is data-live anyway.
export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <main
      id="main"
      className="h-dvh w-screen flex flex-col overflow-hidden"
      aria-label="Elliott Wave Lab"
    >
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-4 focus:py-2 focus:rounded-md focus:bg-accent focus:text-[#062018] focus:text-xs focus:font-semibold focus:shadow-lg"
      >
        Skip to main content
      </a>
      {/* Sole page heading — the visible wordmarks are plain spans. */}
      <h1 className="sr-only">Elliott Wave Lab</h1>
      <AskHotkeys />
      <MobileToolbar />
      <KpiRow />
      <ErrorBoundary>
        <Suspense fallback={<ShellSkeleton />}>
          <Workspace />
        </Suspense>
      </ErrorBoundary>
      <DisclaimerBar />
    </main>
  );
}

function ShellSkeleton() {
  return (
    <div className="flex-1 flex min-h-0">
      <div className="hidden lg:flex flex-col w-72 shrink-0 border-r border-border ewl-surface-sidebar p-4 gap-4">
        <div className="ewl-skeleton h-3 w-24" />
        <div className="space-y-2.5">
          <div className="ewl-skeleton h-8" />
          <div className="ewl-skeleton h-8" />
          <div className="ewl-skeleton h-8" />
        </div>
      </div>
      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex gap-2 px-4 py-2.5 border-b border-border ewl-surface-panel overflow-hidden">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="ewl-skeleton h-6 w-24 rounded-full" />
          ))}
        </div>
        <div className="flex-1 ewl-skeleton m-3" />
      </div>
      <div className="hidden lg:flex flex-col w-80 shrink-0 border-l border-border ewl-surface-panel p-4 gap-3">
        <div className="ewl-skeleton h-3 w-20" />
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="ewl-skeleton h-12" />
        ))}
      </div>
    </div>
  );
}

// Persistent, all-viewport disclaimer — chart-only (phone) users must see it too.
function DisclaimerBar() {
  return (
    <footer className="shrink-0 border-t border-border bg-panel px-4 py-1 text-center">
      <p className="m-0 text-[10px] leading-tight text-faint">
        <span aria-hidden="true">⚠ </span>
        For educational and research purposes only — not financial advice. Wave counts are
        algorithmic hypotheses, not a recommendation to buy or sell any asset.
      </p>
    </footer>
  );
}
