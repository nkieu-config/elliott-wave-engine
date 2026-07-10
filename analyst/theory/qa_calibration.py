"""Calibrate the Q&A scope threshold (τ) and per-chunk floor against the real
embedder + corpus. Dev tool, not CI — needs the grounding extra (torch).

Run after any embedder/corpus change (e.g. a Thai/multilingual swap):
    uv run python -m analyst.theory.qa_calibration

It prints top-1 score distributions for a labelled in/out-of-scope set and the
perfect-separation band; pick τ inside that band (lean low) and set the floor
just below where relevant secondary pages bottom out.
"""

from __future__ import annotations

# Hard negatives are deliberately finance/TA-flavoured (not pure off-topic) —
# those are the realistic false-accepts a naive threshold lets through.
IN_SCOPE: tuple[str, ...] = (
    "When is wave 5 called s5-Shorter?",
    "What is the difference between Trend linkage and Sideway linkage?",
    "What are the main rules of a 5-Wave Trend?",
    "How is wave 3 length constrained relative to wave 1 and wave 5?",
    "What is the Contract sideways pattern?",
    "How do I measure degree using the Gann Box?",
    "What confirms that a 5-Wave Trend is complete?",
    "How deeply can wave 4 retrace into wave 1 territory?",
    "What are the rules of a 3-Wave structure?",
    "When does a Sideway linkage become an Extend?",
    "Which Fibonacci levels are used for a 3-Wave target?",
    "What is the Push and Pull concept?",
    "How do odd and even numbered waves relate to Push and Pull?",
    "What is the s2-Longer concept in a 3-Wave?",
    "How do I choose a starting point for counting waves?",
    "Can a 5-Wave Sideway appear as a sub-wave inside another pattern?",
    "What is Top-Down analysis in wave counting?",
    "What is the minimum size for a Trend linkage in time and price?",
)
OUT_OF_SCOPE: tuple[str, ...] = (
    "What is the RSI indicator?",
    "Should I buy Tesla stock right now?",
    "What is a good stop loss percentage?",
    "How does a MACD crossover work?",
    "What is the P/E ratio of Apple?",
    "How do I cook fried rice?",
    "What is the capital of France?",
    "Explain how Bitcoin mining works.",
    "What time does the US stock market open?",
    "What is dollar cost averaging?",
    "How do candlestick patterns like the doji work?",
    "Who is Warren Buffett?",
)


def main() -> None:
    from analyst.orchestrator import (
        build_analyst,
        load_default_corpus,
    )
    from analyst.theory.embedder import Embedder

    chunks, emb = load_default_corpus()
    r = build_analyst(
        chunks=chunks, embeddings=emb, llm_client=None, embedder=Embedder(),
    ).retriever

    def top1(qs: tuple[str, ...]) -> list[float]:
        return sorted(r.by_similarity_scored(q, k=1)[0][1] for q in qs)

    ins, outs = top1(IN_SCOPE), top1(OUT_OF_SCOPE)
    print(f"in-scope  top1: min={ins[0]:.3f} med={ins[len(ins)//2]:.3f} max={ins[-1]:.3f}")
    print(f"out-scope top1: min={outs[0]:.3f} med={outs[len(outs)//2]:.3f} max={outs[-1]:.3f}")
    band = "EMPTY (overlap!)" if outs[-1] >= ins[0] else f"({outs[-1]:.3f}, {ins[0]:.3f}]"
    print(f"perfect-separation band for τ: {band}")
    for tau in (0.50, 0.52, 0.54, 0.56, 0.58, 0.60):
        ina = sum(v >= tau for v in ins)
        outr = sum(v < tau for v in outs)
        print(f"  τ={tau:.2f}: in accepted {ina}/{len(ins)}  out rejected {outr}/{len(outs)}")


if __name__ == "__main__":
    main()
