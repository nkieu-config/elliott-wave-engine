from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np

from analyst._fingerprint import PIPELINE_FINGERPRINT
from analyst.citations import PAGE_CITATION_RE, SENTENCE_SPLIT_RE, extract_pages
from analyst.client.base import LLMClient
from analyst.client.cache import DiskCache, build_cache_key
from analyst.client.gate import gate_narration_draft
from analyst.client.grounding import (
    find_fabricated_numbers,
    find_ungrounded_claims,
)
from analyst.diagnostics.bottleneck import diagnose_bottleneck
from analyst.diagnostics.confirmation import evaluate_confirmation
from analyst.diagnostics.decision import (
    compute_alternative_brief,
    compute_decision_summary,
)
from analyst.diagnostics.scenario_diff import diff_top_scenarios
from analyst.diagnostics.succession import compute_succession
from analyst.diagnostics.targets import compute_targets
from analyst.prompts import PROMPT_VERSION, build_prompt, build_repair_prompt
from analyst.prompts.qa import QA_SYSTEM_PROMPT, build_qa_prompt
from analyst.schemas.analysis import AnalysisResult
from analyst.schemas.citation import CitationRef, CitationReport
from analyst.schemas.narration import (
    citations_from_draft,
    narration_json_schema,
    parse_narration_draft,
)
from analyst.schemas.output import AnalysisOutput
from analyst.schemas.qa import QaOutput
from analyst.serialization.fallback import mode_fallback
from analyst.serialization.scenario import serialize_scenario
from analyst.taxonomy import ALL_SLOTS
from analyst.theory.chunker import Chunk
from analyst.theory.citation_map import (
    SLOT_CITATIONS,
    family_confirmation_pages,
    family_fib_flow_pages,
    family_invalidation_pages,
    family_succession_pages,
    pages_for_slots,
)
from analyst.theory.retriever import Retriever
from engine import Bar, ScaleMode, Scenario

_log = logging.getLogger(__name__)


class LLMUnavailableError(Exception):
    # Callers serve the deterministic fallback and must NOT cache it — the model
    # may recover; a cached fallback would pin the degraded read for that key.
    pass


DEFAULT_CACHE_DIR = Path(__file__).resolve().parent / ".cache"

_PROVENANCE = f"{PROMPT_VERSION} · {PIPELINE_FINGERPRINT[:8]}"

# Q&A tuning, calibrated on a 18 in-scope / 12 out-of-scope labelled set (incl.
# TA/trading hard negatives) over bge-base-en-v1.5. Top-1 cosine separated
# cleanly: in-scope min 0.607, out-of-scope max 0.546 (a "stop loss %" question).
# Re-run the calibration if the embedder or corpus changes (e.g. a Thai swap).
_QA_K = 5
# Below this top-1 cosine a no-chart question is off-topic. Set just inside the
# (0.546, 0.607] perfect-separation band, leaning low — a falsely-rejected real
# question is worse UX than a borderline one the LLM handles with a disclosure.
_QA_SCOPE_THRESHOLD = 0.56
# Per-chunk floor: a retrieved page below this (beyond the top hit) is dropped
# so it can't become citable noise. Relevant secondary pages bottom out ~0.55
# (a page below it can't even beat the best off-topic question), so 0.55 keeps
# them while trimming the tail.
_QA_CHUNK_FLOOR = 0.55
_QA_MIN_CHARS = 40
_QA_OUT_OF_SCOPE_MSG = (
    "That question is outside the Elliott Wave Lite theory this assistant covers."
)
_QA_FALLBACK_MSG = (
    "I couldn't produce a grounded answer to that question from the theory."
)


