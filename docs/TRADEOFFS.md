# Design Tradeoffs & Known Limitations

Choices made deliberately, and the costs that come with them — documented so the next
reader (or the author, six months on) doesn't rediscover them the hard way.

> For how the system works, see [ARCHITECTURE.md](ARCHITECTURE.md). This page is the
> companion: *why* it works that way, and where the edges are.

## Deliberate tradeoffs

**Auditability over end-to-end learning.** The count is produced by rules, not a model,
so it is fully inspectable — but the LLM can never *improve* the count, only explain it.
A neural counter might read ambiguous charts better; it would forfeit the per-rule
pass/fail trail that is this project's whole point.

**The beam dedup key is intentionally coarse.** Two structurally distinct counts that
score identically are collapsed to one representative. Refining the key to keep both was
tried and measured: it saturates the 500-wide beam immediately, and score-based
truncation then drops good-but-incomplete counts (one case fell from 43 scenarios to 3).
The real limit is that scoring can't rank score-tied structural variants — a
scoring-model question, not a dedup one. The coarseness is load-bearing.

**Single-process caches.** The parquet, LLM-response, and wave-count caches all live
in-process — simple and correct for one worker, which the deployment pins. Multi-worker
scaling needs a shared store (Redis); the seams are isolated behind interfaces for that.

**yfinance as the sole data source.** An unofficial, best-effort API — pragmatic and
key-free for a demo. It's hidden behind a `BarSource` Protocol so a licensed feed can
replace it without touching the engine.

## Known limitations

**"Every claim cites theory" is a structural guarantee, not a semantic one.** Cited
pages are constrained to a per-request whitelist of actually-retrieved pages (an enum at
decode time plus a gate re-check), so no claim can cite a page that wasn't fetched.
Whether that page's *content* actually supports the claim is checked only by an opt-in
advisory embedding pass — off in the default deployment. The count is fully verifiable;
the narration's grounding is best-effort.

**Theory provenance.** This implements a specific (Thai-sourced) Elliott Wave variant. A
few rule boundaries — strict vs inclusive length comparisons, a link-wave time gate —
are interpretation calls that await confirmation against the original text before being
treated as settled.

**Concurrency ceiling.** The synchronous LLM call runs behind `asyncio.to_thread` with
no global request deadline, so a burst of slow cloud calls can saturate the thread pool.
Fine at demo scale; production load would want a bounded executor and an overall timeout.
