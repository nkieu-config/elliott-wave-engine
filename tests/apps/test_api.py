"""FastAPI endpoint tests (TestClient) for apps/api: fast contract surface, the
SSE analyst stream contract (seams mocked, no LLM), and a slow end-to-end
roundtrip pipeline → top scenario id → layer1.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from analyst.schemas.citation import CitationRef
from apps.api import pipeline_ops
from apps.api.main import app
from apps.api.schemas_responses import Layer1Response, PipelineResponse
from apps.api.services import analyst_service

# Not a context manager on purpose: skips the lifespan prewarm (heavy LLM load).
# These tests mock the analyst seams and use the endpoints' lazy-load path.
client = TestClient(app)

CFG = {"symbol": "DDOG", "period": "max", "timeframe": "week", "scale_mode": "linear"}


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready_not_prewarmed(monkeypatch):
    # Cold instance: readiness gates traffic with 503 until the singleton warms.
    monkeypatch.setattr(analyst_service, "is_prewarmed", lambda: False)
    monkeypatch.setattr(analyst_service, "qa_enabled_setting", lambda: False)
    r = client.get("/api/ready")
    assert r.status_code == 503
    body = r.json()
    assert body == {
        "status": "not_ready",
        "analyst_prewarmed": False,
        "qa_enabled": False,
    }


def test_ready_prewarmed(monkeypatch):
    monkeypatch.setattr(analyst_service, "is_prewarmed", lambda: True)
    monkeypatch.setattr(analyst_service, "qa_enabled_setting", lambda: True)
    r = client.get("/api/ready")
    assert r.status_code == 200
    body = r.json()
    assert body == {
        "status": "ready",
        "analyst_prewarmed": True,
        "qa_enabled": True,
    }


def test_mode_map_covers_every_wire_mode():
    # Two sources of truth: a mode in one but not the other 500s at request time.
    from typing import get_args

    from apps.api.routers.analyst import _MODE_TO_ANALYST
    from apps.api.schemas import AnalystMode

    assert set(_MODE_TO_ANALYST) == set(get_args(AnalystMode))


def test_pull_depth_validation_rejected():
    r = client.post("/api/v1/pipeline", json={**CFG, "pull_depth_lo": 0.6, "pull_depth_hi": 0.4})
    assert r.status_code == 422


@pytest.mark.parametrize(
    "override",
    [
        {"atr_period": 3},          # < ge=4
        {"atr_period": 61},         # > le=60
        {"atr_multiplier": 0.4},    # < ge=0.5
        {"atr_multiplier": 6.1},    # > le=6.0
        {"atr_floor": -0.01},       # < ge=0
        {"atr_floor": 0.31},        # > le=0.3
        {"min_bars_between": 0},    # < ge=1
        {"min_bars_between": 13},   # > le=12
        {"k_sigma": 0.05},          # < ge=0.1
        {"k_sigma": 1.6},           # > le=1.5
        {"log_tol_fib": 0.005},     # < ge=0.01
        {"pull_depth_tol": 0.0},    # < ge=0.01
        {"pivot_window": 0},        # < ge=1
        {"pivot_window": 6},        # > le=5
        {"symbol": ""},             # min_length=1
        {"symbol": "BAD SYM!"},     # fails charset pattern
        {"period": "3y"},           # outside the Literal
        {"timeframe": "hour"},      # outside the Literal
    ],
    ids=lambda o: "-".join(f"{k}={v}" for k, v in o.items()),
)
def test_pipeline_rejects_out_of_range_config(override):
    # Each row trips a Field bound / Literal / pattern → 422 at parse, no fetch.
    r = client.post("/api/v1/pipeline", json={**CFG, **override})
    assert r.status_code == 422


def test_education_known_family():
    r = client.get("/api/v1/scenario/education", params={"family": "5W_TREND"})
    assert r.status_code == 200
    body = r.json()
    assert body["family"] == "5W_TREND"
    assert isinstance(body["rules"], list)


def test_education_unknown_family_404():
    r = client.get("/api/v1/scenario/education", params={"family": "NOT_A_FAMILY"})
    assert r.status_code == 404


def test_education_invalid_family_422():
    # Malformed family (space / lowercase) is rejected at validation, before any lookup.
    r = client.get("/api/v1/scenario/education", params={"family": "bad family"})
    assert r.status_code == 422


def test_pipeline_502_redacts_fetch_error_detail(monkeypatch):
    # A fetch failure maps to a generic 502 that doesn't leak the exception text.
    def _boom(*a, **k):
        raise RuntimeError("/internal/path/secret.parquet missing")

    monkeypatch.setattr(pipeline_ops, "fetch_bars", _boom)
    r = client.post("/api/v1/pipeline", json=CFG)
    assert r.status_code == 502
    detail = r.json()["detail"]
    assert "secret.parquet" not in detail and "RuntimeError" not in detail


# ── /api/v1/analyst/stream SSE contract (seams mocked, no LLM) ──────────────────
STREAM_REQ = {**CFG, "scenario_id": "s1", "mode": "explanation", "rate_tps": 500.0}


def _parse_sse(text: str) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    for block in text.strip().split("\n\n"):
        if not block.strip():
            continue
        ev: dict[str, str] = {}
        for line in block.splitlines():
            if line.startswith("event:"):
                ev["event"] = line[len("event:") :].strip()
            elif line.startswith("data:"):
                ev["data"] = line[len("data:") :].strip()
        events.append(ev)
    return events


def _fake_output(*, narration="alpha beta gamma", cached=False, fell_back=False, citations=()):
    return SimpleNamespace(
        narration=narration,
        cached=cached,
        fell_back=fell_back,
        citations=citations,
        model_id="fake-model:1b",
        prompt_version="v9",
    )


@pytest.fixture
def _mock_stream_seams(monkeypatch):
    """Stub the fetch/pipeline/resolve/analyst seams the stream pre-flight calls."""
    monkeypatch.setattr(pipeline_ops, "fetch_bars_or_502", lambda req: (object(),))
    monkeypatch.setattr(pipeline_ops, "execute_pipeline", lambda req, bars: object())
    monkeypatch.setattr(
        pipeline_ops, "resolve_scenario", lambda result, sid: ([object()], object())
    )
    monkeypatch.setattr(analyst_service, "get_model_id", lambda: "fake-model:1b")


def test_analyst_stream_emits_events_in_order(_mock_stream_seams, monkeypatch):
    citations = (CitationRef(page=103, claim_sentence="A five-wave trend pushes."),)
    monkeypatch.setattr(
        analyst_service, "analyze",
        lambda *a, **k: _fake_output(narration="alpha beta gamma", citations=citations),
    )

    r = client.post("/api/v1/analyst/stream", json=STREAM_REQ)
    assert r.status_code == 200
    events = _parse_sse(r.text)
    names = [e["event"] for e in events]
    # Derive token count from the stream so a different chunker doesn't break the
    # start → token+ → citations → done ordering assertion.
    token_count = names.count("token")
    assert token_count >= 1, "expected at least one token event"
    assert names == ["start", *["token"] * token_count, "citations", "done"]

    start = json.loads(events[0]["data"])
    assert start == {"mode": "explanation", "model_id": "fake-model:1b", "scenario_id": "s1"}

    text = "".join(json.loads(e["data"])["text"] for e in events if e["event"] == "token")
    assert text == "alpha beta gamma "

    cit = json.loads(events[-2]["data"])
    assert cit["citations"] == [{"page": 103, "claim_sentence": "A five-wave trend pushes."}]
    assert cit["cached"] is False and cit["fell_back"] is False
    assert cit["model_id"] == "fake-model:1b" and cit["prompt_version"] == "v9"

    done = json.loads(events[-1]["data"])
    assert done["total_tokens"] == token_count
    # gen_ms is real wall-time (non-deterministic) — assert type, not value.
    assert isinstance(done["gen_ms"], (int, float))


def test_analyst_stream_empty_narration_emits_no_token(_mock_stream_seams, monkeypatch):
    # "".split(" ") == [""] would emit one ghost token with total_tokens=1.
    monkeypatch.setattr(
        analyst_service, "analyze", lambda *a, **k: _fake_output(narration="")
    )
    r = client.post("/api/v1/analyst/stream", json=STREAM_REQ)
    assert r.status_code == 200
    events = _parse_sse(r.text)
    assert [e["event"] for e in events] == ["start", "citations", "done"]
    assert json.loads(events[-1]["data"])["total_tokens"] == 0


def test_analyst_stream_marks_pre_resolved_cache_hit(_mock_stream_seams, monkeypatch):
    # cached/fell_back text skips the typewriter; the citations event still reports it.
    monkeypatch.setattr(
        analyst_service, "analyze",
        lambda *a, **k: _fake_output(narration="cached text", cached=True),
    )
    r = client.post("/api/v1/analyst/stream", json=STREAM_REQ)
    assert r.status_code == 200
    cit = next(e for e in _parse_sse(r.text) if e["event"] == "citations")
    assert json.loads(cit["data"])["cached"] is True


def test_analyst_stream_emits_error_event_on_analyze_failure(_mock_stream_seams, monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("model exploded")

    monkeypatch.setattr(analyst_service, "analyze", _boom)
    r = client.post("/api/v1/analyst/stream", json=STREAM_REQ)
    # Stream already began with HTTP 200; the failure surfaces as an `error` event.
    assert r.status_code == 200
    events = _parse_sse(r.text)
    err = next(e for e in events if e["event"] == "error")
    # Generic message — internal exception text must not leak to clients.
    assert json.loads(err["data"]) == {"message": "analyst narration failed"}
    assert "RuntimeError" not in err["data"] and "model exploded" not in err["data"]
    assert events[-1]["event"] == "error", "no done event after a mid-stream failure"


def test_analyst_stream_returns_500_when_model_init_fails(_mock_stream_seams, monkeypatch):
    def _boom():
        raise RuntimeError("ollama unreachable")

    monkeypatch.setattr(analyst_service, "get_model_id", _boom)
    r = client.post("/api/v1/analyst/stream", json=STREAM_REQ)
    assert r.status_code == 500
    assert "analyst init" in r.json()["detail"]


@pytest.mark.parametrize("rate_tps", [0.0, -1.0, 500.1, 1000.0], ids=["zero", "neg", "just_over", "way_over"])
def test_analyst_stream_rejects_invalid_rate_tps(rate_tps):
    # rate_tps gt=0, le=500: 422 at body parse before any seam (no mock needed).
    r = client.post("/api/v1/analyst/stream", json={**STREAM_REQ, "rate_tps": rate_tps})
    assert r.status_code == 422


@pytest.mark.slow
def test_pipeline_then_layer1_roundtrip(bars):  # bars fixture → skip if data unavailable
    res = client.post("/api/v1/pipeline", json=CFG)
    assert res.status_code == 200
    data = res.json()
    # Validate live wire bytes: serializer tests only cover the in-process
    # payload, so response_model re-serialization could still mangle it.
    PipelineResponse.model_validate(data)
    top = data["top_scenario"]
    assert {"id", "score", "score_components", "confidence_tier"} <= set(top)
    assert {
        "death_reason",
        "suggested_action",
        "first_divergence_index",
        "last_alive_segment_index",
    } <= set(data["report"]["diagnostic"])

    scenario_id = top["id"]
    ok = client.post("/api/v1/scenario/layer1", json={**CFG, "scenario_id": scenario_id})
    assert ok.status_code == 200
    body = ok.json()
    Layer1Response.model_validate(body)
    assert body["scenario_id"] == scenario_id
    assert {"bottleneck", "confirmation", "decision"} <= set(body)

    bad = client.post("/api/v1/scenario/layer1", json={**CFG, "scenario_id": "does-not-exist"})
    assert bad.status_code == 404


# ── /api/v1/qa single-shot contract (seams mocked, no embedder/LLM) ─────────────
QA_REQ = {**CFG, "question": "What is a five-wave trend?"}


def _qa_output(**over):
    base = dict(
        question="What is a five-wave trend?", answer="A five-wave trend (p.17).",
        citations=(CitationRef(page=17, claim_sentence="A five-wave trend."),),
        retrieved_pages=(17, 24), out_of_scope=False, fell_back=False,
        cached=False, model_id="fake:1b",
    )
    return SimpleNamespace(**{**base, **over})


def test_qa_503_when_embedder_absent(monkeypatch):
    monkeypatch.setattr(analyst_service, "qa_available", lambda: False)
    r = client.post("/api/v1/qa", json=QA_REQ)
    assert r.status_code == 503
    assert "ANALYST_QA" in r.json()["detail"]


def test_qa_empty_question_422():
    r = client.post("/api/v1/qa", json={**CFG, "question": ""})
    assert r.status_code == 422


def test_qa_theory_only_no_pipeline(monkeypatch):
    monkeypatch.setattr(analyst_service, "qa_available", lambda: True)
    # No scenario_id → must NOT touch the pipeline seams.
    monkeypatch.setattr(pipeline_ops, "fetch_bars_or_502", _forbidden)
    captured = {}

    def _answer(question, **k):
        captured.update(question=question, scenario=k["scenario"])
        return _qa_output()

    monkeypatch.setattr(analyst_service, "answer_question", _answer)
    r = client.post("/api/v1/qa", json=QA_REQ)
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] == "A five-wave trend (p.17)."
    assert body["citations"] == [{"page": 17, "claim_sentence": "A five-wave trend."}]
    assert body["retrieved_pages"] == [17, 24]
    assert captured["scenario"] is None  # theory-only


def test_qa_out_of_scope_passthrough(monkeypatch):
    monkeypatch.setattr(analyst_service, "qa_available", lambda: True)
    monkeypatch.setattr(
        analyst_service, "answer_question",
        lambda *a, **k: _qa_output(answer="Outside scope.", out_of_scope=True,
                                   citations=(), retrieved_pages=()),
    )
    r = client.post("/api/v1/qa", json=QA_REQ)
    assert r.status_code == 200
    assert r.json()["out_of_scope"] is True


def test_qa_scenario_aware_rebuilds_chart(monkeypatch):
    monkeypatch.setattr(analyst_service, "qa_available", lambda: True)
    monkeypatch.setattr(pipeline_ops, "fetch_bars_or_502", lambda req: (object(),))
    monkeypatch.setattr(pipeline_ops, "execute_pipeline", lambda req, bars: object())
    sentinel = object()
    monkeypatch.setattr(
        pipeline_ops, "resolve_scenario", lambda result, sid: ([sentinel], sentinel)
    )
    captured = {}

    def _answer(question, **k):
        captured.update(scenario=k["scenario"], bars=k["bars"])
        return _qa_output()

    monkeypatch.setattr(analyst_service, "answer_question", _answer)
    r = client.post("/api/v1/qa", json={**QA_REQ, "scenario_id": "s1"})
    assert r.status_code == 200
    assert captured["scenario"] is sentinel
    assert captured["bars"] is not None


def test_qa_500_on_unexpected_error(monkeypatch):
    # A non-HTTPException from the service maps to 500 with a generic, redacted detail.
    monkeypatch.setattr(analyst_service, "qa_available", lambda: True)
    monkeypatch.setattr(analyst_service, "answer_question", _boom_runtime)
    r = client.post("/api/v1/qa", json=QA_REQ)
    assert r.status_code == 500
    detail = r.json()["detail"]
    assert "RuntimeError" not in detail and "kaboom" not in detail


def test_qa_502_passthrough_from_fetch(monkeypatch):
    # A 502 raised by the fetch seam must re-raise as 502, not get swallowed to 500.
    from fastapi import HTTPException

    monkeypatch.setattr(analyst_service, "qa_available", lambda: True)
    monkeypatch.setattr(
        pipeline_ops, "fetch_bars_or_502",
        lambda req: (_ for _ in ()).throw(
            HTTPException(status_code=502, detail="fetch_bars: upstream down")
        ),
    )
    monkeypatch.setattr(analyst_service, "answer_question", _forbidden)
    r = client.post("/api/v1/qa", json={**QA_REQ, "scenario_id": "s1"})
    assert r.status_code == 502
    assert "fetch_bars" in r.json()["detail"]


def _boom_runtime(*a, **k):
    raise RuntimeError("kaboom")


def _forbidden(*a, **k):
    raise AssertionError("pipeline seam must not run for theory-only Q&A")
