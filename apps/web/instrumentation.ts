// Lazy + DSN-gated so empty-DSN builds carry no @opentelemetry/* chunks.

export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    await import("./sentry.server.config");
  } else if (process.env.NEXT_RUNTIME === "edge") {
    await import("./sentry.edge.config");
  }
}

export const onRequestError = async (...args: unknown[]) => {
  if (!process.env.SENTRY_DSN) return;
  const Sentry = (await import("@sentry/nextjs")) as unknown as {
    captureRequestError?: (...a: unknown[]) => unknown;
  };
  return Sentry.captureRequestError?.(...args);
};
