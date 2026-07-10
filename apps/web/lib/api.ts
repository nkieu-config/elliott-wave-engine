import { parseSSE, type SSEMessage } from "./sse";
import type { FamilyEducation, Layer1Result, SampleData, ScaleMode } from "./types";
import type { CommitmentCurve, Period, Timeframe } from "./config";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
// Versioned business endpoints; ops probes (/api/health, /api/ready) stay unversioned.
const API_V1 = `${API_URL}/api/v1`;

export interface PipelineConfig {
  symbol?: string;
  period?: Period;
  timeframe?: Timeframe;
  scale_mode?: ScaleMode;
  atr_period?: number;
  atr_multiplier?: number;
  atr_floor?: number;
  min_bars_between?: number;
  k_sigma?: number;
  log_tol_fib?: number;
  pull_depth_lo?: number;
  pull_depth_hi?: number;
  pull_depth_tol?: number;
  pivot_window?: number;
  commitment_curve?: CommitmentCurve;
}

export async function fetchPipeline(
  config: PipelineConfig = {},
  signal?: AbortSignal,
): Promise<SampleData> {
  const res = await fetch(`${API_V1}/pipeline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
    signal,
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`pipeline ${res.status}: ${body || res.statusText}`);
  }
  return (await res.json()) as SampleData;
}

export interface Layer1Request extends PipelineConfig {
  scenario_id: string;
}

// Server re-runs the pipeline to resolve scenario_id, so callers must pass the
// exact config that produced the id or get a 404.
export async function fetchLayer1(
  req: Layer1Request,
  signal?: AbortSignal,
): Promise<Layer1Result> {
  const res = await fetch(`${API_V1}/scenario/layer1`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    signal,
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`layer1 ${res.status}: ${body || res.statusText}`);
  }
  return (await res.json()) as Layer1Result;
}

export async function fetchEducation(
  family: string,
  signal?: AbortSignal,
): Promise<FamilyEducation> {
  const res = await fetch(
    `${API_V1}/scenario/education?family=${encodeURIComponent(family)}`,
    { signal, cache: "force-cache" },
  );
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`education ${res.status}: ${body || res.statusText}`);
  }
  return (await res.json()) as FamilyEducation;
}

export interface QaCitation {
  page: number;
  claim_sentence: string;
}

export interface QaResponse {
  question: string;
  answer: string;
  citations: QaCitation[];
  retrieved_pages: number[];
  out_of_scope: boolean;
  fell_back: boolean;
  cached: boolean;
  model_id: string | null;
}

export interface QaChartContext extends PipelineConfig {
  scenario_id: string;
}

export interface QaRequest {
  question: string;
  // Omit for theory-only Q&A; set for chart-aware (server rebuilds the scenario).
  chart?: QaChartContext;
  force_refresh?: boolean;
}

export async function askQuestion(
  req: QaRequest,
  signal?: AbortSignal,
): Promise<QaResponse> {
  const res = await fetch(`${API_V1}/qa`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    signal,
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`qa ${res.status}: ${body || res.statusText}`);
  }
  return (await res.json()) as QaResponse;
}

export type AnalystMode = "explanation" | "outlook" | "risk" | "differentiator";

export interface AnalystStreamRequest extends PipelineConfig {
  scenario_id: string;
  mode: AnalystMode;
  rate_tps?: number;
  force_refresh?: boolean;
}

// POST + SSE (not EventSource — we need a request body). Throws on non-2xx
// before the first frame so callers surface it instead of a silent end.
export async function* streamAnalyst(
  req: AnalystStreamRequest,
  signal?: AbortSignal,
): AsyncGenerator<SSEMessage> {
  const res = await fetch(`${API_V1}/analyst/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(req),
    signal,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${body || res.statusText}`);
  }
  yield* parseSSE(res, signal);
}
