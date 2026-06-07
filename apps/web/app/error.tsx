"use client";

// Route-segment error boundary — catches segment-render throws (the in-app
// ErrorBoundary covers the Workspace subtree).

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    if (!process.env.NEXT_PUBLIC_SENTRY_DSN) return;
    void import("@sentry/nextjs")
      .then((Sentry) => Sentry.captureException(error, { tags: { boundary: "route" } }))
      .catch(() => {
        /* Sentry unavailable — the fallback still renders. */
      });
  }, [error]);

  return (
    <main className="h-dvh w-screen grid place-items-center bg-bg text-text-dim">
      <div className="text-center px-8 max-w-md">
        <h1 className="text-lg font-semibold text-text">Something went wrong</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          The workspace hit an unexpected error. Try again — if it persists, reload the page.
        </p>
        <button
          type="button"
          onClick={reset}
          className="inline-block mt-5 px-4 py-2 rounded-md bg-accent text-[#062018] text-[13px] font-semibold hover:bg-accent-bright transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          Try again
        </button>
      </div>
    </main>
  );
}