@dataclass
class Analyst:
    retriever: Retriever
    llm_client: LLMClient | None
    cache: DiskCache

    def compute_layer1(
        self,
        scenario: Scenario,
        bars: list[Bar],
        *,
        all_scenarios: list[Scenario] | None = None,
        scale_mode: ScaleMode = "linear",
    ) -> AnalysisResult:
        """Compute the deterministic Layer-1 analysis (bottleneck, confirmation, targets) — no LLM."""
        verbose = _verbose_components_for_scenario(scenario, bars)
        bottleneck = (
            diagnose_bottleneck(verbose, scenario.family)
            if _has_active_slots(verbose) else None
        )
        # Per-slot intermediates power 2nd/3rd weakest narration, not just bottleneck.
        score_intermediates = dict(verbose.get("intermediates", {}) or {})
        confirmation = evaluate_confirmation(scenario, bars, scale_mode)
        targets = compute_targets(scenario)
        succession = compute_succession(scenario)
        decision = compute_decision_summary(scenario, bars, targets)
        diffs = (
            tuple(diff_top_scenarios(all_scenarios)) if all_scenarios else ()
        )
        alternative = None
        if all_scenarios and len(all_scenarios) > 1:
            try:
                alt_sc = next(s for s in all_scenarios if s is not scenario)
            except StopIteration:
                alt_sc = None
            if alt_sc is not None:
                alt_targets = compute_targets(alt_sc)
                alternative = compute_alternative_brief(
                    scenario, alt_sc, bars, alt_targets,
                )
        return AnalysisResult(
            scenario_id=scenario.id,
            bottleneck=bottleneck,
            confirmation=confirmation,
            targets=targets,
            succession=succession,
            decision=decision,
            alternative=alternative,
            score_intermediates=score_intermediates,
            scenario_diffs=diffs,
        )

    def analyze(
        self,
        scenario: Scenario,
        bars: list[Bar],
        mode: str,
        *,
        all_scenarios: list[Scenario] | None = None,
        scale_mode: ScaleMode = "linear",
        rag_enabled: bool = True,
        layer1: AnalysisResult | None = None,
        force_refresh: bool = False,
    ) -> AnalysisOutput:
        """Produce a cached, gated LLM narration for a scenario on top of its Layer-1 analysis."""
        # force_refresh skips cache read but still writes back (per-section Regenerate).
        if layer1 is None:
            layer1 = self.compute_layer1(
                scenario, bars,
                all_scenarios=all_scenarios, scale_mode=scale_mode,
            )

        # Stable id keys one scenario to one cache entry; model_id fallback for stubs.
        model_id = None
        if self.llm_client is not None:
            model_id = getattr(self.llm_client, "cache_model_id", None) or getattr(
                self.llm_client, "model_id", None
            )
        # Decoding knobs in the key — sampling changes must invalidate cached narrations.
        temperature = getattr(self.llm_client, "temperature", None) if self.llm_client else None
        seed = getattr(self.llm_client, "seed", None) if self.llm_client else None
        cache_key = build_cache_key(
            scenario, mode=mode, prompt_version=PIPELINE_FINGERPRINT,
            model_id=model_id or "none", rag_enabled=rag_enabled,
            temperature=temperature, seed=seed,
        )
        cached = None if force_refresh else self.cache.get(cache_key)
        if cached is not None:
            narration_c, raw_cached, fell_back_c, report_c = _decode_cache_payload(
                cached
            )
            # Empty narration (legacy pre-gate-length-floor entry) → miss.
            if narration_c.strip():
                return AnalysisOutput(
                    scenario_id=scenario.id, mode=mode, layer1=layer1,
                    narration=narration_c,
                    citations=_extract_citations(narration_c),
                    citation_report=report_c,
                    model_id=model_id, prompt_version=_PROVENANCE, cached=True,
                    fell_back=fell_back_c, raw_narration=raw_cached,
                )

        if rag_enabled:
            target_pages = _retrieval_pages(
                scenario, mode, all_scenarios=all_scenarios,
            )
            chunks = self.retriever.by_pages(sorted(target_pages))
            # allowed_pages = pages actually returned (§5.6).
            theory_md = _format_chunks(chunks)
            allowed_pages = {c.page for c in chunks}
        else:
            chunks = []
            theory_md = "(theory retrieval disabled for ablation)"
            allowed_pages = set()
        layer1_md = serialize_scenario(scenario, layer1, mode)
        # Layer-1's own (p.N) citations must be in allowed_pages or echoes fail the gate.
        allowed_pages |= extract_pages(layer1_md)
        # Mode-aware so a differentiator/outlook gate failure doesn't surface bottleneck text.
        fallback_text = mode_fallback(mode, layer1)

        if self.llm_client is None:
            return AnalysisOutput(
                scenario_id=scenario.id, mode=mode, layer1=layer1,
                narration=fallback_text, citations=(),
                citation_report=CitationReport(),
                model_id=None, prompt_version=_PROVENANCE, cached=False,
                fell_back=True, raw_narration=None,
            )
        system_prompt, user_prompt = build_prompt(mode, layer1_md, theory_md)
        # Schema's page enum = dynamic allowed set, so disallowed citations are impossible.
        schema = narration_json_schema(allowed_pages)
        try:
            narration, draft, report, fell_back, raw = self._generate_gated(
                system_prompt=system_prompt, user_prompt=user_prompt, schema=schema,
                allowed_pages=allowed_pages, fallback_text=fallback_text,
                fab_corpus=layer1_md,
            )
        except LLMUnavailableError:
            # Model unavailable — serve the deterministic template, but DON'T cache
            # (gate-fallbacks below are cached; a transient LLM miss must not be).
            _log.warning("LLM unavailable for analyze(mode=%s); serving fallback", mode)
            return AnalysisOutput(
                scenario_id=scenario.id, mode=mode, layer1=layer1,
                narration=fallback_text, citations=(),
                citation_report=CitationReport(),
                model_id=model_id, prompt_version=_PROVENANCE, cached=False,
                fell_back=True, raw_narration=None,
            )
        # Cache on fallback too — re-renders must not re-hit the cloud for a deterministic template.
        self.cache.put(
            cache_key, _encode_cache_payload(narration, raw, report, fell_back),
        )
        citations = (
            citations_from_draft(draft)
            if draft is not None and not fell_back
            else ()
        )

        return AnalysisOutput(
            scenario_id=scenario.id, mode=mode, layer1=layer1,
            narration=narration, citations=citations,
            citation_report=report, fell_back=fell_back,
            model_id=model_id, prompt_version=_PROVENANCE,  # fallover-stable; avoids shared-state race
            cached=False, raw_narration=raw,
        )

    def _augment_grounding(self, draft, report):
        r = self.retriever
        if r.embedder is None or not r.chunks:
            return report
        page_to_row = {c.page: i for i, c in enumerate(r.chunks)}
        ungrounded = find_ungrounded_claims(
            draft, embedder=r.embedder,
            corpus_embeddings=r.embeddings, page_to_row=page_to_row,
        )
        if not ungrounded:
            return report
        return replace(report, ungrounded_citation_claims=ungrounded)

    def _generate_gated(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: dict,
        allowed_pages: Any,
        fallback_text: str,
        fab_corpus: str,
        min_chars: int | None = None,
        repair_mode: str = "analysis",
    ) -> tuple[str, Any, CitationReport, bool, str | None]:
        # Shared LLM→gate→grounding→one-repair policy for analyze() and
        # answer_question() so the two flows can't drift. fab_corpus="" disables
        # the number check (find_fabricated_numbers no-ops on empty input).
        gate_kw = {} if min_chars is None else {"min_chars": min_chars}

        def _run(prompt: str) -> tuple[str, Any, CitationReport, bool, str | None]:
            try:
                raw = self.llm_client.complete(
                    _chat_messages(system_prompt, prompt), format=schema,
                )
            except Exception as e:  # all providers down → let the caller fall back
                raise LLMUnavailableError(str(e)) from e
            draft = parse_narration_draft(raw)
            text, report, fell_back = gate_narration_draft(
                draft, allowed_pages=allowed_pages,
                layer1_fallback=fallback_text, **gate_kw,
            )
            if not fell_back:
                report = self._augment_grounding(draft, report)
                fabricated = find_fabricated_numbers(draft, layer1_md=fab_corpus)
                if fabricated:
                    report = replace(report, fabricated_number_claims=fabricated)
            return text, draft, report, fell_back, raw

        # Initial call: LLMUnavailableError propagates so the caller serves its fallback.
        text, draft, report, fell_back, raw = _run(user_prompt)
        if not (fell_back or report.has_soft_flags):
            return text, draft, report, fell_back, raw
        # One repair attempt; keep the original unless the repair was hard-clean
        # where the original wasn't (don't regress a passing read into a fallback).
        repair_user = build_repair_prompt(user_prompt, raw, report, mode=repair_mode)
        try:
            text2, draft2, report2, fell_back2, raw2 = _run(repair_user)
        except LLMUnavailableError:
            # Model died mid-flight — keep the gated original rather than fall back.
            return text, draft, report, fell_back, raw
        if fell_back2 and not fell_back:
            return text, draft, report, fell_back, raw
        return text2, draft2, report2, fell_back2, raw2

    def answer_question(
        self,
        question: str,
        *,
        scenario: Scenario | None = None,
        bars: list[Bar] | None = None,
        scale_mode: ScaleMode = "linear",
        layer1: AnalysisResult | None = None,
        k: int = _QA_K,
        force_refresh: bool = False,
    ) -> QaOutput:
        """Answer a free-form theory question via similarity retrieval + the gated LLM path."""
        # Q&A is similarity-retrieved (no fixed slot→page map) and optionally
        # scenario-aware. Reuses the analysis gate/grounding/repair path; only
        # retrieval and the out-of-scope short-circuit differ.
        if self.retriever.embedder is None:
            raise RuntimeError(
                "Q&A needs an embedder; enable ANALYST_QA=1 "
                "(install with `uv sync --extra grounding`)."
            )
        # Scenario-aware Q&A computes Layer-1 from the chart's bars — without
        # them it would silently score an empty series, so fail loud instead.
        if scenario is not None and layer1 is None and not bars:
            raise ValueError("scenario-aware Q&A needs bars (or a precomputed layer1)")
        q = question.strip()
        scored = self.retriever.by_similarity_scored(q, k) if q else []
        top_score = scored[0][1] if scored else 0.0
        # Keep the best hit plus only clearly-relevant others, so a marginal page
        # neither dilutes the prompt nor becomes a citable allowed page.
        kept = scored[:1] + [(c, s) for c, s in scored[1:] if s >= _QA_CHUNK_FLOOR]
        chunks = [c for c, _ in kept]
        retrieved_pages = tuple(c.page for c in chunks)

        # Scenario-aware: inject the chart's Layer-1 so data questions resolve.
        chart_md: str | None = None
        if scenario is not None:
            if layer1 is None:
                layer1 = self.compute_layer1(
                    scenario, bars or [], scale_mode=scale_mode,
                )
            chart_md = serialize_scenario(scenario, layer1, "qa")

        # No chart to lean on and weak theory match → refuse before the LLM call
        # rather than answer ungrounded.
        if scenario is None and top_score < _QA_SCOPE_THRESHOLD:
            return QaOutput(
                question=q, answer=_QA_OUT_OF_SCOPE_MSG, citations=(),
                retrieved_pages=retrieved_pages,
                citation_report=CitationReport(), out_of_scope=True,
            )

        theory_md = _format_chunks(chunks)
        allowed_pages = set(retrieved_pages)
        if chart_md:
            # Chart block's own (p.N) echoes must be citable or they fail the gate.
            allowed_pages |= extract_pages(chart_md)
        # Numbers may come from the chart OR a quoted theory figure (e.g. "200%"),
        # so both ground the fabrication check — chart-only false-flags a rule's
        # number stated as a data_observation. Bodies only: the "### p.N" headers
        # would otherwise launder a fabricated figure through a matching page number.
        theory_bodies = "\n".join(c.body for c in chunks)
        fab_corpus = f"{chart_md}\n{theory_bodies}" if chart_md else ""

        model_id = None
        if self.llm_client is not None:
            model_id = getattr(self.llm_client, "cache_model_id", None) or getattr(
                self.llm_client, "model_id", None
            )
        temperature = getattr(self.llm_client, "temperature", None) if self.llm_client else None
        seed = getattr(self.llm_client, "seed", None) if self.llm_client else None
        cache_key = _qa_cache_key(
            q, retrieved_pages, scenario, model_id or "none", temperature, seed,
        )
        cached = None if force_refresh else self.cache.get(cache_key)
        if cached is not None:
            answer_c, _raw_c, fell_back_c, report_c = _decode_cache_payload(cached)
            if answer_c.strip():
                return QaOutput(
                    question=q, answer=answer_c,
                    citations=_extract_citations(answer_c),
                    retrieved_pages=retrieved_pages, citation_report=report_c,
                    fell_back=fell_back_c, cached=True,
                    model_id=model_id,
                )

        if self.llm_client is None:
            return QaOutput(
                question=q, answer=_QA_FALLBACK_MSG, citations=(),
                retrieved_pages=retrieved_pages,
                citation_report=CitationReport(), fell_back=True,
            )

        schema = narration_json_schema(allowed_pages)
        user_prompt = build_qa_prompt(q, theory_md, chart_md)
        try:
            answer, draft, report, fell_back, raw = self._generate_gated(
                system_prompt=QA_SYSTEM_PROMPT, user_prompt=user_prompt, schema=schema,
                allowed_pages=allowed_pages, fallback_text=_QA_FALLBACK_MSG,
                fab_corpus=fab_corpus, min_chars=_QA_MIN_CHARS, repair_mode="qa",
            )
        except LLMUnavailableError:
            _log.warning("LLM unavailable for Q&A; serving fallback")
            return QaOutput(
                question=q, answer=_QA_FALLBACK_MSG, citations=(),
                retrieved_pages=retrieved_pages,
                citation_report=CitationReport(), fell_back=True,
            )

        # Don't cache a fallback: unlike analyze()'s deterministic template, the
        # Q&A fallback is a generic error — caching it would pin a transient LLM
        # miss as a permanent failure for that question.
        if not fell_back:
            self.cache.put(
                cache_key, _encode_cache_payload(answer, raw, report, fell_back),
            )
        citations = (
            citations_from_draft(draft)
            if draft is not None and not fell_back
            else ()
        )
        return QaOutput(
            question=q, answer=answer, citations=citations,
            retrieved_pages=retrieved_pages, citation_report=report,
            fell_back=fell_back, cached=False,
            model_id=model_id,  # fallover-stable local; avoids shared-state race
        )


