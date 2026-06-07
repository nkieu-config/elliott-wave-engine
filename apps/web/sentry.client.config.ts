// Lazy + DSN-gated. Static-importing @sentry/nextjs pulls in @opentelemetry/*,
// which Next 15's chunker fails to vendor (`Cannot find module
// './vendor-chunks/@opentelemetry.js'` at `next start`).

export {};

const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;

if (dsn) {
  void import("@sentry/nextjs").then((Sentry) => {
    Sentry.init({
      dsn,
      tracesSampleRate: Number(process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE ?? 0.1),
      // Must be added explicitly or the replays* rates below are inert.
      integrations: [Sentry.replayIntegration()],
      replaysSessionSampleRate: 0,
      replaysOnErrorSampleRate: 1,
      environment: process.env.NEXT_PUBLIC_SENTRY_ENV ?? "development",
    });
  });
}
