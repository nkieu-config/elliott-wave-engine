import {
  Profiler,
  memo,
  useState,
  type ProfilerOnRenderCallback,
} from "react";
import { act, cleanup, render, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ReadingPane } from "@/components/analyst/reading-pane";
import { MODES } from "@/components/analyst/narration-modes";
import { useNarrationStream, type Mode, type ModeState } from "@/lib/hooks/use-narration-stream";

afterEach(cleanup);

const NOOP = () => {};
const MODES_BY_KEY = Object.fromEntries(MODES.map((m) => [m.key, m])) as Record<
  Mode,
  (typeof MODES)[number]
>;

const INITIAL: ModeState = {
  status: "streaming",
  text: "",
  tokens: 0,
  genMs: null,
  error: null,
  citations: [],
  cached: false,
  fellBack: false,
  modelId: null,
};
const freshStates = (): Record<Mode, ModeState> => ({
  explanation: { ...INITIAL },
  outlook: { ...INITIAL },
  risk: { ...INITIAL },
  differentiator: { ...INITIAL },
});

// "Run all": 4 modes stream concurrently; the active pane's slice changes on
// only 1 in 4 tokens. The other 3/4 re-render the parent but leave the active
// slice referentially identical — exactly where a stable startMode lets memo bail.
const TOTAL_TOKENS = 120;
const ACTIVE: Mode = "explanation";
const SEQUENCE: Mode[] = Array.from({ length: TOTAL_TOKENS }, (_, i) =>
  i % 4 === 0 ? ACTIVE : (["outlook", "risk", "differentiator"][i % 3] as Mode),
);
const ACTIVE_TOKENS = SEQUENCE.filter((m) => m === ACTIVE).length;

// ── Proof A — the fix at its source ─────────────────────────────────────────
describe("useNarrationStream startMode identity", () => {
  it("stays stable when config gets a fresh identity each render (pre-fix churn)", () => {
    const { result, rerender } = renderHook(
      ({ cfg }) => useNarrationStream("scn-1", cfg),
      { initialProps: { cfg: {} as Record<string, unknown> } },
    );
    const before = result.current.startMode;
    const beforeAll = result.current.startAll;

    // New object, same values — what nuqs hands back every render.
    rerender({ cfg: {} });
    rerender({ cfg: {} });

    expect(Object.is(result.current.startMode, before)).toBe(true);
    expect(Object.is(result.current.startAll, beforeAll)).toBe(true);
  });
});

// ── Proof B — the consequence through React.memo (deterministic counter) ─────
// Probe uses React.memo's default shallow compare — the same mechanism that
// wraps ReadingPane — so its render count is a faithful stand-in.
interface ProbeProps {
  state: ModeState;
  startMode: () => void;
  stopMode: () => void;
}
let probeRenders = 0;
const Probe = memo(function Probe(_props: ProbeProps) {
  probeRenders += 1;
  return null;
});

function ProbeHarness({
  unstable,
  apiRef,
}: {
  unstable: boolean;
  apiRef: { current: ((m: Mode) => void) | null };
}) {
  const [states, setStates] = useState<Record<Mode, ModeState>>(freshStates);
  apiRef.current = (mode) =>
    setStates((s) => ({
      ...s,
      [mode]: { ...s[mode], tokens: s[mode].tokens + 1, text: `${s[mode].text}x` },
    }));
  const startMode = unstable ? () => {} : NOOP;
  return <Probe state={states[ACTIVE]} startMode={startMode} stopMode={NOOP} />;
}

function countProbeRenders(unstable: boolean): number {
  probeRenders = 0;
  const apiRef: { current: ((m: Mode) => void) | null } = { current: null };
  render(<ProbeHarness unstable={unstable} apiRef={apiRef} />);
  for (const mode of SEQUENCE) act(() => apiRef.current!(mode));
  const count = probeRenders;
  cleanup();
  return count;
}

// ── Proof C — the real ReadingPane's render WORK via Profiler.actualDuration ─
function ReadingPaneHarness({
  unstable,
  apiRef,
  onRender,
}: {
  unstable: boolean;
  apiRef: { current: ((m: Mode) => void) | null };
  onRender: ProfilerOnRenderCallback;
}) {
  const [states, setStates] = useState<Record<Mode, ModeState>>(freshStates);
  apiRef.current = (mode) =>
    setStates((s) => ({
      ...s,
      [mode]: { ...s[mode], tokens: s[mode].tokens + 1, text: `${s[mode].text}x` },
    }));
  const startMode = unstable ? () => {} : NOOP;
  return (
    <Profiler id="reading-pane" onRender={onRender}>
      <ReadingPane
        meta={MODES_BY_KEY[ACTIVE]}
        state={states[ACTIVE]}
        startMode={startMode}
        stopMode={NOOP}
      />
    </Profiler>
  );
}

// Profiler.onRender fires once per parent commit regardless of memo bail, so a
// commit COUNT can't see the bail — but actualDuration is ~0 for a bailed
// subtree, so the summed render WORK does track it.
function profileReadingPane(unstable: boolean): { workMs: number } {
  const apiRef: { current: ((m: Mode) => void) | null } = { current: null };
  let workMs = 0;
  const onRender: ProfilerOnRenderCallback = (_id, _phase, actualDuration) => {
    workMs += actualDuration;
  };
  render(<ReadingPaneHarness unstable={unstable} apiRef={apiRef} onRender={onRender} />);
  for (const mode of SEQUENCE) act(() => apiRef.current!(mode));
  cleanup();
  return { workMs };
}

describe("ReadingPane re-render profile (Run all, 120 tokens across 4 modes)", () => {
  it("stable startMode lets React.memo skip the 3/4 background-only re-renders", () => {
    // B — deterministic render counts through memo.
    const unstableRenders = countProbeRenders(true);
    const stableRenders = countProbeRenders(false);

    // C — real ReadingPane render work.
    const unstableReal = profileReadingPane(true);
    const stableReal = profileReadingPane(false);

    const mount = 1;
    const reduction = 1 - stableRenders / unstableRenders;
    const workReduction = 1 - stableReal.workMs / unstableReal.workMs;

    // eslint-disable-next-line no-console
    console.log(
      `\n  ── ReadingPane re-render profile (${TOTAL_TOKENS} tokens, active="${ACTIVE}", ${ACTIVE_TOKENS} active-slice changes) ──\n` +
        `  [memo render count]   pre-fix: ${unstableRenders}   post-fix: ${stableRenders}   −${(reduction * 100).toFixed(1)}%\n` +
        `  [real ReadingPane work] pre-fix: ${unstableReal.workMs.toFixed(1)}ms   ` +
        `post-fix: ${stableReal.workMs.toFixed(1)}ms   −${(workReduction * 100).toFixed(1)}%\n`,
    );

    // Pre-fix: unstable startMode defeats memo → a render on every token.
    expect(unstableRenders).toBe(mount + TOTAL_TOKENS);
    // Post-fix: memo bails on background-only tokens → mount + active changes only.
    expect(stableRenders).toBe(mount + ACTIVE_TOKENS);
    expect(reduction).toBeGreaterThan(0.7);

    // Real component: post-fix performs far less render work (bailed subtrees
    // contribute ~0 actualDuration).
    expect(workReduction).toBeGreaterThan(0.5);
  });
});