def build_analyst(
    *,
    chunks: list[Chunk],
    embeddings: np.ndarray,
    llm_client: LLMClient | None,
    embedder: Any | None = None,
    cache_dir: Path = DEFAULT_CACHE_DIR,
) -> Analyst:
    """Assemble an Analyst from a theory corpus, an optional LLM, and an on-disk cache."""
    return Analyst(
        retriever=Retriever(chunks=chunks, embeddings=embeddings, embedder=embedder),
        llm_client=llm_client,
        cache=DiskCache(cache_dir),
    )


def _parse_chunks_jsonl(path: Path) -> list[dict]:
    import json

    chunks_raw: list[dict] = []
    skipped = 0
    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            chunks_raw.append(json.loads(line))
        except json.JSONDecodeError as e:
            skipped += 1
            _log.warning(
                "chunks.jsonl: skipping malformed line %d (%s): %s",
                lineno, e.msg, line[:80],
            )
    if not chunks_raw:
        raise RuntimeError(
            f"{path.name} yielded zero parsable chunks ({skipped} skipped) — "
            f"corpus is unusable; rebuild via analyst/theory/make_embeddings.py."
        )
    if skipped:
        _log.warning(
            "%s: loaded %d chunks, skipped %d malformed",
            path.name, len(chunks_raw), skipped,
        )
    return chunks_raw


