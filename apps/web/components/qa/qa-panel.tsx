"use client";

import { AlertCircle, ArrowUp, Crosshair, Loader2, Telescope } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryStates } from "nuqs";
import { useAskPanel } from "@/lib/ask-store";
import { useSelectedScenario } from "@/lib/chart-store";
import { cn } from "@/lib/cn";
import { groupCitationsByPage } from "@/lib/citations";
import { configParsers } from "@/lib/config";
import { askQuestion, type QaResponse } from "@/lib/api";
import { SourceChip } from "@/components/analyst/source-chip";

// Double as a hint of what's answerable.
const EXAMPLES = [
  "When is s5-Shorter valid?",
  "Trend vs Sideway linkage?",
  "How deep can wave 4 retrace?",
] as const;

// Optionally grounds the answer in the selected scenario (chart-aware), else
// pure theory RAG.
export function QaPanel({ open = true }: { open?: boolean }) {
  const [config] = useQueryStates(configParsers);
  const [selectedId] = useSelectedScenario();
  // Grounding lives in the store so the follow-up link can preset it on.
  const grounded = useAskPanel((s) => s.grounded);
  const setGrounded = useAskPanel((s) => s.setGrounded);
  const focusNonce = useAskPanel((s) => s.focusNonce);
  const [question, setQuestion] = useState("");
  const [asked, setAsked] = useState<string | null>(null); // echoed transcript line
  const [result, setResult] = useState<QaResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // On touch, autofocus only after an explicit open (focusNonce bump) — a
  // mount-time focus would pop the keyboard. Desktop always focuses when open.
  const prevNonce = useRef(focusNonce);
  useEffect(() => {
    if (!open) return;
    const explicit = focusNonce !== prevNonce.current;
    prevNonce.current = focusNonce;
    const desktop =
      typeof window !== "undefined" && window.matchMedia("(min-width: 1024px)").matches;
    if (explicit || desktop) inputRef.current?.focus();
  }, [focusNonce, open]);

  const submit = useCallback(
    async (override?: string) => {
      const q = (override ?? question).trim();
      if (!q || loading) return;
      abortRef.current?.abort();
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      setLoading(true);
      setAsked(q);
      setError(null);
      setResult(null);
      try {
        const res = await askQuestion(
          {
            ...config,
            question: q,
            scenario_id: grounded && selectedId ? selectedId : undefined,
          },
          ctrl.signal,
        );
        setResult(res);
      } catch (e) {
        if (ctrl.signal.aborted) return;
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!ctrl.signal.aborted) setLoading(false);
      }
    },
    [question, loading, config, grounded, selectedId],
  );

  const canSend = question.trim().length > 0 && !loading;
  const showTranscript = asked != null && (loading || result != null || error != null);

  return (
    <div className="flex flex-col gap-3.5 px-5 py-4">
      {/* Caret sits flush to the px-5 gutter so it aligns with the echoed `›`
          in the transcript. */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void submit();
        }}
      >
        <div className="ewl-ask-line group flex items-center gap-2.5 h-9 border-b border-border-hi transition-colors focus-within:border-accent-bright">
          <span
            aria-hidden="true"
            className="font-mono text-[15px] leading-none text-muted transition-colors group-focus-within:text-accent-bright"
          >
            ›
          </span>
          <input
            id="qa-q"
            ref={inputRef}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="ask the Elliott Wave Lite theory…"
            maxLength={500}
            aria-label="Ask a theory question"
            autoComplete="off"
            className="flex-1 min-w-0 bg-transparent text-[14px] text-text placeholder:text-muted focus:outline-none"
          />
          {/* Grounding toggle rides the line (only with a scenario) so it costs
              no extra row. */}
          {selectedId && (
            <button
              type="button"
              onClick={() => setGrounded(!grounded)}
              data-active={grounded}
              aria-pressed={grounded}
              aria-label={
                grounded
                  ? "Answer grounded in the chart — click to use theory only"
                  : "Ground the answer in the chart you’re reading"
              }
              title="Ground the answer in the chart you’re reading"
              className="ewl-ask-scope"
            >
              <Crosshair className="h-3 w-3" aria-hidden="true" />
              Chart
            </button>
          )}
          {/* Send is secondary to Enter — brightens only when sendable. */}
          <button
            type="submit"
            disabled={!canSend}
            aria-label="Send question"
            className={cn(
              "ewl-ask-send grid place-items-center h-7 w-7 rounded-md shrink-0 transition-colors",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent",
              canSend
                ? "text-accent-bright hover:bg-panel-elev active:bg-accent-soft"
                : "text-faint cursor-not-allowed",
            )}
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <ArrowUp className="h-4 w-4" aria-hidden="true" />
            )}
          </button>
        </div>
      </form>

      {/* Starters (idle only) — outside the live region so they aren't announced. */}
      {!showTranscript && (
        <div role="group" aria-label="Example questions">
          <span className="block mb-1.5 text-[10px] font-mono uppercase tracking-[0.16em] text-faint">
            Try
          </span>
          <div className="flex flex-wrap gap-1.5">
            {EXAMPLES.map((q) => (
              <button
                key={q}
                type="button"
                className="ewl-pill"
                onClick={() => {
                  setQuestion(q);
                  void submit(q);
                }}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Live region so the loading→answer transition reaches screen readers. */}
      <div aria-live="polite">
        {showTranscript && (
          <div className="ewl-ask-thread">
            {/* Echoed prompt — the console line the readout answers. */}
            <p className="ewl-ask-echo">
              <span aria-hidden="true" className="caret">
                ›
              </span>
              <span className="text">{asked}</span>
            </p>

            {loading && <AnswerSkeleton />}

            {error && (
              <p className="flex items-start gap-2 text-[12px] text-down" role="alert">
                <AlertCircle className="h-3.5 w-3.5 mt-px shrink-0" aria-hidden="true" />
                {error.startsWith("qa 503")
                  ? "Q&A isn’t enabled on the server (set ANALYST_QA=1)."
                  : error}
              </p>
            )}

            {result && !loading && <Answer result={result} />}
          </div>
        )}
      </div>
    </div>
  );
}

function Answer({ result }: { result: QaResponse }) {
  if (result.out_of_scope) {
    return (
      <p className="flex items-start gap-2 text-[13px] text-muted italic leading-relaxed">
        <Telescope className="h-4 w-4 mt-px shrink-0 text-faint" aria-hidden="true" />
        That question is outside the Elliott Wave Lite theory this assistant
        covers. Try asking about wave rules, retracements, or scenario validity.
      </p>
    );
  }
  // Cited sentences surface as the chip tooltip (parity with reading-pane).
  const pages = groupCitationsByPage(result.citations);
  return (
    <div className="space-y-2.5">
      {/* 15px / 1.7 matches reading-pane body type, not a smaller chat reply. */}
      <p className="text-[15px] leading-[1.7] font-medium text-text-dim whitespace-pre-wrap">
        {result.answer}
      </p>
      {/* Provenance line reuses the reading-pane's Sources chips so Q&A and a
          system read carry the same citation skin. */}
      {(pages.length > 0 || result.fell_back || result.cached || result.model_id) && (
        <div className="ewl-read-meta">
          {pages.length > 0 && (
            <span className="flex flex-wrap items-center gap-1.5">
              <span className="uppercase tracking-[0.14em] text-muted">Sources</span>
              {pages.map(([p, sentences]) => (
                <SourceChip key={p} page={p} sentences={sentences} />
              ))}
            </span>
          )}
          {/* model_id rides the status word's tooltip — too technical for the
              always-visible line. */}
          <span
            className="ml-auto ewl-read-dateline shrink-0"
            title={result.model_id ? `Generated by ${result.model_id}` : undefined}
          >
            {result.fell_back ? (
              <span className="text-warn">ungrounded · rephrase</span>
            ) : result.cached ? (
              <span className="cached">cached</span>
            ) : (
              <span className="fresh">fresh</span>
            )}
          </span>
        </div>
      )}
    </div>
  );
}

// Mirrors the answer's shape: prose block + receipts row.
function AnswerSkeleton() {
  return (
    <div className="space-y-2.5" aria-label="Reading the theory…">
      <div className="space-y-1.5">
        <div className="ewl-skeleton h-3.5 w-full" />
        <div className="ewl-skeleton h-3.5 w-[92%]" />
        <div className="ewl-skeleton h-3.5 w-[68%]" />
      </div>
      <div className="flex gap-1.5">
        <div className="ewl-skeleton h-5 w-12 rounded" />
        <div className="ewl-skeleton h-5 w-12 rounded" />
      </div>
    </div>
  );
}
