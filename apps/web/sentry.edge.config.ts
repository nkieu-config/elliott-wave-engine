// Sentry edge init — DSN-gated.
export {};

const dsn = process.env.SENTRY_DSN;
if (dsn) {
  void import("@sentry/nextjs").then((Sentry) => {
    Sentry.init({
      dsn,
      tracesSampleRate: Number(process.env.SENTRY_TRACES_SAMPLE_RATE ?? 0.1),
      environment: process.env.SENTRY_ENV ?? "development",
    });
  });
}