def load_default_corpus() -> tuple[list[Chunk], np.ndarray]:
    """Read the prebuilt RAG corpus shipped under ``analyst/theory/data/``."""
    from analyst.theory.embedder import EMBED_DIM  # plain constant — no torch import

    data_dir = Path(__file__).resolve().parent / "theory" / "data"
    chunks_raw = _parse_chunks_jsonl(data_dir / "chunks.jsonl")
    chunks = [Chunk(**c) for c in chunks_raw]
    # allow_pickle=False + shape check: a stale corpus fails loud, not silent.
    embeddings = np.load(data_dir / "embeddings.npy", allow_pickle=False)
    if embeddings.ndim != 2 or embeddings.shape[1] != EMBED_DIM:
        raise ValueError(
            f"embeddings.npy shape {embeddings.shape} is not (*, {EMBED_DIM}); "
            "rebuild the corpus (analyst/theory/make_embeddings.py)"
        )
    return chunks, embeddings


def _has_active_slots(components: dict) -> bool:
    return any(k in components for k in ALL_SLOTS)


def _verbose_components_for_scenario(scenario: Scenario, bars: list[Bar]) -> dict:
    # Scale-independent (every slot is a ratio/log-CV), so no scale_mode needed.
    from engine import score_intermediates
    return score_intermediates(scenario, bars)


