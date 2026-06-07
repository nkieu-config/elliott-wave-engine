"use client";

// Catches throws above the in-app ErrorBoundary; without it Next 15 white-screens
// with no Sentry capture. Replaces the whole document, so styles are inline.

import { useEffect } from "react";

export default function GlobalError({
  error,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Lazy + DSN-gated, mirroring error-boundary.tsx / providers.tsx.
    if (!process.env.NEXT_PUBLIC_SENTRY_DSN) return;
    void import("@sentry/nextjs")
      .then((Sentry) => Sentry.captureException(error, { tags: { boundary: "global" } }))
      .catch(() => {
        /* Sentry unavailable — the fallback still renders. */
      });
  }, [error]);

  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          minHeight: "100dvh",
          display: "grid",
          placeItems: "center",
          background: "#070a12",
          color: "#cbd5e1",
          fontFamily:
            '-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif',
        }}
      >
        <div style={{ textAlign: "center", padding: "2rem", maxWidth: "28rem" }}>
          <h1 style={{ fontSize: "1.125rem", fontWeight: 600, color: "#f1f5f9", margin: 0 }}>
            Something went wrong
          </h1>
          <p style={{ marginTop: "0.75rem", fontSize: "0.875rem", lineHeight: 1.6 }}>
            The app hit an unexpected error and couldn&apos;t recover. Reloading usually clears it.
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            style={{
              marginTop: "1.25rem",
              padding: "0.5rem 1rem",
              borderRadius: "0.375rem",
              border: "none",
              background: "#10b981",
              color: "#062018",
              fontSize: "0.8125rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Reload
          </button>
        </div>
      </body>
    </html>
  );
}
