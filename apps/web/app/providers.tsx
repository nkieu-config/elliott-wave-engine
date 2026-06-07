"use client";

// Side-effect import runs the DSN-gated Sentry.init(): Next 15.1 has no client
// instrumentation hook, so without it Sentry never inits and captureException
// below is a no-op. Still DSN-gated, so a no-DSN build pulls in no chunks.
import "@/sentry.client.config";

import { QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Provider as TooltipProvider } from "@radix-ui/react-tooltip";
import { NuqsAdapter } from "nuqs/adapters/next/app";
import * as React from "react";
import { Toaster, toast } from "sonner";
import { LocaleProvider } from "@/lib/locale";

// Stable Sonner ids — successive calls update the same slot, not stack.
const TOAST_QUERY_ERROR = "ewl-query-error";
const TOAST_UNHANDLED = "ewl-unhandled";

export function Providers({
  children,
  locale,
}: {
  children: React.ReactNode;
  locale: string;
}) {
  const [queryClient] = React.useState(
    () =>
      new QueryClient({
        queryCache: new QueryCache({
          onError: (error, query) => {
            // Suppress on background refetches (cached data present) — the hero
            // banner already covers it. New failures always toast.
            if (query.state.data !== undefined) return;
            const msg = error instanceof Error ? error.message : "Unknown error";
            toast.error(`Couldn’t load pipeline: ${msg}`, {
              id: TOAST_QUERY_ERROR,
              duration: 6000,
            });
          },
        }),
        defaultOptions: {
          queries: {
            refetchOnWindowFocus: false,
            staleTime: 60 * 1000,
            retry: 1,
          },
        },
      }),
  );

  // Catch promise rejections that escape the React tree (fire-and-forget
  // fetches, SSE throws) — otherwise prod users see nothing.
  React.useEffect(() => {
    const onUnhandled = (e: PromiseRejectionEvent) => {
      const reason = e.reason;
      const msg = reason instanceof Error ? reason.message : String(reason);
      toast.error(`Background error: ${msg}`, {
        id: TOAST_UNHANDLED,
        duration: 5000,
      });
      // DSN-gated lazy import — same pattern as ErrorBoundary's captureError.
      if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
        void import("@sentry/nextjs")
          .then((Sentry) => {
            Sentry.captureException(reason instanceof Error ? reason : new Error(msg), {
              tags: { source: "unhandledrejection" },
            });
          })
          .catch(() => {
            // Sentry unavailable — toast still fired.
          });
      }
    };
    window.addEventListener("unhandledrejection", onUnhandled);
    return () => window.removeEventListener("unhandledrejection", onUnhandled);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      {/* Single app-wide Tooltip.Provider — per-instance providers broke the
          shared skip-delay across tooltips. */}
      <TooltipProvider delayDuration={150} skipDelayDuration={300}>
        <NuqsAdapter>
          <LocaleProvider locale={locale}>{children}</LocaleProvider>
        </NuqsAdapter>
      </TooltipProvider>
      <Toaster
        position="bottom-right"
        theme="dark"
        // Bottom inset clears the mobile gesture bar.
        offset={{ bottom: "24px", right: "16px" }}
        toastOptions={{
          style: {
            background: "var(--color-panel)",
            border: "1px solid var(--color-border-hi)",
            color: "var(--color-text)",
            fontFamily: "var(--font-sans)",
          },
          className: "ewl-toast",
        }}
      />
    </QueryClientProvider>
  );
}