def _retrieval_pages(
    scenario: Scenario, mode: str,
    all_scenarios: list[Scenario] | None = None,
) -> set[int]:
    pages: set[int] = set()
    components = scenario.score_components or {}
    active_slots = [s for s in SLOT_CITATIONS if s in components]
    if mode == "explanation":
        # Family-resolved so a Sideway scenario doesn't get Trend pages.
        pages.update(pages_for_slots(active_slots, scenario.family))
    if mode == "slot_focus":
        # Top-3 weakest + family's invalidation pages.
        weakest = sorted(active_slots, key=lambda s: components[s])[:3]
        pages.update(pages_for_slots(weakest, scenario.family))
        pages.update(family_invalidation_pages(scenario.family))
    if mode == "differentiator":
        # Union top-3 families so competitors' Fibonacci pages are retrievable.
        families = {scenario.family}
        if all_scenarios:
            families.update(s.family for s in all_scenarios[:3])
        for fam in families:
            pages.update(pages_for_slots(active_slots, fam))
    if mode == "scenario_outlook":
        pages.update(family_confirmation_pages(scenario.family))
        pages.update(family_invalidation_pages(scenario.family))
        pages.update(family_fib_flow_pages(scenario.family))
        pages.update(family_succession_pages(scenario.family))
    return pages


