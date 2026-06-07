"use client";

import * as React from "react";
import { ErrorFallback } from "@/components/feedback/error-fallback";

// Lazy + DSN-gated: avoid static-importing @sentry/nextjs so DSN-less builds
// don't pull in @opentelemetry/* chunks (Next 15's chunker mis-vendors them).
async function captureError(error: Error, info: React.ErrorInfo, context?: string) {
  if (!process.env.NEXT_PUBLIC_SENTRY_DSN) return;
  try {
    const Sentry = await import("@sentry/nextjs");
    Sentry.captureException(error, {
      tags: context ? { boundary: context } : undefined,
      extra: { componentStack: info.componentStack },
    });
  } catch {
    // Sentry unavailable — the boundary still shows the fallback.
  }
}

interface State {
  error: Error | null;
}

interface Props {
  children: React.ReactNode;
  /** Region label for the fallback title and Sentry tags. */
  context?: string;
  /** Tight in-panel layout; defaults true when `context` is set. */
  compact?: boolean;
}

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    void captureError(error, info, this.props.context);
  }

  reset = () => this.setState({ error: null });

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;

    const compact = this.props.compact ?? this.props.context !== undefined;
    return (
      <ErrorFallback
        error={error}
        reset={this.reset}
        context={this.props.context}
        compact={compact}
      />
    );
  }
}