def _format_chunks(chunks: list[Chunk]) -> str:
    return "\n\n".join(f"### p.{c.page}\n{c.body}" for c in chunks)


def _qa_cache_key(
    question: str,
    pages: tuple[int, ...],
    scenario: Scenario | None,
    model_id: str,
    temperature: float | None,
    seed: int | None,
) -> tuple:
    # Same question on different charts must not collide, so with a scenario we
    # reuse its content-derived hash and ride the question in `mode`.
    qhash = hashlib.sha256(question.encode()).hexdigest()[:16]
    if scenario is not None:
        return build_cache_key(
            scenario, mode=f"qa:{qhash}", prompt_version=PIPELINE_FINGERPRINT,
            model_id=model_id, rag_enabled=True,
            temperature=temperature, seed=seed,
        )
    return ("qa", qhash, tuple(sorted(pages)), model_id,
            PIPELINE_FINGERPRINT, temperature, seed)


def _chat_messages(system: str, user: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _encode_cache_payload(
    narration: str, raw: str | None, report: CitationReport, fell_back: bool,
) -> dict:
    return {
        "narration": narration,
        "raw": raw,
        "fell_back": fell_back,
        "report": report.to_dict(),
    }


def _decode_cache_payload(
    cached: Any,
) -> tuple[str, str | None, bool, CitationReport]:
    # Tolerates legacy bare-string format.
    if isinstance(cached, str):
        return cached, None, False, CitationReport()
    report = CitationReport.from_dict(cached.get("report", {}))
    return (
        cached.get("narration", ""),
        cached.get("raw"),
        bool(cached.get("fell_back", False)),
        report,
    )


def _extract_citations(text: str) -> tuple[CitationRef, ...]:
    # Expand (p.N-M) into one CitationRef per page with surrounding sentence.
    out: list[CitationRef] = []
    for sentence in SENTENCE_SPLIT_RE.split(text.strip()):
        if not sentence:
            continue
        for m in PAGE_CITATION_RE.finditer(sentence):
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else start
            for page in range(start, end + 1):
                out.append(CitationRef(page=page, claim_sentence=sentence))
    return tuple(out)
